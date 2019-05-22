# Setup unit tests locally

## Create a database

Create a database for unit tests and install the `POSTGIS` extension
in it:

```
CREATE DATABASE mytestdatabase OWNER myuser;
\c mytestdatabase
CREATE EXTENSION POSTGIS;
```

## Settings

Add a `TEST` section to your local database settings.

Example:

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'USER': 'mydatabaseuser',
        'NAME': 'mydatabase',
        'TEST': {
            'NAME': 'mytestdatabase',
        },
    },
}
```

## Run unit tests

You can run the unit tests from the main directory as:

```
python manage.py test --keepdb
```

Use the `--keepdb` option to prevent the database from being destroyed
after the test run.

> Djangos default behaviour is to create a test database itself when
running unit tests and destroying that afterwards. However, that
requires additional permissions which are not necessary if you use the
`--keepdb` flag.
