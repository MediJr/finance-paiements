"""
Utilitaires HTTP partagés : adresse IP client et redirections sûres.

Centralise des règles de sécurité auparavant dupliquées dans chaque module.
"""

from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def adresse_ip_client(request) -> str | None:
    """
    Retourne l'adresse IP du client.

    L'en-tête X-Forwarded-For est fourni par le client et donc falsifiable :
    il n'est pris en compte que si l'application est explicitement déployée
    derrière un reverse proxy de confiance (TRUST_X_FORWARDED_FOR=True).
    """
    if request is None:
        return None
    if getattr(settings, 'TRUST_X_FORWARDED_FOR', False):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def redirection_sure(request, url: str | None, defaut: str):
    """
    Redirige vers `url` uniquement si elle pointe vers ce site.

    Protège contre les redirections ouvertes (`?next=https://site-malveillant`).
    """
    if url and url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(url)
    return redirect(defaut)
