ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install minimal runtime dependencies (no build tools needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install stable release from PyPI (prebuilt wheel - no compilation)
# v4.3.3 released March 2024 - mature, stable, full Pi 4 support
RUN pip3 install --no-cache-dir rpi_ws281x==4.3.3 requests

# Copy application files
WORKDIR /app
COPY src/ /app/
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
