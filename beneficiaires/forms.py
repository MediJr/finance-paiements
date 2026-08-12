"""Formulaires web — bénéficiaires (validation de saisie uniquement)."""

from django import forms

from accounts.models import Utilisateur
from beneficiaires.models import Beneficiaire


class BeneficiaireCreateForm(forms.Form):
    utilisateur_beneficiaire = forms.ModelChoiceField(
        queryset=Utilisateur.objects.none(),
        label='Bénéficiaire',
    )
    alias = forms.CharField(
        max_length=150,
        required=False,
        label='Alias',
    )

    def __init__(self, *args, proprietaire: Utilisateur, **kwargs):
        super().__init__(*args, **kwargs)
        exclus = Beneficiaire.objects.filter(
            proprietaire=proprietaire,
        ).values_list('utilisateur_beneficiaire_id', flat=True)
        self.fields['utilisateur_beneficiaire'].queryset = (
            Utilisateur.objects.filter(est_actif=True)
            .exclude(pk=proprietaire.pk)
            .exclude(pk__in=exclus)
            .order_by('nom', 'prenom')
        )


class BeneficiaireUpdateForm(forms.Form):
    alias = forms.CharField(
        max_length=150,
        required=False,
        label='Alias',
    )
    statut = forms.ChoiceField(
        choices=Beneficiaire.Statut.choices,
        label='Statut',
    )
