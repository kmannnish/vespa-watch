# Vespa-watch

## Rationale

This repository contains the website for the monitoring of [_Vespa velutina_](https://www.inaturalist.org/taxa/119019-Vespa-velutina), an invasive species in Belgium.

## Contributors

[List of contributors](https://github.com/inbo/vespa-watch/contributors)

## License

[MIT License](https://github.com/inbo/vespa-watch/blob/master/LICENSE)

## Django webapp

This directory contains the Django project for Vespa-watch.

### Setup

- Use PostgreSQL, create the database first
- Use Python 3.6
- Simple split settings:
    - copy `djangoproject/settings/settings_local.template.py ` to `djangoproject/settings/settings_local.py`
    - tell Django to use those local settings: `$ export DJANGO_SETTINGS_MODULE=djangoproject.settings.settings_local`
