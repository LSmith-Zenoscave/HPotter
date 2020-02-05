# command:
# docker run --init -p 22:22 -p 23:23 -p 80:8080 -p 8000:8000 \
#        -v /var/run/docker.sock:/var/run/docker.sock <image_name>

FROM alpine
EXPOSE 22 23 80 8000

RUN apk update
RUN apk add python3 
RUN pip3 install --upgrade pip
RUN apk add git
RUN apk add build-base
RUN apk add python3-dev
RUN apk add libffi-dev
RUN apk add postgresql-dev
RUN apk add openssl-dev
RUN apk add mariadb-dev

WORKDIR /HPotter

COPY requirements.txt setup.py ./
RUN pip install -r requirements.txt
COPY hpotter ./hpotter/
COPY RSAKey.cfg ./
RUN chmod +x ./runit.sh

ENTRYPOINT [ "ash", "-c", "python3 -m hpotter.jsonserver &>/dev/null & python3 -m hpotter" ]
