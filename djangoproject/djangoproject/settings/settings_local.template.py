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