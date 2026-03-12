FROM python:3.10.8-slim-bullseye

RUN apt-get update -y && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# for Netskope
COPY ./netskope_root.crt /usr/local/share/ca-certificates
RUN update-ca-certificates
ENV PIP_CERT=/usr/local/share/ca-certificates/netskope_root.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.8.0 python3 -
ENV PATH=$PATH:/root/.local/bin

WORKDIR /app
COPY . /app
RUN poetry config virtualenvs.create false && poetry install
RUN poetry add "markitdown[xlsx,docx]"

