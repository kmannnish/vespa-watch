from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
JS_DEBUG = False

ALLOWED_HOSTS = [
    '.elasticbeanstalk.com',
    '.eu-west-1.elb.amazonaws.com',
    '.vespawatch-dev.eu-west-1.elasticbeanstalk.com',
    '.localhost',
]

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ['RDS_DB_NAME'],  # environmental variables exposed by elastic beanstalk
        'USER': os.environ['RDS_USERNAME'],
        'PASSWORD': os.environ['RDS_PASSWORD'],
        'HOST': os.environ['RDS_HOSTNAME'],
        'PORT': os.environ['RDS_PORT'],
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "..", "www", "static")
STATIC_URL = '/static/'


# ---------- Custom settings ----------

# Logging aws eb

LOG_FILE_PATH = '/opt/python/log/django.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}


# S3 static storage for media files

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = None # None to use AWS internal role/permissions
AWS_STORAGE_BUCKET_NAME = 'lw-vespawatch'
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 day
}
AWS_S3_FILE_OVERWRITE = True
AWS_S3_REGION_NAME = 'eu-west-1'
AWS_LOCATION = 'media'


# Other

VESPAWATCH_BASE_SITE_URL = "http://vespawatch-dev.eu-west-1.elasticbeanstalk.com/"
