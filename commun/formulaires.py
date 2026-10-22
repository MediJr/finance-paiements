"""Briques de formulaires partagées."""

import uuid

from django import forms


class CleIdempotenceMixin(forms.Form):
    """
    Ajoute une clé d'idempotence cachée, générée à l'affichage du formulaire.

    Le même formulaire soumis deux fois (double clic, rechargement) porte la
    même clé : le service n'exécute l'opération qu'une seule fois.
    """

    cle_idempotence = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault('cle_idempotence', uuid.uuid4().hex)
