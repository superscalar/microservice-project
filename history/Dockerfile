FROM ruby:3.3.5

WORKDIR /var/www
ADD history_microservice.rb .
ADD Gemfile .
ADD config.ru .
RUN bundle install
RUN chmod +x history_microservice.rb

# for some reason, the rackup executable doesn't get installed just with bundle
RUN gem install rackup

CMD ["sh", "-c", "rackup --host 0.0.0.0 -p $HISTORY_PORT"]