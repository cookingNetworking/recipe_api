#!/bin/sh

set -e

echo "LISTEN_PORT: $LISTEN_PORT"
echo "APP_HOST: $APP_HOST"
echo "APP_PORT: $APP_PORT"
envsubst '$LISTEN_PORT,$APP_HOST,$APP_PORT' < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
cat /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
