"""Formulaires web — bénéficiaires (validation de saisie uniquement)."""

from django import forms

from beneficiaires.models import Beneficiaire


class BeneficiaireCreateForm(forms.Form):
    """
    Le destinataire est désigné par son e-mail exact : aucune liste de
    clients n'est proposée (pas d'énumération de l'annuaire).
    """

    email = forms.EmailField(
        label='E-mail du bénéficiaire',
        help_text='Adresse utilisée par votre destinataire pour son compte.',
    )
    alias = forms.CharField(
        max_length=150,
        required=False,
        label='Alias',
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
