ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies for rpi_ws281x
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers \
    make \
    git

# Create virtual environment and install Python packages
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install rpi_ws281x from source for better compatibility
RUN pip3 install --no-cache-dir \
    rpi_ws281x \
    requests

# Copy application files
COPY src/ /app/
COPY run.sh /

RUN chmod a+x /run.sh

WORKDIR /app

CMD [ "/run.sh" ]
