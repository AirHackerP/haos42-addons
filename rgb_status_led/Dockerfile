ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install build dependencies for compiling rpi_ws281x from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    gcc \
    g++ \
    make \
    git \
    scons \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Clone STABLE release v4.3.3 (not latest main - stable might have less strict detection)
RUN git clone --depth 1 --branch v4.3.3 --recurse-submodules \
    https://github.com/rpi-ws281x/rpi-ws281x-python.git /tmp/rpi-ws281x-python

# Build and install from stable source (NO PATCHING - try as-is first)
WORKDIR /tmp/rpi-ws281x-python
RUN pip3 install --no-cache-dir .

# Install other dependencies
RUN pip3 install --no-cache-dir requests

# Copy application files
WORKDIR /app
COPY src/ /app/
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
