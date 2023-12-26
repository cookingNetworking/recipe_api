
server {
    listen 80;
    server_name cookingnetwork.co www.cookingnetwork.co;



    location / {
        return 301 https://$host$request_uri;
    }
}

server {

    # static file
    location /static {
        alias /vol/static;
    }


    location / {
        uwsgi_pass app:9000;
        include /etc/nginx/uwsgi_params;
        client_max_body_size 10M;

        # CORS head
        add_header 'Access-Control-Allow-Origin' 'https://cookingnetwork.vercel.app';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        add_header 'Access-Control-Allow-Credentials' 'true';
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain charset=UTF-8';
        add_header 'Content-Length' 0;
        return 204;


        }
    location /ws/ {
    proxy_pass http://django_daphne;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    # 其他WebSocket代理设置...
}
}
