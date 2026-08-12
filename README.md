# Finance — Plateforme de paiements numériques

Application `11-finance` (**Security by Design**).

> **Contexte lab** : environnement de développement / expérimentation, pas une configuration de production.

## Statut

**Terminée** — Prototype 4 Sprint 10 (exports CSV / JSON).

## Installation et lancement

Le guide complet se trouve dans **[docs/installation.md](docs/installation.md)**.

Résumé :

```bash
cd applications/11-finance
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env

cd docker
docker compose up -d db

cd ../backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001
```

Application : `http://127.0.0.1:8001/`  
Administration (comptes `is_staff`) : `http://127.0.0.1:8001/administration/`

Adapter `DJANGO_SECRET_KEY` dans `.env` avant tout usage hors développement local. Ne pas committer le fichier `.env`.

## Structure

```text
accounts/ wallets/ historique/ beneficiaires/
virements/ paiements/
administration/   # Paramètres + sécurité + pilotage + exports
observabilite/    # Journal d'événements
api/ frontend/ tests/ docs/ livrables/
```

## Exports

Voir [docs/exports.md](docs/exports.md).

- Web : `/administration/exports/`
- API : `/api/administration/exports/?type=…&export_format=json|csv`

## Tests

```bash
pytest
```

## Documentation

Index : [docs/README.md](docs/README.md) · Installation : [docs/installation.md](docs/installation.md)
