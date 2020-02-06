# command:
# docker run --init -p 22:22 -p 23:23 -p 80:8080 -p 8000:8000 \
#        -v /var/run/docker.sock:/var/run/docker.sock \
#        -v `pwd`/plugins.yml:/HPotter/plugins.yml <image_name>

FROM alpine

RUN apk add --update --no-cache \
    python3 \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev
RUN pip3 install --upgrade pip

WORKDIR /HPotter

COPY requirements.txt setup.py ./
RUN pip install -r requirements.txt
COPY hpotter ./hpotter/
COPY RSAKey.cfg ./

ENTRYPOINT python3 -m hpotter
