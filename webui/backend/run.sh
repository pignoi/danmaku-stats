#!/bin/bash

if [ "$APP_ENV" == "DEVELOPMENT" ]; then
    uwsgi config_development.ini
elif [ "$APP_ENV" == "PRODUCTION" ]; then
    uwsgi config_production.ini
else
    echo ERROR in ENV setting.
fi

