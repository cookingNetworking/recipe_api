
server {
    listen ${LISTEN_PORT};
    server_name cookingnetwork.co www.cookingnetwork.co;
    # static file
    location /static {
        alias /vol/web/static/static;
    }


    location / {
        uwsgi_pass ${APP_HOST}:${APP_PORT};
        include /etc/nginx/uwsgi_params;
        client_max_body_size 50M;
        }
    location /ws/ {
        proxy_pass http://unix:/tmp/daphne.sock;
        proxy_http_version 1.1;
        proxy_redirect off;
        proxy_buffering off;
        include /etc/nginx/proxy_params;
        }
}

