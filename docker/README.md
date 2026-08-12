# Docker

Orchestration locale de l'application Finance.

## Services

| Service | Conteneur | Port hôte |
|---------|-----------|-----------|
| PostgreSQL 16 | `finance-db` | `5433` |
| Django | `finance-web` | `8001` |

Les ports `5433` et `8001` évitent les conflits avec d'autres applications du laboratoire.

## Démarrage

```bash
# Depuis applications/11-finance/
copy .env.example .env   # une seule fois

cd docker
docker compose up -d db
docker compose up -d web
```

## Vérifications

```bash
docker compose config
docker compose ps
docker compose exec db pg_isready -U finance -d finance
```
