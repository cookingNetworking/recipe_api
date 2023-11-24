#!/bin/sh
echo "LISTEN_PORT: $LISTEN_PORT"
echo "APP_HOST: $APP_HOST"
echo "APP_PORT: $APP_PORT"

set -e

if [ -f /etc/letsencrypt/live/cookingnetwork.co/fullchain.pem ]; then

    envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
else

    envsubst < /etc/nginx/no-ssl.conf.tpl > /etc/nginx/conf.d/default.conf
fi


cat /etc/nginx/conf.d/default.conf


nginx -g 'daemon off;'