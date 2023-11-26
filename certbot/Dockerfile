
FROM certbot/certbot:v2.7.4

RUN apk add certbot-nginx

COPY ./init-certbot.sh /init-certbot.sh
RUN chmod +x /init-certbot.sh
CMD ["/init-certbot.sh"]
