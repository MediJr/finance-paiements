# Historique des opérations — Sprint 2

## Objectif

Enregistrer et consulter les événements financiers associés à un Wallet.

Aucune opération financière réelle n'est exécutée au Sprint 2.
Aucun solde n'est modifié.

## Modèle `HistoriqueOperation`

| Champ | Description |
|-------|-------------|
| wallet | Wallet concerné (obligatoire) |
| type_operation | Type générique (crédit, débit, virement, paiement, remboursement, autre) |
| statut | État de l'événement |
| description | Texte libre |
| montant | Optionnel |
| devise | Par défaut celle du Wallet |
| reference | Identifiant métier unique |
| dates | création / mise à jour |

## Service

`historique.services.historique_service`

- `create_historique_operation` — enregistrement centralisé (sans effet sur le solde)
- `list_historique_operations` — consultation / filtres
- `get_historique_operation` — détail

Filtres : `wallet`, `type`, `statut`, `date_debut`, `date_fin`, `reference`.

## Interfaces

### Web

- `/historique/` — liste filtrable
- `/historique/<id>/` — détail

### API (authentifiée, lecture seule)

- `GET /api/historique/`
- `GET /api/historique/<id>/`
- `GET /api/wallets/<id>/historique/`

Aucune création via l'API.

## Sécurité (Sprint 7)

Un utilisateur non administrateur ne consulte que l'historique de **ses** Wallets.
Les administrateurs (`is_staff`) conservent une vision globale.
