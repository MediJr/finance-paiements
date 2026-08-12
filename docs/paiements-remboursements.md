# Paiements et remboursements — Sprint 5

## Objectif

Exécuter des paiements et des remboursements atomiques, sans dupliquer la logique des virements.

## Réutilisation

Les mouvements de fonds passent par `wallets.services.mouvement_service` :

- `parse_montant`
- `transferer_fonds`
- `journaliser_transfert`

Utilisé par `virement_service`, `paiement_service` et `remboursement_service`.

## Paiement

Service : `paiements.services.paiement_service.executer_paiement`

Validations : Wallets actifs, bénéficiaire actif autorisé, montant > 0, devises, solde,
plafond `montant_paiement_max`, refus en mode maintenance (Sprint 7).

Historique : type `paiement` (OUT/IN).

## Remboursement

Service : `paiements.services.remboursement_service.executer_remboursement`

- rattaché à un paiement existant
- émis uniquement par le bénéficiaire d'origine
- montant ≤ reste remboursable (défaut = reste total)
- refuse un paiement déjà totalement remboursé
- refus en mode maintenance (Sprint 7)

Historique : type `remboursement` (OUT/IN).

## Interfaces

### Web

- `/paiements/`, `/paiements/nouveau/`, `/paiements/<id>/`
- `/remboursements/`, `/remboursements/nouveau/`, `/remboursements/<id>/`

### API

- `POST/GET /api/paiements/`, `GET /api/paiements/<id>/`
- `POST/GET /api/remboursements/`, `GET /api/remboursements/<id>/`
