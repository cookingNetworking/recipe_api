
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

        # CORS head
        add_header Access-Control-Allow-Methods 'GET,POST,DELETE,PUT,PATCH,OPTIONS';
        add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization,X-CSRFToken,Origin,sessionid';
        add_header 'Access-Control-Max-Age' 1728000;
        }
    location /ws/ {
        proxy_pass http://unix:/tmp/daphne.sock;
        proxy_http_version 1.1;
        proxy_redirect off;
        proxy_buffering off;
        include /etc/nginx/proxy_params;
        }
}

