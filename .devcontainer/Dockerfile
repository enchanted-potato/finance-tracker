FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl git unzip wget gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install just (command runner)
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install terraform
ARG TERRAFORM_VERSION=1.10.5
RUN wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

WORKDIR /app

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"
