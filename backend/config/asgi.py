"""
Point d'entrée ASGI pour le déploiement asynchrone du projet Django.
"""

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

backend_dir = Path(__file__).resolve().parent.parent
app_root = backend_dir.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
