FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="GSHIN"


ENV LISTEN_PORT=8443
ENV APP_HOST=app
ENV APP_PORT=9000
ENV DOMAIN=cookingnetwork.co

USER root

RUN apk add --no-cache certbot && \
    mkdir -p /var/www/certbot && \
    mkdir -p /etc/letsencrypt && \
    mkdir -p /var/lib/letsencrypt && \
    mkdir -p /var/log/letsencrypt && \
    chown -R nginx:nginx /var/www/certbot && \
    chown -R nginx:nginx /etc/letsencrypt && \
    chown -R nginx:nginx /var/lib/letsencrypt && \
    chown -R nginx:nginx /var/log/letsencrypt

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh
COPY ./certbot-renew /etc/periodic/daily/certbot-renew

RUN mkdir -p /vol/static && \
    chmod 755 /vol/static && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh && \
    chmod +x /etc/periodic/daily/certbot-renew


VOLUME /vol/static
VOLUME /etc/letsencrypt
VOLUME /var/lib/letsencrypt
VOLUME /var/log/letsencrypt
VOLUME /var/www/certbot

USER nginx

CMD ["/run.sh"]