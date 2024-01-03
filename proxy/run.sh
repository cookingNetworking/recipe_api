#!/bin/sh


set -e
envsubst < /etc/nginx/no-ssl.conf.tpl > /etc/nginx/conf.d/default.conf

nginx -g 'daemon off;'