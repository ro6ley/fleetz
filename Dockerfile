FROM python:3.8-alpine

LABEL maintainer="robleyadrian@gmail.com"

EXPOSE 80

RUN apk update && apk add dcron curl wget rsync ca-certificates bash g++ build-base python3-dev musl-dev && apk add postgresql-dev && rm -rf /var/cache/apk/*

RUN mkdir -p /var/log/supervisor

ADD . /fleetz

WORKDIR /fleetz

RUN pip install -r requirements.txt

RUN python manage.py collectstatic

COPY run.sh run.sh

RUN chmod +x run.sh

CMD ["./run.sh"]
