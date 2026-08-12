# Utilisateurs et Wallets — Sprint 1

## Utilisateur métier

Modèle `accounts.Utilisateur`, lié en OneToOne à `django.contrib.auth.User`.

| Champ | Description |
|-------|-------------|
| prenom, nom | Identité |
| email, telephone | Contact |
| est_actif | État du compte |
| date_creation, date_mise_a_jour | Dates techniques |

Création recommandée via `accounts.services.create_utilisateur`.

## Wallet

Modèle `wallets.Wallet`, relation OneToOne avec `Utilisateur`.

| Champ | Description |
|-------|-------------|
| utilisateur | Propriétaire (obligatoire, unique) |
| solde | Décimal ≥ 0, initialement `0.00` |
| devise | Par défaut `EUR` |
| statut | `actif` / `inactif` |
| dates | création / mise à jour |

## Création automatique

À la création d'un `Utilisateur` :

1. signal `post_save` → `wallet_service.create_wallet_for_utilisateur`
2. le service est idempotent (`get_or_create`)

Aucune opération financière n'est disponible au Sprint 1.

## Interfaces

### Web

- `/utilisateurs/` — liste
- `/utilisateurs/<id>/` — détail + aperçu Wallet
- `/wallets/<id>/` — consultation Wallet

### API (authentifiée)

- `GET /api/utilisateurs/`
- `GET /api/utilisateurs/<id>/`
- `GET /api/utilisateurs/<id>/wallet/`
- `GET /api/wallets/<id>/`

## Sécurité (Sprint 7)

Un utilisateur non administrateur ne consulte que **son** profil et **son** Wallet.
Les administrateurs (`is_staff`) conservent une vision globale.
