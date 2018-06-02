FROM node:9-alpine

ENV NODE_ENV production

RUN apk --update add git python make g++ && \
  npm install -g harp@0.17.0 && \
  apk del git python make g++ && rm -rf /var/cache/apk/*

  RUN npm install -g jade@1.11.0
  ENTRYPOINT ["/usr/local/bin/jade"]

EXPOSE 9000
ENTRYPOINT ["harp"]
CMD ["--version"]
