
# HPotter
A simple to install and run Honey Pot.

(README may be out of date. Update TDB)

[![Build Status](https://travis-ci.org/drsjb80/HPotter.svg?branch=master)](https://travis-ci.org/drsjb80/HPotter)

## Running and developing

To install the necessary packages, do:

    pip install -r requirements.txt

To run the honeypot itself, do:

    python3 -m hpotter

To run the SQL to JSON webserver, do:

    python3 -m hpotter.jsonserver

Once the jsonserver is running, you can see the current data by loading the
ajax.html file that is in the directory above into your web browser.

To see the current contents of the database, do:
    sqlite3 -list main.db .dump

The JSON API is easy to query. To get all the data, go to localhost:8080:

    curl localhost:8080

If you're interested in a particular table, reference that:

    curl localhost:8080/sh

If you want to use JSONP, pass a callback:

    curl localhost:8080/?callback=jQuery

To get JSON in the form to use with jTables, do:

    curl localhost:8080/?handd=true

## Databases
The default database is SQLite and requires no configuration. The tables
are written into the default ("main.db") database.

If you'd like to use a different database, there are some environment
variables that need setting.

HPOTTER\_DB -- the name of the database type, e.g.: "mysql".
    Defaults to "sqlite".

HPOTTER\_DB\_PASSWORD -- e.g.: "my-secret-pw".
    Defaults to "".

HPOTTER\_DB\_HOST
    Defaults to "127.0.0.1".

HPOTTER\_DB\_PORT -- e.g.: 3306
    Defaults to "".

HPOTTER\_DB\_DB -- The database where the tables are placed e.g.: hpotter.
Created if not present.  Defaults to "hpotter".

## Directory structure
hpotter/

This is the main honeypot executable. It looks in plugins and runs all the
plugins found there.

plugins/

This is where the protocol-specific plugins reside. They are based on
https://docs.python.org/3/library/socketserver.html  The generic.py file is
a good place to start for creating your own plugins.

jsonserver/

Where the SQL to JSON web server resides.    

## Thanks
This product includes GeoLite2 data created by MaxMind, available from
<a href="https://www.maxmind.com">https://www.maxmind.com</a>.
