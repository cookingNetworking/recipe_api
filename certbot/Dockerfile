FROM certbot/certbot:latest

RUN pip3 install certbot-nginx

COPY ./run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT ["/run.sh"]
