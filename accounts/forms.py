"""Formulaires web — inscription et connexion (validation de saisie uniquement)."""

from django import forms


class InscriptionForm(forms.Form):
    prenom = forms.CharField(max_length=150, label='Prénom')
    nom = forms.CharField(max_length=150, label='Nom')
    email = forms.EmailField(label='E-mail')
    telephone = forms.CharField(max_length=30, required=False, label='Téléphone')
    username = forms.CharField(max_length=150, label='Identifiant')
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirmation du mot de passe',
    )


class ConnexionForm(forms.Form):
    username = forms.CharField(max_length=150, label='Identifiant')
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')
