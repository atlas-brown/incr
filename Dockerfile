FROM debian:latest

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3-dev \
    python3-pip \
    python3-venv \
    wget \
    curl

COPY . /app
WORKDIR /app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install --no-cache-dir -r requirements.txt
RUN chmod +x setup.sh && ./setup.sh

CMD ["/bin/bash"]
