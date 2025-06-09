#!/bin/bash

if [ "$APP_ENV" == "DEVELOPMENT" ]; then
    python3 dynamic_update.py & 
    uwsgi config_development.ini

elif [ "$APP_ENV" == "PRODUCTION" ]; then
    python3 dynamic_update.py & 
    uwsgi config_production.ini

else
    echo ERROR in ENV setting.

fi

