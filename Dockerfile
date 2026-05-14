FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.cargo/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    strace \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    pkg-config \
    software-properties-common \
    wget \
    curl \
    libssl-dev \
    libstdc++6 \
    libtool \
    m4 \
    automake \
    mergerfs \
    sudo \
    vim \
    unzip

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain nightly
RUN pip3 install uv

COPY . /app
WORKDIR /app

RUN uv pip install --system -r pyproject.toml
RUN cargo build --release

CMD ["/bin/bash"]