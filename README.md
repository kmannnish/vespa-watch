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


### CSS/SASS

We use SASS to generate our custom stylesheets, meaning:

- Never manually edit `static/vespawatch/css/main.css`
- Instead, make changes in `static_src/scss/*` and compile them with `npm run create:css`. The resulting files 
will be saved under `static/vespawatch/css/` so they are made available the standard way to django (for template inclusion, `
the collectstatic command, ...)
- In development you can use `npm run watch:css` instead, so the SASS files are automatically compiled on save.
- The first time, you'll need to install the dependencies for this process: ``npm install``

### GeoDjango / PostGIS setup notes

- Geographic libraries needed: GEOS, PROJ.4, GDAL
- Install PostGIS on existing PosgreSQL database:

    $ psql -d <db_name>
    
    psql (9.6.5, server 9.6.8)
    Type "help" for help.

    vespa-watch=# CREATE EXTENSION postgis;
    
- The FirefightersZone model has a "polygon" field. Don't hesitate to set/edit it in the Admin to 
check GeoDjango/Postgis are functional.


    