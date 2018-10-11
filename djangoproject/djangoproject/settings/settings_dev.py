from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['RDS_DB_NAME'],
        'USER': os.environ['RDS_USERNAME'],
        'PASSWORD': os.environ['RDS_PASSWORD'],
        'HOST': os.environ['RDS_HOSTNAME'],
        'PORT': os.environ['RDS_PORT'],
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, "..", "www", "static")
STATIC_URL = '/static/'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'SECRETPHRASEFORDEV'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INAT_USER_USERNAME = 'vespawatch'
INAT_USER_PASSWORD = ''
INAT_APP_ID = 'd1d0f541791be42e234ce82a5bb8332ab816ff7ab35c6e27b12c0455939a5ea8'
INAT_APP_SECRET = ''
