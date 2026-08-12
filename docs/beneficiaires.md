# Bénéficiaires — Sprint 3

## Objectif

Permettre à chaque utilisateur de gérer sa liste de destinataires autorisés.

Aucune opération financière n'est exécutée.

## Modèle `Beneficiaire`

| Champ | Description |
|-------|-------------|
| proprietaire | Utilisateur propriétaire de la liste |
| utilisateur_beneficiaire | Utilisateur destinataire |
| alias | Nom personnalisé (optionnel) |
| statut | `actif` / `inactif` |
| dates | création / mise à jour |

Contrainte d'unicité : `(proprietaire, utilisateur_beneficiaire)`.

## Règles métier

- un propriétaire peut avoir plusieurs bénéficiaires ;
- pas d'auto-ajout ;
- pas de doublon ;
- désactivation logique (DELETE API → statut `inactif`) ;
- seuls les bénéficiaires actifs sont sélectionnables (`list_beneficiaires_selectionnables`).

## Service

`beneficiaires.services.beneficiaire_service`

- `create_beneficiaire`
- `list_beneficiaires` / `list_beneficiaires_selectionnables`
- `get_beneficiaire_pour_proprietaire` (contrôle d'appartenance)
- `update_beneficiaire`
- `desactiver_beneficiaire` / `reactiver_beneficiaire`

## Interfaces

### Web

- `/beneficiaires/` — liste
- `/beneficiaires/nouveau/` — création
- `/beneficiaires/<id>/` — détail
- `/beneficiaires/<id>/modifier/` — modification

### API (authentifiée, scoped au propriétaire)

- `GET /api/beneficiaires/`
- `POST /api/beneficiaires/`
- `GET /api/beneficiaires/<id>/`
- `PUT|PATCH /api/beneficiaires/<id>/`
- `DELETE /api/beneficiaires/<id>/` — désactivation logique
