# Pilotage — Tableau de bord, statistiques et rapports (Sprint 8)

Outils de pilotage réservés aux administrateurs (`is_staff`).

Pas de Data Analytics avancée, pas d'IA, pas de prédiction.

## Tableau de bord

Compteurs globaux :

- utilisateurs (total / actifs)
- wallets (total / actifs)
- bénéficiaires (total / actifs)
- virements, paiements, remboursements
- opérations d'historique

Service : `administration.services.dashboard_service.get_dashboard`

| Interface | URL |
|-----------|-----|
| Web | `/administration/dashboard/` |
| API | `GET /api/administration/dashboard/` |

## Statistiques

Indicateurs métier filtrables :

- nombre et montants cumulés (virements / paiements / remboursements)
- répartition par statut
- activité par jour
- soldes wallets

Filtres : `date_debut`, `date_fin`, `statut`, `utilisateur` (id métier).

Service : `administration.services.statistiques_service.get_statistiques`

| Interface | URL |
|-----------|-----|
| Web | `/administration/statistiques/` |
| API | `GET /api/administration/statistiques/` |

## Rapports

Rapports consultables en lecture seule :

- `virements`
- `paiements`
- `remboursements`
- `wallets`
- `utilisateurs`

Service : `administration.services.rapport_service.generer_rapport`

| Interface | URL |
|-----------|-----|
| Web | `/administration/rapports/?type=…` |
| API | `GET /api/administration/rapports/?type=…` |

## Sécurité

- Accès exclusivement administrateur (décorateur web + `IsAdministrateur` API)
- Les utilisateurs standards sont refusés (redirection / 403)
- Aucune modification de données via ces écrans
