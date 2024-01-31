
server {

    # static file
    location /static {
        alias /vol/static;
    }


    location / {
        uwsgi_pass app:9000;
        include /etc/nginx/uwsgi_params;
        client_max_body_size 10M;
	add_header 'Access-Control-Allow-Origin' 'https://www.cookingnetwork.co';
        add_header 'Access-Control-Allow-Credentials' 'true';
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

