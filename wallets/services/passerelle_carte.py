"""
Passerelle de paiement par carte simulée (côté serveur).

Remplace un prestataire réel (Stripe, Adyen…) pour l'alimentation des Wallets.
La décision d'accepter ou de refuser est prise ici, à partir du numéro de carte
validé (clé de Luhn) — jamais à partir d'une donnée « résultat » du client.

Convention de test (inspirée des prestataires réels) : toute carte valide est
acceptée, sauf celles qui se terminent par `0002` (refus « fonds insuffisants »).
Aucun numéro complet n'est conservé : seul un libellé masqué est renvoyé.
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError

SUFFIXE_REFUS = '0002'

# Cartes de démonstration documentées (README, docs/alimentation.md).
CARTE_TEST_ACCEPTEE = '4242424242424242'
CARTE_TEST_REFUSEE = '4000000000000002'


@dataclass(frozen=True)
class ResultatAutorisation:
    accepte: bool
    carte_masquee: str
    motif_refus: str = ''


def _luhn_valide(numero: str) -> bool:
    total = 0
    for index, chiffre in enumerate(reversed(numero)):
        n = int(chiffre)
        if index % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def autoriser_carte(numero_carte) -> ResultatAutorisation:
    """
    Demande d'autorisation à la passerelle simulée.

    Lève ValidationError si le numéro est mal formé (aucune alimentation créée).
    """
    numero = ''.join(str(numero_carte or '').split()).replace('-', '')
    if not (numero.isdigit() and 13 <= len(numero) <= 19 and _luhn_valide(numero)):
        raise ValidationError('Numéro de carte invalide.')
    masque = f'•••• {numero[-4:]}'
    if numero.endswith(SUFFIXE_REFUS):
        return ResultatAutorisation(
            accepte=False,
            carte_masquee=masque,
            motif_refus='Refus de la banque (fonds insuffisants — carte de test).',
        )
    return ResultatAutorisation(accepte=True, carte_masquee=masque)
