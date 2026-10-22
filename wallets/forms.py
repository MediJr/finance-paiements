"""Formulaires web — alimentation du Wallet (validation de saisie uniquement)."""

import uuid
from decimal import Decimal

from django import forms


class AlimentationForm(forms.Form):
    montant = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=14,
        decimal_places=2,
        label='Montant (EUR)',
    )
    numero_carte = forms.CharField(
        max_length=23,
        label='Numéro de carte',
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'inputmode': 'numeric'}),
        help_text='Le numéro n’est jamais conservé : seuls les 4 derniers chiffres sont enregistrés.',
    )
    # Une clé par affichage du formulaire : un double envoi ne crédite qu'une fois.
    cle_idempotence = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault('cle_idempotence', uuid.uuid4().hex)
