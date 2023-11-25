#!/bin/bash

DOMAIN="cookingnetwork.co"
WWW_DOMAIN="www.cookingnetwork.co"
EMAIL="evo.derbro.2023@gmail.com"
WEBROOT_PATH="/var/www/certbot"
STAGING=1 # 設為 1 用於測試，準備部署時改為 0

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "證書不存在，正在為 $DOMAIN 和 $WWW_DOMAIN 生成證書..."

    certbot certonly --webroot \
        -w $WEBROOT_PATH \
        -d $DOMAIN \
        -d $WWW_DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --non-interactive \
        ${STAGING:+--staging}

    echo "證書生成完畢。"
else
    echo "證書已存在，無需重新生成。"
fi
