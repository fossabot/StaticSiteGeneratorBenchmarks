FROM ruby:2.1
ADD Gemfile /opt/
ADD Gemfile.lock /opt/
WORKDIR /opt
RUN bundle install
CMD ["bundle exec nanoc -v"]
