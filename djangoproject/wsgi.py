"""
WSGI config for djangoproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

if os.environ['ENVIRONMENT'] == "dev":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoproject.settings.settings_dev'
elif os.environ['ENVIRONMENT'] == "prd":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoproject.settings.settings_prd'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoproject.settings.settings_local'

application = get_wsgi_application()
