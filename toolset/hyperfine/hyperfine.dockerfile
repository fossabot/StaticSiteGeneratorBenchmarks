FROM ubuntu:xenial

RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/sharkdp/hyperfine/releases/download/v1.0.0/hyperfine_1.0.0_amd64.deb
RUN dpkg -i hyperfine_1.0.0_amd64.deb

COPY build.sh build.sh

RUN chmod 777 build.sh

# Environment vars required by the wrk scripts with nonsense defaults
ENV name name
ENV port port
ENV content_url content_url
ENV file_number file_number
ENV file_size file_size
ENV header header
ENV build_command build_command
