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


### Importing firefighters zone / creating accounts

When deploying the application, you'll need to import the firefighters zone data:

$ python manage.py import_firefighters_zones data/Brandweerzones_2019.geojson

Then, we'll create a user account for each of these zones:

$ python manage.py create_firefighters_accounts

### CSS/SASS

We use SASS to generate our custom stylesheets, meaning:

- Never manually edit `static/vespawatch/css/main.css`
- Instead, make changes in `static_src/scss/*` and compile them with `npm run create:css`. The resulting files 
will be saved under `static/vespawatch/css/` so they are made available the standard way to django (for template inclusion, `
the collectstatic command, ...)
- In development you can use `npm run watch:css` instead, so the SASS files are automatically compiled on save.
- The first time, you'll need to install the dependencies for this process: ``npm install``

### GeoDjango / PostGIS setup notes

Vespa-Watch relies on GeoDjango/PostGIS. Refer to their documentation if needed.

The initial firefighters zone data was received as an ESRI shapefile. Convert it to GeoJSON prior to use with:

$ ogr2ogr -f GeoJSON -t_srs EPSG:4326 data/Brandweerzones_2019.geojson <path_to_received_shapefile>/Brandweerzones_2019.shp
