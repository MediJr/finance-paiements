# Rapport technique — Sprint 0 — Initialisation

**Application** : 11-finance (Plateforme de paiements numériques)  
**Prototype** : 1 — Fondation de l'application  
**Date** : 6 août 2026  
**Statut** : Terminé — en attente de validation

---

## 1. Résumé technique

Le Sprint 0 a mis en place les fondations techniques de l'application **Finance**, référence Security by Design du laboratoire pour les API de paiement.

Aucune fonctionnalité métier n'a été développée. Le projet suit l'architecture MTV Django du laboratoire, avec séparation `backend/`, `api/`, `frontend/`, `database/`, `docker/`, `tests/`, `docs/` et `livrables/`.

Django REST Framework est configuré, PostgreSQL est préparé via Docker, et la suite pytest valide la configuration technique.

---

## 2. Fonctionnalités développées

Aucune fonctionnalité métier (conformément au cahier des charges).

Travaux techniques réalisés :

- Arborescence de l'application `11-finance`
- Projet Django 6.0 avec settings modulaires (`base`, `development`, `test`)
- Application `api` (structure prête, racine technique uniquement)
- Configuration PostgreSQL via variables d'environnement
- Docker (Dockerfile + docker-compose : PostgreSQL 16 + Django)
- Authentification Django standard (pas de modèle utilisateur personnalisé)
- Logging de base
- Suite pytest (7 tests de configuration)
- Documentation technique initiale

---

## 3. Architecture créée

```text
Client
  ├── /         → Statut technique JSON
  ├── /admin/   → Administration Django
  └── /api/     → Racine API technique (DRF)
         │
         ▼
   backend/config (settings, urls)
         │
         ▼
   PostgreSQL (tables Django système uniquement)
```

---

## 4. Arborescence obtenue

Voir `structure-dossiers.txt`.

---

## 5. Fichiers créés

| Fichier / Dossier | Rôle |
|-------------------|------|
| `backend/manage.py` | CLI Django |
| `backend/config/` | Settings, URLs, WSGI, ASGI |
| `api/` | Application DRF (racine technique) |
| `frontend/templates/`, `frontend/static/` | Ressources frontend |
| `database/init/01-init.sql` | Script d'initialisation PostgreSQL |
| `docker/Dockerfile` | Image Python 3.12 |
| `docker/docker-compose.yml` | Orchestration db + web |
| `tests/test_configuration.py` | Tests de configuration |
| `tests/conftest.py` | Configuration pytest |
| `pytest.ini` | Configuration pytest |
| `requirements.txt` | Dépendances Python |
| `.env.example` | Modèle de variables d'environnement |
| `.gitignore` | Exclusions Git |
| `docs/architecture.md` | Documentation architecture |
| `docs/versions.md` | Versions des technologies |
| `docs/installation.md` | Guide d'installation |
| `README.md`, `CHANGELOG.md` | Documentation application |
| `livrables/Sprint-00/` | Livrables du sprint |
| `media/` | Répertoire médias |

---

## 6. Fichiers modifiés

Aucun fichier hors création initiale (le `README.md` placeholder a été remplacé).

---

## 7. Dépendances installées

| Paquet | Version |
|--------|---------|
| Django | 6.0.7 |
| djangorestframework | 3.17.1 |
| psycopg2-binary | 2.9.12 |
| pytest | 9.1.1 |
| pytest-django | 4.12.0 |
| python-dotenv | 1.2.2 |

---

## 8. Configuration réalisée

- Settings modulaires (`base` / `development` / `test`)
- PostgreSQL via `.env` (ports locaux `5433` / app `8001`)
- DRF : SessionAuthentication, IsAuthenticated, JSON
- Authentification Django + validateurs de mots de passe
- Logging console de base
- pytest-django avec SQLite en mémoire pour les tests

---

## 9. Migrations

Aucune migration métier créée.

Les migrations Django système (`auth`, `admin`, `contenttypes`, `sessions`) sont applicables via `python manage.py migrate` une fois PostgreSQL démarré.

---

## 10. Modèles / Services / API / Templates

| Élément | Sprint 0 |
|---------|----------|
| Modèles métier | Aucun |
| Services métier | Aucun |
| Endpoints API métier | Aucun (`/api/` racine technique uniquement) |
| Templates métier | Aucun |

---

## 11. Résultats des tests

### Django — `manage.py check`

```
System check identified no issues (0 silenced).
```

**Résultat** : OK

### pytest — 7 tests

```
tests/test_configuration.py::test_database_configuration PASSED
tests/test_configuration.py::test_installed_apps PASSED
tests/test_configuration.py::test_django_configuration_is_valid PASSED
tests/test_configuration.py::test_api_url_prefix_is_accessible PASSED
tests/test_configuration.py::test_drf_is_configured PASSED
tests/test_configuration.py::test_root_status_endpoint PASSED
tests/test_configuration.py::test_auth_password_validators_configured PASSED

7 passed in 0.42s
```

**Résultat** : OK — 7/7 tests passés

### Docker Compose — validation

```
docker compose config
```

**Résultat** : OK — configuration valide (services `db` et `web`)

### PostgreSQL / runserver

**Résultat** : Connexion effective non testée — Docker Desktop arrêté (`dockerDesktopLinuxEngine` indisponible).  
La configuration Docker a été validée via `docker compose config`.

---

## 12. Difficultés rencontrées

1. **Docker Desktop non démarré** — Impossible de lancer PostgreSQL et de valider `migrate` / `runserver` avec connexion réelle. Même situation que le Sprint 0 de `01-bibliotheque`.

2. **Ports locaux** — Choix des ports `5433` (PostgreSQL) et `8001` (Django) pour éviter les conflits avec d'autres applications du laboratoire.

---

## 13. Recommandations pour le Sprint 1

1. Démarrer Docker Desktop et lancer PostgreSQL (`docker compose up -d db`)
2. Appliquer les migrations Django système (`python manage.py migrate`)
3. Développer uniquement les fonctionnalités demandées par le Sprint 1 (ex. authentification / comptes si demandés)
4. Conserver la séparation services / vues dès les premières règles métier
5. Renforcer progressivement les contrôles Security by Design (sans anticiper SIEM / observabilité)

---

## 14. Proposition de message de commit Git

```
feat(finance): initialisation du projet — Prototype 1 Sprint 0
```

**Note** : aucun commit n'a été créé. En attente de validation.

---

**Fin du rapport — Sprint 0**
