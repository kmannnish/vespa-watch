from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ['ENVIRONMENT'] == "dev":
    DEBUG = True
else:
    DEBUG = False
JS_DEBUG = False

# allowed hosts as function of the environment
ALLOWED_HOSTS.extend([
    '.elasticbeanstalk.com',
    '.eu-west-1.elb.amazonaws.com',
    '.localhost',
])
if os.environ['ENVIRONMENT'] == "dev":
    ALLOWED_HOSTS.extend([
        '.vespawatch-dev.eu-west-1.elasticbeanstalk.com',
    ])
if os.environ['ENVIRONMENT'] == "uat":
    ALLOWED_HOSTS.extend([
        '.vespawatch-uat.eu-west-1.elasticbeanstalk.com',
        '.uat.vespawatch.be',
    ])
if os.environ['ENVIRONMENT'] == "prd":
    ALLOWED_HOSTS.extend([
    '.vespawatch-prd.eu-west-1.elasticbeanstalk.com',
    '.vespawatch.be',
    ])


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

# iNaturalist app secret
if os.environ['ENVIRONMENT'] == "prd":
    INAT_APP_SECRET = os.environ['INAT_APP_SECRET']
    INAT_USER_PASSWORD =  os.environ['INAT_USER_PASSWORD']
    INATURALIST_PUSH = True;

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "..", "www", "static")

# ---------- Custom settings ----------

# Logging aws eb

LOG_FILE_PATH = '/opt/python/log/django.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        }
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': LOG_FILE_PATH,
            'backupCount': 3
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    }
}

# increase the alert level for dev environment
if os.environ['ENVIRONMENT'] == 'dev':
    LOGGING['handlers']['file']['level'] = 'INFO'
    LOGGING['loggers']['django']['level'] = 'INFO'

# S3 storage for static and pictures
AWS_ACCESS_KEY_ID = None # None to use AWS internal role/permissions
AWS_STORAGE_BUCKET_NAME = 'lw-vespawatch-{}'.format(os.environ['ENVIRONMENT'])
AWS_QUERYSTRING_AUTH = False
AWS_S3_CUSTOM_DOMAIN = '{}.s3.amazonaws.com'.format(AWS_STORAGE_BUCKET_NAME)
AWS_DEFAULT_ACL = None  # inherit the bucket ACL
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=2592000',  # 30 days
}
AWS_S3_FILE_OVERWRITE = True
AWS_S3_REGION_NAME = 'eu-west-1'

# s3 static file settings
STATICFILES_LOCATION = 'static'
STATICFILES_STORAGE = 'custom_s3_storage.StaticStorage'
STATIC_URL = 'https://{}/{}/'.format(AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

# S3 media file settings
MEDIAFILES_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'custom_s3_storage.MediaStorage'

# Other
VESPAWATCH_BASE_SITE_URL = "http://vespawatch-{}.eu-west-1.elasticbeanstalk.com/".format(os.environ['ENVIRONMENT'])
