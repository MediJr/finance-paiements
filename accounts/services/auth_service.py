"""
Services métier — inscription, authentification et sessions des clients.

Le site /admin/ de Django reste réservé au personnel : les clients disposent
de leur propre espace (/comptes/), protégé contre la force brute.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError

from accounts.models import Utilisateur
from accounts.services.utilisateur_service import create_utilisateur
from commun.http import adresse_ip_client
from observabilite.models import Evenement
from observabilite.services.journal_service import (
    TYPE_AUTH_BLOCAGE,
    TYPE_AUTH_CONNEXION,
    TYPE_AUTH_DECONNEXION,
    TYPE_AUTH_ECHEC,
    TYPE_AUTH_INSCRIPTION,
    enregistrer_evenement,
)

User = get_user_model()

# Le seuil par IP est plus large : plusieurs utilisateurs peuvent partager une IP.
FACTEUR_SEUIL_IP = 4

MESSAGE_ECHEC = 'Identifiant ou mot de passe incorrect.'
MESSAGE_BLOCAGE = (
    'Trop de tentatives de connexion échouées. '
    'Réessayez dans {minutes} minutes.'
)


def inscrire_client(
    *,
    username: str,
    password: str,
    password_confirm: str,
    prenom: str,
    nom: str,
    email: str,
    telephone: str = '',
    request=None,
) -> Utilisateur:
    """Crée un compte client (utilisateur, profil métier et Wallet à 0)."""
    username = (username or '').strip()
    email = (email or '').strip().lower()
    erreurs: dict[str, list[str]] = {}
    if not username:
        erreurs.setdefault('username', []).append('Identifiant obligatoire.')
    elif User.objects.filter(username__iexact=username).exists():
        erreurs.setdefault('username', []).append('Cet identifiant est déjà utilisé.')
    if not email:
        erreurs.setdefault('email', []).append('E-mail obligatoire.')
    elif Utilisateur.objects.filter(email__iexact=email).exists():
        erreurs.setdefault('email', []).append('Un compte existe déjà avec cet e-mail.')
    if not (prenom or '').strip() or not (nom or '').strip():
        erreurs.setdefault('nom', []).append('Prénom et nom obligatoires.')
    if password != password_confirm:
        erreurs.setdefault('password_confirm', []).append(
            'Les mots de passe ne correspondent pas.'
        )
    else:
        try:
            validate_password(password, User(username=username, email=email))
        except ValidationError as exc:
            erreurs.setdefault('password', []).extend(exc.messages)
    if erreurs:
        raise ValidationError(erreurs)

    utilisateur = create_utilisateur(
        username=username,
        password=password,
        prenom=prenom.strip(),
        nom=nom.strip(),
        email=email,
        telephone=(telephone or '').strip(),
    )
    enregistrer_evenement(
        type_evenement=TYPE_AUTH_INSCRIPTION,
        module='accounts',
        description=f'Inscription de {username}',
        utilisateur=utilisateur.user,
        adresse_ip=adresse_ip_client(request),
    )
    return utilisateur


def _cles_tentatives(username: str, adresse_ip: str | None) -> list[str]:
    cles = [f'connexion:echecs:compte:{username.lower()}']
    if adresse_ip:
        cles.append(f'connexion:echecs:ip:{adresse_ip}')
    return cles


def connexion_bloquee(username: str, adresse_ip: str | None) -> bool:
    """Vrai si le compte ou l'IP a dépassé le nombre d'échecs autorisés."""
    seuil = settings.CONNEXION_MAX_ECHECS
    cle_compte, *cle_ip = _cles_tentatives(username, adresse_ip)
    if cache.get(cle_compte, 0) >= seuil:
        return True
    return bool(cle_ip) and cache.get(cle_ip[0], 0) >= seuil * FACTEUR_SEUIL_IP


def _enregistrer_echec(username: str, adresse_ip: str | None) -> None:
    duree = settings.CONNEXION_DUREE_BLOCAGE_MINUTES * 60
    for cle in _cles_tentatives(username, adresse_ip):
        cache.add(cle, 0, timeout=duree)
        try:
            cache.incr(cle)
        except ValueError:
            cache.set(cle, 1, timeout=duree)


def authentifier_client(request, *, username: str, password: str):
    """
    Authentifie un utilisateur et ouvre une session.

    Retourne (user, None) en cas de succès, (None, message) sinon. Le message
    d'échec est identique que l'identifiant existe ou non.
    """
    username = (username or '').strip()
    adresse_ip = adresse_ip_client(request)
    if not username or not password:
        return None, 'Identifiant et mot de passe requis.'

    if connexion_bloquee(username, adresse_ip):
        enregistrer_evenement(
            type_evenement=TYPE_AUTH_BLOCAGE,
            module='accounts',
            description=f'Connexion bloquée pour {username} (trop de tentatives)',
            niveau=Evenement.Niveau.WARNING,
            contexte={'username': username},
            adresse_ip=adresse_ip,
        )
        return None, MESSAGE_BLOCAGE.format(minutes=settings.CONNEXION_DUREE_BLOCAGE_MINUTES)

    user = authenticate(request, username=username, password=password)
    if user is None:
        _enregistrer_echec(username, adresse_ip)
        enregistrer_evenement(
            type_evenement=TYPE_AUTH_ECHEC,
            module='accounts',
            description=f'Échec de connexion pour {username}',
            niveau=Evenement.Niveau.WARNING,
            contexte={'username': username},
            adresse_ip=adresse_ip,
        )
        return None, MESSAGE_ECHEC

    cache.delete(f'connexion:echecs:compte:{username.lower()}')
    login(request, user)
    enregistrer_evenement(
        type_evenement=TYPE_AUTH_CONNEXION,
        module='accounts',
        description=f'Connexion de {user.username}',
        utilisateur=user,
        adresse_ip=adresse_ip,
    )
    return user, None


def deconnecter(request) -> None:
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        enregistrer_evenement(
            type_evenement=TYPE_AUTH_DECONNEXION,
            module='accounts',
            description=f'Déconnexion de {user.username}',
            utilisateur=user,
            adresse_ip=adresse_ip_client(request),
        )
    logout(request)
