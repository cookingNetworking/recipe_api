FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="GSHIN"


ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000
ENV DOMAIN=cookingnetwork.co

USER root
# 安装 Certbot
RUN apk --no-cache add certbot

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./no-ssl.conf.tpl /etc/nginx/no-ssl.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./proxy_params /etc/nginx/proxy_params
COPY ./run.sh /run.sh

RUN mkdir -p /vol/static && \
    chmod 755 /vol/static && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh


VOLUME /vol/static



USER nginx

CMD ["/run.sh"]
