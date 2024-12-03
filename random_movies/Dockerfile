FROM rust:1.82.0-slim-bullseye

WORKDIR /var/www
RUN apt-get update
RUN apt-get -y install libssl-dev pkg-config
ADD Cargo.lock .
ADD Cargo.toml .
ADD src/ src/
CMD ["sh", "-c", "cargo run"]