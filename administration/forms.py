"""Formulaires web — administration."""

from django import forms

from administration.models import ParametresApplication


class ParametresForm(forms.ModelForm):
    class Meta:
        model = ParametresApplication
        fields = [
            'nom_application',
            'devise_par_defaut',
            'mode_maintenance',
            'montant_virement_max',
            'montant_paiement_max',
            'delai_session_minutes',
        ]
