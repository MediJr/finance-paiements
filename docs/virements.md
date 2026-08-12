# Virements — Sprint 4

## Objectif

Permettre un virement sécurisé et atomique entre le Wallet d'un utilisateur et celui d'un bénéficiaire actif.

## Modèle `Virement`

| Champ | Description |
|-------|-------------|
| reference | Identifiant métier unique |
| wallet_emetteur | Wallet source |
| wallet_beneficiaire | Wallet destination |
| montant | Strictement positif |
| devise | Devise du transfert |
| statut | `reussi` / `echoue` |
| motif | Optionnel |
| dates | création / mise à jour |

## Service

`virements.services.virement_service.executer_virement`

Exécuté dans une transaction Django unique :

1. validations métier ;
2. verrouillage des Wallets (`select_for_update`) ;
3. débit / crédit des soldes ;
4. création du `Virement` ;
5. écriture automatique de l'historique (débit + crédit).

Toute modification de solde passe exclusivement par ce service.

## Validations

- Wallet émetteur et bénéficiaire actifs
- bénéficiaire actif appartenant au propriétaire
- montant > 0
- devises compatibles
- solde suffisant
- pas d'auto-virement
- **plafond** `montant_virement_max` (Sprint 7)
- **mode maintenance** : opération refusée (Sprint 7)

## Interfaces

### Web

- `/virements/` — liste
- `/virements/nouveau/` — exécution
- `/virements/<id>/` — détail

### API

- `POST /api/virements/` — `{ beneficiaire_id, montant, motif? }`
- `GET /api/virements/`
- `GET /api/virements/<id>/`
