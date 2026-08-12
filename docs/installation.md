# Guide d'installation — Finance (11-finance)

## Prérequis

- Python 3.12 ou supérieur
- Docker et Docker Compose (recommandé pour PostgreSQL)
- Git

## Installation pas à pas

### 1. Se placer dans l'application

```bash
cd Logiciels/applications/11-finance
```

### 2. Environnement virtuel Python

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Variables d'environnement

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS
```

Adapter `DJANGO_SECRET_KEY` avant tout usage hors développement local.

### 5. Démarrer PostgreSQL

```bash
cd docker
docker compose up -d db
```

Vérifier que le conteneur est actif :

```bash
docker compose ps
```

### 6. Vérifier Django

```bash
cd ../backend
python manage.py check
```

### 7. Appliquer les migrations Django système

```bash
python manage.py migrate
```

### 8. Créer un superutilisateur (recommandé)

```bash
python manage.py createsuperuser
```

### 9. Lancer le serveur

```bash
python manage.py runserver 8001
```

Accéder à :

- `http://127.0.0.1:8001/utilisateurs/` — liste des utilisateurs
- `http://127.0.0.1:8001/api/utilisateurs/` — API utilisateurs
- `http://127.0.0.1:8001/admin/` — administration Django

### 10. Exécuter les tests

```bash
cd ..
pytest
```

Création d'un utilisateur métier (shell Django) :

```bash
python manage.py shell
```

```python
from accounts.services import create_utilisateur
create_utilisateur(
    username='alice',
    password='MotDePasseFort123!',
    prenom='Alice',
    nom='Martin',
    email='alice@example.com',
)
```

## Démarrage complet via Docker

```bash
cd docker
docker compose up -d
```

L'application est alors disponible sur le port `8001`.

## Dépannage

- **Port 5433 déjà utilisé** : modifier `POSTGRES_PORT` dans `.env` et `docker-compose.yml`.
- **Échec de connexion PostgreSQL** : vérifier que `docker compose up -d db` a réussi et que `POSTGRES_HOST` / `POSTGRES_PORT` correspondent.
- **Module `config` introuvable** : exécuter les commandes depuis `backend/` ou utiliser `pytest` à la racine de l'application (voir `pytest.ini`).
