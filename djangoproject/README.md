This directory contains the Django project for Vespa-watch.

Setup:
======

- Use PostgreSQL, create the database first
- Use Python 3.6
- Simple split settings: 
    - copy `djangoproject/settings/settings_local.template.py ` to `djangoproject/settings/settings_local.py`
    - tell Django to use those local settings: `$ export DJANGO_SETTINGS_MODULE=djangoproject.settings.settings_local`
