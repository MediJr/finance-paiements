# Versions des technologies — Sprint 0

| Technologie | Version | Remarque |
|-------------|---------|----------|
| Python | 3.12.4 | Environnement local |
| Django | 6.0.7 | Framework backend |
| Django REST Framework | 3.17.1 | API REST |
| PostgreSQL | 16 (Alpine) | Image Docker `postgres:16-alpine` |
| Docker | 29.5.3 | Moteur de conteneurisation |
| Docker Compose | v5.1.4 | Orchestration |
| pytest | 9.1.1 | Framework de tests |
| pytest-django | 4.12.0 | Intégration Django/pytest |
| psycopg2-binary | 2.9.12 | Driver PostgreSQL |
| python-dotenv | 1.2.2 | Gestion des variables d'environnement |

## Vérification

```bash
python --version
python -m django --version
pip show djangorestframework pytest psycopg2-binary
docker --version
docker compose version
```
