# Architecture — Finance (11-finance)

**Dernière mise à jour** : Prototype 4 — Sprint 10 (Exports — clôture)

## Modules

```text
accounts / wallets / historique / beneficiaires
virements / paiements
administration   → paramètres + sécurité + pilotage + exports
observabilite    → journal d'événements
api              → REST métier (scoped) + /api/administration/
```

## Flux principal

```text
Client
  → vues (web / API) — auth + scope / admin
       → services métier — règles + plafonds + maintenance
            → mouvement_service — seuls débits/crédits
                 → PostgreSQL
       → journal_service (observabilité)
       → export_service (CSV / JSON admin)
```

## Prototypes

| Prototype | Thème | Sprints |
|-----------|-------|---------|
| 1 | Fondation | 0–2 |
| 2 | Opérations financières | 3–5 |
| 3 | Admin + sécurité + pilotage | 6–8 |
| 4 | Observabilité + exports | 9–10 |
