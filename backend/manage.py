#!/usr/bin/env python
"""Utilitaire en ligne de commande Django pour les tâches administratives."""
import os
import sys
from pathlib import Path


def main():
    """Exécute les tâches administratives Django."""
    backend_dir = Path(__file__).resolve().parent
    app_root = backend_dir.parent
    if str(app_root) not in sys.path:
        sys.path.insert(0, str(app_root))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Vérifiez que l'environnement "
            "virtuel est activé et que Django est installé."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
