#!/bin/sh
DOMAIN="cookingnetwork.co"
WWW_DOMAIN="www.cookingnetwork.co"
EMAIL="evo.derbro.2023@gmail.com"
WEBROOT_PATH="/var/www/certbot"
STAGING=1 # Set to 1 for testing, 0 for production

# Create the certificates if they do not exist
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "No certificates found for $DOMAIN and $WWW_DOMAIN. Generating now..."

    # Determine if we should use the staging flag
    if [ "$STAGING" -eq "1" ]; then
        STAGING_FLAG="--staging"
    else
        STAGING_FLAG=""
    fi

    # Run the certbot command with the determined flags
    certbot certonly --webroot \
        -w $WEBROOT_PATH \
        -d $DOMAIN \
        -d $WWW_DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --non-interactive \
        $STAGING_FLAG \

    echo "Certificate generation complete."
else
    echo "Certificates already exist for $DOMAIN, no need to regenerate."
fi
