FROM mcr.microsoft.com/playwright:v1.40.0-focal

# Create a non-root user
RUN useradd -ms /bin/bash sandboxer
USER sandboxer
WORKDIR /home/sandboxer

# Install extra tools if needed
RUN sudo apt-get update && sudo apt-get install -y curl jq && \
    sudo rm -rf /var/lib/apt/lists/*

COPY browse.js .