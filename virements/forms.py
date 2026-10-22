"""Formulaires web — virements (saisie uniquement)."""

from decimal import Decimal

from django import forms

from accounts.models import Utilisateur
from beneficiaires.services import list_beneficiaires_selectionnables
from commun.formulaires import CleIdempotenceMixin


class VirementCreateForm(CleIdempotenceMixin, forms.Form):
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
    motif = forms.CharField(
        max_length=255,
        required=False,
        label='Motif',
    )

    def __init__(self, *args, emetteur: Utilisateur, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['beneficiaire'].queryset = list_beneficiaires_selectionnables(
            proprietaire=emetteur
        )
        self.fields['beneficiaire'].label_from_instance = (
            lambda b: b.alias
            or f'{b.utilisateur_beneficiaire.prenom} {b.utilisateur_beneficiaire.nom}'
        )
