FROM debian:latest

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3-dev \
    python3-pip \
    wget \
    curl

COPY . /app
WORKDIR /app
RUN chmod +x setup.sh && ./setup.sh

CMD ["/bin/bash"]
