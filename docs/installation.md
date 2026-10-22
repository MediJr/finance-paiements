# Installation et déploiement

> Phase du cycle de vie : **Déploiement**.

## Option 1 — Démarrage rapide (SQLite, sans Docker)

Prérequis : Python 3.12+.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux / macOS
pip install -r requirements-dev.txt

# Windows
set DJANGO_SETTINGS_MODULE=config.settings.local
# Linux / macOS
# export DJANGO_SETTINGS_MODULE=config.settings.local

python backend/manage.py migrate
python backend/manage.py creer_comptes_demo
python backend/manage.py runserver 8001
```

Ouvrir http://127.0.0.1:8001/

| Compte de démonstration | Identifiant | Mot de passe | Situation de départ |
|-------------------------|-------------|--------------|---------------------|
| Cliente | `alice` | `Alice-Demo-2026` | 1 500 EUR, Bob en bénéficiaire |
| Client | `bob` | `Bob-Demo-2026` | 300 EUR, Alice en bénéficiaire |
| Administrateur | `admin` | `Admin-Demo-2026` | Accès à l'administration |

Cartes de test : `4242 4242 4242 4242` (acceptée), `4000 0000 0000 0002` (refusée).

> Les comptes de démonstration ne peuvent être créés qu'en mode `DEBUG`.

## Option 2 — Docker (PostgreSQL, environnement de développement)

```bash
copy .env.example .env            # Windows  (cp sous Linux / macOS)
cd docker
docker compose up --build
docker compose exec web python backend/manage.py migrate
docker compose exec web python backend/manage.py creer_comptes_demo
```

| Service | Port hôte |
|---------|-----------|
| Application Django | 8001 |
| PostgreSQL 16 | 5433 |

## Option 3 — Production (Docker, Gunicorn)

1. Copier `.env.example` vers `.env` et renseigner au minimum :
   `DJANGO_SECRET_KEY` (longue chaîne aléatoire), `DJANGO_ALLOWED_HOSTS`,
   `DJANGO_CSRF_TRUSTED_ORIGINS`, `POSTGRES_PASSWORD`.
2. Lancer :

```bash
cd docker
docker compose -f docker-compose.prod.yml up --build -d
```

Le service `web` applique les migrations, collecte les fichiers statiques puis
démarre Gunicorn (3 workers, utilisateur non-root). Le TLS est attendu en amont
(Nginx, Traefik, Caddy…) ; définir alors `TRUST_X_FORWARDED_FOR=True` si ce
proxy est le seul point d'entrée.

Vérification de la configuration :

```bash
python backend/manage.py check --deploy --settings=config.settings.production
```

Les plafonds (par opération, journalier, alimentation), la devise, la durée de
session et le mode maintenance se règlent ensuite depuis
**Administration → Paramètres**.

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `DJANGO_SECRET_KEY` | — (obligatoire en production) | Clé cryptographique Django |
| `DJANGO_DEBUG` | `False` | Mode debug (forcé à `True` en développement) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Noms d'hôte autorisés |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | Origines HTTPS de confiance (production) |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` | Redirection HTTP → HTTPS (production) |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `finance` | Base de données |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `localhost` / `5433` | Connexion PostgreSQL |
| `CONNEXION_MAX_ECHECS` | `5` | Échecs de connexion avant blocage (×4 par IP) |
| `CONNEXION_DUREE_BLOCAGE_MINUTES` | `15` | Durée du blocage |
| `TRUST_X_FORWARDED_FOR` | `False` | Faire confiance à l'IP transmise par le reverse proxy |
