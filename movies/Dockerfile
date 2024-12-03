FROM debian:12.8-slim
WORKDIR /var/www

RUN apt-get update
RUN apt-get -y install build-essential
RUN apt-get -y install pkg-config
RUN apt-get -y install openssl
RUN apt-get -y install libssl-dev
RUN apt-get -y install zlib1g-dev zlib1g lib32z1-dev
RUN apt-get -y install ldc
RUN apt-get -y install dub

ADD source/ source/
ADD dub.json .
ADD dub.selections.json .

CMD ["sh", "-c", "DC=ldc2 dub run"]