"""
Crée les comptes de démonstration (développement uniquement).

    python backend/manage.py creer_comptes_demo

- alice (cliente) : 1 500 EUR, Bob en bénéficiaire
- bob (client)    : 300 EUR, Alice en bénéficiaire
- admin (personnel) : accès à l'administration
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Utilisateur
from accounts.services import create_utilisateur
from beneficiaires.services import ajouter_beneficiaire_par_email
from wallets.services import alimenter_wallet
from wallets.services.passerelle_carte import CARTE_TEST_ACCEPTEE

CLIENTS = (
    # username, mot de passe, prénom, nom, e-mail, solde initial
    ('alice', 'Alice-Demo-2026', 'Alice', 'Martin', 'alice@demo.local', '1500.00'),
    ('bob', 'Bob-Demo-2026', 'Bob', 'Dupont', 'bob@demo.local', '300.00'),
)
ADMIN = ('admin', 'Admin-Demo-2026')


class Command(BaseCommand):
    help = 'Crée deux clients approvisionnés et un administrateur de démonstration.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Comptes de démonstration interdits hors mode DEBUG.')
        User = get_user_model()

        crees = []
        for username, mot_de_passe, prenom, nom, email, solde in CLIENTS:
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'{username} existe déjà.')
                continue
            client = create_utilisateur(
                username=username,
                password=mot_de_passe,
                prenom=prenom,
                nom=nom,
                email=email,
            )
            alimenter_wallet(utilisateur=client, montant=solde, numero_carte=CARTE_TEST_ACCEPTEE)
            crees.append(client)
            self.stdout.write(self.style.SUCCESS(f'{username} / {mot_de_passe} ({solde} EUR)'))

        if len(crees) == len(CLIENTS):
            alice, bob = crees
            ajouter_beneficiaire_par_email(proprietaire=alice, email=bob.email, alias='Bob')
            ajouter_beneficiaire_par_email(proprietaire=bob, email=alice.email, alias='Alice')

        username, mot_de_passe = ADMIN
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(
                username=username,
                password=mot_de_passe,
                email='admin@demo.local',
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(self.style.SUCCESS(f'{username} / {mot_de_passe} (administrateur)'))
        self.stdout.write(f'{Utilisateur.objects.count()} client(s) au total.')
