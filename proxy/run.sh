#!/bin/sh
echo "LISTEN_PORT: $LISTEN_PORT"
echo "APP_HOST: $APP_HOST"
echo "APP_PORT: $APP_PORT"

set -e
envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
cat /etc/nginx/default.conf.tpl
nginx -g 'daemon off;'