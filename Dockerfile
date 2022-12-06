FROM ubuntu:20.04

SHELL ["/bin/bash", "-c"]

ARG WORK_DIR=/repo
WORKDIR ${WORK_DIR}

# Create local bin dir and add to PATH.
ARG LOCAL_BIN=${WORK_DIR}/bin
ENV PATH=${LOCAL_BIN}:${PATH}
RUN mkdir -p ${LOCAL_BIN}

# Install pre-requisites.
#   - libarchive-dev appears to be needed for mamba.
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
        apt-transport-https \
        ca-certificates \
        coreutils \
        curl \
        wget \
        grep \
        tar \
        sed \
        direnv \
        jq \
        libarchive-dev \
        parallel \
    && apt-get autoremove -y

# Install Azure CLI.
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install AzCopy.
COPY .setup/ .setup/
RUN bash .setup/azcopy.sh -p ${LOCAL_BIN}

# Install python environment.
COPY conda-lock.yml poetry.lock poetry.toml pyproject.toml setup-shell install-env ./
# Run the following setup tasks:
#   - add an empty .git dir to satisfy the check that we're running from the repo root.
#   - install base conda environment and project specific conda environment with all conda-managed dependencies.
#   - source setup-shell script to install poetry-managed dependencies.
#   - configure .bashrc to source setup-shell when bash is run interactively.
RUN mkdir .git \
    && bash ./install-env \
    && source ./setup-shell \
    && echo "source ${WORK_DIR}/setup-shell" >> ${HOME}/.bashrc

# Copy source code.
COPY lib/ lib/
COPY scripts/ scripts/