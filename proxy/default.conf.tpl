
server {
    listen 80;
    server_name cookingnetwork.co www.cookingnetwork.co; 


    location ^~ /.well-known/acme-challenge/ {
        allow all;
        root /var/www/certbot;
        try_files $uri $uri/ =404;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl; 
    server_name cookingnetwork.co www.cookingnetwork.co; 

    if (-f /etc/letsencrypt/live/cookingnetwork.co/fullchain.pem) {
        ssl_certificate /etc/letsencrypt/live/cookingnetwork.co/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/cookingnetwork.co/privkey.pem;
    }

 

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
}
