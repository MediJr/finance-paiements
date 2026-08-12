"""
Point d'entrée WSGI pour le déploiement du projet Django.
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

backend_dir = Path(__file__).resolve().parent.parent
app_root = backend_dir.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
