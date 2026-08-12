# Observabilité — Journal d'événements (Prototype 4 — Sprint 9)

Couche d'observabilité pour tracer les événements métier et techniques.

Ce n'est **pas** un SIEM, ni une plateforme Analytics.

## Architecture

```text
Services métier / middleware
        │
        ▼
observabilite.services.journal_service   ← unique point d'écriture
        │
        ▼
Evenement (PostgreSQL)
        │
        ├── Web admin  /administration/evenements/
        └── API admin  /api/administration/evenements/
```

Règles :

- écriture exclusive via `enregistrer_evenement` / `enregistrer_evenement_durable`
- événements immuables (pas de modification / suppression)
- consultation réservée aux administrateurs (`is_staff`)

## Modèle `Evenement`

| Champ | Description |
|-------|-------------|
| id | Identifiant |
| date_creation | Horodatage |
| type_evenement | Type métier / technique |
| niveau | `INFO`, `WARNING`, `ERROR`, `SECURITY` |
| module | Module source (`accounts`, `virements`, …) |
| utilisateur | User Django (nullable) |
| description | Texte |
| contexte | JSON |
| adresse_ip | IP optionnelle |
| user_agent | User-Agent optionnel |

Migration : `observabilite.0001_evenement`.

## Événements journalisés

| Domaine | Types |
|---------|-------|
| Utilisateurs | création, activation, désactivation |
| Wallet | création |
| Bénéficiaires | création, modification, désactivation |
| Virements | création, réussite, échec |
| Paiements | création, réussite, échec |
| Remboursements | création, réussite, échec |
| Administration | modification paramètres, accès admin |
| Technique | `http_500`, `erreur_application` |

## API (lecture seule)

- `GET /api/administration/evenements/`
- `GET /api/administration/evenements/<id>/`

Filtres : `niveau`, `module`, `type`, `utilisateur`, `date_debut`, `date_fin`, `q`.

## Interface web

- `/administration/evenements/` — liste + recherche / filtres
- `/administration/evenements/<id>/` — détail

Django Admin : consultation seule (pas d'ajout / modification / suppression).
