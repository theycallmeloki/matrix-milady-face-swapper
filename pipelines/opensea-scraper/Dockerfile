# Base image
FROM ubuntu:20.04

# Update Ubuntu Software repository
RUN apt-get update && apt-get upgrade -y

# Install necessary packages
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y \
    wget \
    xvfb \
    gnupg \
    --no-install-recommends

# Add Google Chrome to the repository sources
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set display port and disable access control
ENV DISPLAY=:99
ENV XEPHYR_OPTS="-ac -screen 0 1920x1080x24+32 -nolisten tcp"

# Add a startup script
RUN echo '#!/bin/bash' > /usr/bin/startup.sh \
    && echo 'Xvfb :99 -ac -screen 0 1920x1080x24+32 -nolisten tcp &' >> /usr/bin/startup.sh \
    && echo 'google-chrome-stable' >> /usr/bin/startup.sh \
    && chmod +x /usr/bin/startup.sh

# Start script
ENTRYPOINT ["/usr/bin/startup.sh"]
