#!/bin/sh

if [ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
  certbot certonly --webroot -w /var/www/certbot -d ${DOMAIN} --email evo.derbro.2023@gmail.com --agree-tos --non-interactive
fi

set -e

envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
