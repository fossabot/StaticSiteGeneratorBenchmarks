FROM node:alpine

RUN apk --update add git python make g++ && \
  npm install cuttlebelle --global && \
  apk del git python make g++ && rm -rf /var/cache/apk/*

RUN cuttlebelle
