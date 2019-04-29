"""
Django settings for djangoproject project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '<SOMETHING_SECRET_TO_REDEFINE_HERE>'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
JS_DEBUG = False

ALLOWED_HOSTS = ['.localhost']

# add private ip from AWS
# cfr. https://hashedin.com/blog/5-gotchas-with-elastic-beanstalk-and-django/
def is_ec2_linux():
    """Detect if we are running on an EC2 Linux Instance

       See http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/identify_ec2_instances.html
    """
    if os.path.isfile("/sys/hypervisor/uuid"):
        with open("/sys/hypervisor/uuid") as f:
            uuid = f.read()
            return uuid.startswith("ec2")
    return False

def get_linux_ec2_private_ip():
    """Get the private IP Address of the machine if running
    on an EC2 linux server
    """
    from urllib import request
    if not is_ec2_linux():
        return None
    try:
        response = request.urlopen('http://169.254.169.254/latest/meta-data/local-ipv4')
        return response.read()
    except:
        return None
    finally:
        if response:
            response.close()
# ElasticBeanstalk healthcheck sends requests with host header = internal ip
# So we detect if we are in elastic beanstalk, and add the instances private ip address
private_ip = get_linux_ec2_private_ip()
if private_ip:
    ALLOWED_HOSTS.append(private_ip)


# Application definition

INSTALLED_APPS = [
    'modeltranslation',  # MUST be before Admin, see https://github.com/deschler/django-modeltranslation/issues/408

    # From Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    # From others
    'crispy_forms',
    'markdownx',
    'imagekit',

    # Local helpers
    'page_fragments',


    'vespawatch'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware'
]

ROOT_URLCONF = 'djangoproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export'
            ],
        },
    },
]

WSGI_APPLICATION = 'djangoproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Brussels'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('nl', _('Dutch')),
    ('en', _('English')),
]

PAGE_FRAGMENTS_FALLBACK_LANGUAGE = 'nl'

LOCALE_PATHS = (os.path.join(BASE_DIR, os.pardir, 'locale'), os.path.join(BASE_DIR, 'locale'), )

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

MEDIA_URL = '/img/'
STATIC_URL = '/static/'


# ---------- Custom settings ----------

# Map

MAP_CIRCLE_FILL_OPACITY = 0.5
MAP_CIRCLE_STROKE_OPACITY = 0.8
MAP_CIRCLE_STROKE_WIDTH = 1
MAP_CIRCLE_NEST_RADIUS = 12
MAP_CIRCLE_INDIVIDUAL_RADIUS = 5
MAP_CIRCLE_INDIVIDUAL_COLOR = '#fd9126'
MAP_CIRCLE_NEST_COLOR = {  # This depend of the management action
    'finished': '#9ccb19',
    'unfinished': '#ee4000',
    'DEFAULT': '#73984a'
}
MAP_CIRCLE_UNKNOWN_COLOR = '#000' # if the subject is not 'Individual' or 'Nest'
MAP_INITIAL_POSITION = [50.85, 4.35]
MAP_INITIAL_ZOOM = 8

MAP_TILELAYER_BASE_URL = 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png'
MAP_TILELAYER_OPTIONS = {
    'attribution': '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://carto.com/attributions">CARTO</a>',
    'subdomains': 'abcd',
    'maxZoom': 20
}


# iNaturalist

INAT_USER_USERNAME = 'vespawatch'
INAT_USER_PASSWORD = ''
INAT_APP_ID = 'd1d0f541791be42e234ce82a5bb8332ab816ff7ab35c6e27b12c0455939a5ea8'
INAT_APP_SECRET = ''


# Other

CRISPY_TEMPLATE_PACK = 'bootstrap4'

LANGUAGES_AVAILABLE_IN_SELECTOR = [
    ('nl', _('Dutch')),
    ('en', _('English')),
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

MARKDOWNX_IMAGE_MAX_SIZE = {
    'size': (1200, 600),
    'quality': 100
}

VESPAWATCH_EVIDENCE_OBS_FIELD_ID = 9770  # The identifier of the "vespawatch_evidence" observation field @iNaturalist
VESPAWATCH_ID_OBS_FIELD_ID = 9613 # # The identifier of the "vespawatch_id" observation field @iNaturalist
VESPAWATCH_PROJECT_ID = 22865  # vespawatch project ID @ iNaturalist
VESPAWATCH_PROJECT_URL = f"https://inaturalist.org/projects/{VESPAWATCH_PROJECT_ID}"
VESPAWATCH_USER_ID = 1263313  # vespawatch user ID @ iNaturalist

WEBSITE_NAME = "Vespa-Watch"


# Exported to templates

SETTINGS_EXPORT = [
    'DEBUG',
    'JS_DEBUG',
    'LANGUAGES',
    'LANGUAGES_AVAILABLE_IN_SELECTOR',
    'VESPAWATCH_EVIDENCE_OBS_FIELD_ID',
    'VESPAWATCH_ID_OBS_FIELD_ID',
    'VESPAWATCH_PROJECT_URL',
    'WEBSITE_NAME'
]
