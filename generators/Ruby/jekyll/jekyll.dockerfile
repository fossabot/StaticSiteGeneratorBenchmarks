FROM jekyll/jekyll:stable

COPY --chown=jekyll src ./src

WORKDIR /src
