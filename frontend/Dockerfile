FROM fukamachi/sbcl:2.4.10-debian

RUN apt update
RUN apt-get -y install build-essential
RUN apt-get -y install libfixposix-dev

WORKDIR /var/www
ADD frontend.lisp .
ADD index.html .
ADD favicon.ico .
ADD styles/ styles/
ADD static/ static/

RUN apt-get -y purge build-essential libfixposix-dev
RUN apt-get -y autoremove

ENTRYPOINT []
CMD ["sh", "-c", "sbcl --load /var/www/frontend.lisp"]