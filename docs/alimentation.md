# Alimentation du portefeuille

Seul point d'entrée de fonds sur la plateforme (sprint 11). Sans lui, les
portefeuilles, créés à 0 EUR, ne pourraient jamais être utilisés.

## Modèle `Alimentation`

| Champ | Rôle |
|-------|------|
| `reference` | Référence unique `DEP-…` |
| `wallet` | Portefeuille crédité |
| `montant`, `devise` | Montant demandé |
| `statut` | `acceptee` / `refusee` |
| `carte_masquee` | `•••• 4242` — le numéro complet n'est jamais conservé |
| `motif_refus` | Raison renvoyée par la passerelle |
| `cle_idempotence` | Unique par portefeuille : un double envoi ne crédite qu'une fois |

## Passerelle simulée (`wallets/services/passerelle_carte.py`)

La décision est prise **côté serveur** par `autoriser_carte(numero)` :

1. le numéro doit compter 13 à 19 chiffres avec une clé de **Luhn** valide ;
   sinon : erreur `400`, rien n'est enregistré ;
2. toute carte valide est acceptée, sauf celles qui se terminent par `0002`
   (refus « fonds insuffisants »), sur le modèle des cartes de test des
   prestataires réels.

| Carte de test | Résultat |
|---------------|----------|
| `4242 4242 4242 4242` | Acceptée |
| `4000 0000 0000 0002` | Refusée |

## Règles

- portefeuille verrouillé pendant l'opération ;
- montant à 2 décimales maximum, plafonné par le paramètre
  `montant_alimentation_max` (5 000 EUR par défaut) ;
- refusé en mode maintenance ou si le portefeuille est inactif ;
- chaque tentative (acceptée ou refusée) produit une ligne d'historique
  `CREDIT` (`réussie` / `échouée`) et un événement d'observabilité.

## Interfaces

- Web : `/wallets/alimenter/`
- API : `POST /api/alimentations/` `{ "montant": "100.00", "numero_carte": "4242…" }`
  → `201` acceptée, `402` refusée, `200` si l'en-tête `Idempotency-Key` rejoue une
  alimentation existante, `400` si la carte ou le montant est invalide.
- API : `GET /api/alimentations/` — alimentations du client connecté.
