"""
WSGI config for astralfin project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'astralfin.settings')

application = get_wsgi_application()
