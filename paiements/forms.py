"""Formulaires web — paiements et remboursements."""

from decimal import Decimal

from django import forms

from accounts.models import Utilisateur
from beneficiaires.services import list_beneficiaires_selectionnables
from paiements.models import Paiement
from paiements.services import list_paiements


class PaiementCreateForm(forms.Form):
    beneficiaire = forms.ModelChoiceField(
        queryset=None,
        label='Bénéficiaire',
        empty_label='Sélectionner…',
    )
    montant = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=14,
        decimal_places=2,
        label='Montant',
    )
    motif = forms.CharField(max_length=255, required=False, label='Motif')

    def __init__(self, *args, payeur: Utilisateur, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['beneficiaire'].queryset = list_beneficiaires_selectionnables(
            proprietaire=payeur
        )
        self.fields['beneficiaire'].label_from_instance = (
            lambda b: b.alias
            or f'{b.utilisateur_beneficiaire.prenom} {b.utilisateur_beneficiaire.nom}'
        )


class RemboursementCreateForm(forms.Form):
    paiement = forms.ModelChoiceField(
        queryset=None,
        label='Paiement à rembourser',
        empty_label='Sélectionner…',
    )
    montant = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=14,
        decimal_places=2,
        required=False,
        label='Montant (vide = reste total)',
    )

    def __init__(self, *args, acteur: Utilisateur, **kwargs):
        super().__init__(*args, **kwargs)
        # Paiements reçus par l'acteur et encore remboursables.
        qs = list_paiements(utilisateur=acteur).filter(
            wallet_beneficiaire=acteur.wallet,
        ).exclude(statut=Paiement.Statut.REMBOURSE)
        self.fields['paiement'].queryset = qs
        self.fields['paiement'].label_from_instance = (
            lambda p: f'{p.reference} — reste {p.montant_restant} {p.devise}'
        )
