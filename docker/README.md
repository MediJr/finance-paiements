# Docker

| Fichier | Usage |
|---------|-------|
| `Dockerfile` | Image Python 3.12, utilisateur non-root, Gunicorn par défaut |
| `docker-compose.yml` | Développement : PostgreSQL + `runserver` avec rechargement du code |
| `docker-compose.prod.yml` | Production : PostgreSQL + Gunicorn + WhiteNoise |

## Développement

```bash
copy .env.example .env      # à la racine du projet (cp sous Linux / macOS)
cd docker
docker compose up --build
```

| Service | Port hôte |
|---------|-----------|
| `web` (Django) | 8001 |
| `db` (PostgreSQL 16) | 5433 |

## Production

Voir [docs/installation.md](../docs/installation.md#option-3--production-docker-gunicorn).
