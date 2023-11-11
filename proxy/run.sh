#!/bin/sh

if [ ! -d "/etc/letsencrypt/live/cookingnetwork.co" ]; then
  certbot certonly --webroot -w /var/www/certbot -d cookingnetwork.co --email evo.derbro.2023@gmail.com --agree-tos --non-interactive --staging
fi

set -e

envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
