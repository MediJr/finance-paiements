# Versions des dépendances

| Technologie | Version | Rôle |
|-------------|---------|------|
| Python | 3.12 | Langage (image Docker et CI) |
| Django | 6.0.7 | Framework web |
| Django REST Framework | 3.17.1 | API REST |
| PostgreSQL | 16 (alpine) | Base de données |
| psycopg2-binary | 2.9.12 | Pilote PostgreSQL |
| python-dotenv | 1.2.2 | Chargement du fichier `.env` |
| Gunicorn | 23.0.0 | Serveur d'application (production) |
| WhiteNoise | 6.9.0 | Fichiers statiques (production) |
| pytest | 9.1.1 | Tests |
| pytest-django | 4.12.0 | Intégration pytest / Django |
| pytest-cov | 6.2.1 | Couverture de code |

Dépendances d'exécution : `requirements.txt` ; développement et tests :
`requirements-dev.txt`.
