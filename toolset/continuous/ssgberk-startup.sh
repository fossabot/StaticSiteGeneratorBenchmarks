#!/bin/bash

set -e

while true
do
  cd $SSGBERK_REPORTPARENT
  ./ssgberk-shutdown.sh

  if [ -d "$SSGBERK_REPOPARENT/$SSGBERK_REPONAME" ]; then
    sudo rm -rf $SSGBERK_REPOPARENT/$SSGBERK_REPONAME
  fi

  git clone \
    -b $SSGBERK_REPOBRANCH \
    $SSGBERK_REPOURI \
    $SSGBERK_REPOPARENT/$SSGBERK_REPONAME \
    --depth 1

  cd $SSGBERK_REPOPARENT/$SSGBERK_REPONAME

  docker run \
    --network=host \
    --mount type=bind,source=$SSGBERK_REPOPARENT/$SSGBERK_REPONAME,target=/StaticSiteGeneratorBenchmarks \
    matheusrv/ssgberk \
    --server-host $SSGBERK_SERVER_HOST \
    --client-host $SSGBERK_CLIENT_HOST \
    --network-mode host \
    --results-name "$SSGBERK_RUN_NAME" \
    --results-environment "$SSGBERK_ENVIRONMENT" \
    --results-upload-uri "$SSGBERK_UPLOAD_URI" \
    --quiet

  zip -r results.zip results

  curl \
    -i -v \
    -X POST \
    --header "Content-Type: application/zip" \
    --data-binary @results.zip \
    $SSGBERK_UPLOAD_URI

  sleep 5
done
