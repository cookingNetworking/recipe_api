server {
    listen 80;
    server_name cookingnetwork.co;


    location ^~ /.well-known/acme-challenge/ {
        allow all;
        root /var/www/certbot;
        try_files $uri $uri/ =404;
        break;
    }


    location / {
        return 301 https://$host$request_uri;
    }
}

#https
server {
    listen 8443 ssl;
    server_name $cookingnetwork.co;

    ssl_certificate /etc/letsencrypt/live/cookingnetwork.co/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cookingnetwork.co/privkey.pem;

    location / {
        uwsgi_pass app:9000;
        include /etc/nginx/uwsgi_params;
        client_max_body_size 10M;
    }

    location /static {
        alias /vol/static;
    }

}
