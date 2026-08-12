"""
Service métier — tableau de bord administrateur (Sprint 8).

Indicateurs de synthèse uniquement. Pas d'analytique avancée.
"""

from __future__ import annotations

from accounts.models import Utilisateur
from administration.permissions import require_administrateur
from beneficiaires.models import Beneficiaire
from historique.models import HistoriqueOperation
from paiements.models import Paiement, Remboursement
from virements.models import Virement
from wallets.models import Wallet


def get_dashboard(*, administrateur) -> dict:
    """
    Retourne les compteurs globaux du tableau de bord.

    Réservé aux administrateurs.
    """
    require_administrateur(administrateur)

    return {
        'utilisateurs': Utilisateur.objects.count(),
        'utilisateurs_actifs': Utilisateur.objects.filter(est_actif=True).count(),
        'wallets': Wallet.objects.count(),
        'wallets_actifs': Wallet.objects.filter(statut=Wallet.Statut.ACTIF).count(),
        'beneficiaires': Beneficiaire.objects.count(),
        'beneficiaires_actifs': Beneficiaire.objects.filter(
            statut=Beneficiaire.Statut.ACTIF
        ).count(),
        'virements': Virement.objects.count(),
        'paiements': Paiement.objects.count(),
        'remboursements': Remboursement.objects.count(),
        'operations': HistoriqueOperation.objects.count(),
    }
