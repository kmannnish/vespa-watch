# Vespa-watch

Django app for the monitoring and management of [_Vespa velutina_](https://www.inaturalist.org/taxa/119019-Vespa-velutina), an invasive species in Belgium.

## Installation

### Setup database

1. Create an empty PostgreSQL database (e.g. `vespa-watch`)
2. Enable PostGIS: `CREATE EXTENSION postgis;`

### Define settings

1. Clone this repository: `git clone https://github.com/inbo/vespa-watch`
2. Copy `djangoproject/settings/settings_local.template.py` to `djangoproject/settings/settings_local.py`
3. In that file, verify the database settings are correct and set `SECRET_KEY` to a non-empty value

### Setup python environment

1. Create a virtual environment, e.g. `conda create -n vespawatch python=3.6`
2. Activate the environment, e.g. `source activate vespawatch`
3. Navigate to the project directory and install the requirements: `pip install -r requirements.txt`
4. Tell Django to use the local settings: `export DJANGO_SETTINGS_MODULE=djangoproject.settings.settings_local`

### Apply database migrations

```bash
python manage.py migrate
```

### Create superuser

In development (this will prompt you for a username, email and password):

```bash
python manage.py createsuperuser
```

In production use instead:

```bash
python manage.py create_su
```

### Create fire brigade users

A fire brigade user is responsible for a specific zone. Import zone geospatial information:

```bash
python manage.py import_firefighters_zones data/Brandweerzones_2019.geojson
```

Create a fire brigade user for each zone (this will return passwords in the console, so you might want to catch those):

```bash
python manage.py create_firefighters_accounts
```

### Load data from iNaturalist

Initialize the database with observations from iNaturalist:

```bash
python manage.py sync_pull
```

## Run the application

In your virtual environment:

```bash
python manage.py runserver
```

Go to http://localhost:9000 to see the application.

## Development

### CSS/SASS

We use SASS to generate our custom stylesheets, meaning:

* Never manually edit `static/vespawatch/css/main.css`
* Instead, make changes in `static_src/scss/*` and compile them with `npm run create:css`. The resulting files 
will be saved under `static/vespawatch/css/` so they are made available the standard way to django (for template inclusion, `
the collectstatic command, ...)
* In development you can use `npm run watch:css` instead, so the SASS files are automatically compiled on save.
* The first time, you'll need to install the dependencies for this process: ``npm install``

### GeoDjango / PostGIS setup notes

Vespa-Watch relies on GeoDjango/PostGIS. Refer to their documentation if needed.

The initial firefighters zone data was received as an ESRI shapefile. Convert it to GeoJSON prior to use with:

```bash
ogr2ogr -f GeoJSON -t_srs EPSG:4326 data/Brandweerzones_2019.geojson <path_to_received_shapefile>/Brandweerzones_2019.shp
```

## Contributors

[List of contributors](https://github.com/inbo/vespa-watch/contributors)

## License

[MIT License](https://github.com/inbo/vespa-watch/blob/master/LICENSE)
