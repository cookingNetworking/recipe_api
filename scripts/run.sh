#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py migrate
python manage.py shell_plus -c "from recipe.tasks import set_up_for_server_start; set_up_for_server_start.delay()"

daphne -b 0.0.0.0 -p 8001 app.asgi:application

uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi

