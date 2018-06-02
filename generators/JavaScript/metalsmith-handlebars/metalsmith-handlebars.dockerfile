FROM node:boron

RUN npm install --save-dev \
    metalsmith \
    metalsmith-assets \
    metalsmith-browser-sync \
    metalsmith-collections \
    metalsmith-feed \
    metalsmith-html-minifier \
    metalsmith-in-place \
    metalsmith-layouts \
    metalsmith-mapsite \
    metalsmith-markdown \
    metalsmith-permalinks \
    metalsmith-publish \
    metalsmith-serve \
    metalsmith-word-count \
    handlebars

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

EXPOSE 8080

RUN apt-get update && apt-get install -y \
    lighttpd

COPY lighttpd.conf /etc/lighttpd/

COPY startup.sh /

CMD "/startup.sh"
