server {
    listen ${LISTEN_PORT} ssl;
    server_name ${DOMAIN};

    location ^~ /.well-known/acme-challenge/ {
        allow all;
        root /var/www/certbot;
        try_files $uri =404;
        break;
    }

    location /static {
        alias /vol/static;
    }

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    location / {
        uwsgi_pass ${APP_HOST}:${APP_PORT};
        include /etc/nginx/uwsgi_params;
        client_max_body_size 10M;
    }

}

