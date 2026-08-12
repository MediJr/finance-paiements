# Administration et paramètres

## Objectif

Module d'administration fonctionnelle pour superviser, configurer, piloter et exporter.

Aucune opération financière n'est modifiée depuis l'administration.

## Accès

Réservé aux utilisateurs Django `is_staff`.

## Paramètres (`ParametresApplication`)

Singleton (pk=1) — appliqués réellement depuis le Sprint 7 :

| Paramètre | Effet |
|-----------|-------|
| `mode_maintenance` | Bloque virements / paiements / remboursements |
| `montant_virement_max` | Plafond service virement |
| `montant_paiement_max` | Plafond service paiement |
| `delai_session_minutes` | Durée de session (middleware) |
| `devise_par_defaut` | Devise à la création de Wallet |

Voir aussi [security-by-design.md](security-by-design.md), [pilotage.md](pilotage.md), [exports.md](exports.md).

## Écrans web

| URL | Contenu |
|-----|---------|
| `/administration/` | Accueil admin |
| `/administration/dashboard/` | Tableau de bord |
| `/administration/statistiques/` | Statistiques |
| `/administration/rapports/` | Rapports |
| `/administration/exports/` | Exports CSV / JSON |
| `/administration/parametres/` | Paramètres |
| `/administration/utilisateurs/` | Consultation + activation/désactivation |
| `/administration/wallets/` | Consultation Wallets |
| `/administration/operations/` | Opérations |
| `/administration/journal/` | Journal d'administration |
| `/administration/evenements/` | Journal d'événements |

## API

Préfixe `/api/administration/` — permission `IsAdministrateur` :

- `GET|PUT|PATCH /parametres/`
- `GET /utilisateurs/`
- `GET /wallets/`
- `GET /operations/?type=…`
- `GET /dashboard/`
- `GET /statistiques/`
- `GET /rapports/?type=…`
- `GET /evenements/`
- `GET /evenements/<id>/`
- `GET /exports/?type=…&export_format=csv|json`
