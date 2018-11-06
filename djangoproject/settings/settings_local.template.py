from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'vespa-watch',
        'HOST': 'localhost',
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '<SOMETHING_SECRET_TO_REDEFINE_HERE>'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INAT_USER_USERNAME = 'vespawatch'
INAT_USER_PASSWORD = ''
INAT_APP_ID = 'd1d0f541791be42e234ce82a5bb8332ab816ff7ab35c6e27b12c0455939a5ea8'
INAT_APP_SECRET = ''