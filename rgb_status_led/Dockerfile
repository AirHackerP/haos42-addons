ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies for building rpi_ws281x from source
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
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy patch file first
COPY force_pi4.patch /tmp/

# Clone rpi-ws281x-python with submodules (includes latest native library)
# Cache bust: 2026-01-22-2230
RUN git clone --depth 1 --recurse-submodules https://github.com/rpi-ws281x/rpi-ws281x-python.git /tmp/rpi-ws281x-python

# Build and install from source (setup.py is in library/ subdirectory)
WORKDIR /tmp/rpi-ws281x-python/library
RUN git submodule update --init --recursive

# Apply patch to force Pi 4 hardware detection (bypasses /proc/device-tree access in Docker)
RUN cd lib && patch -p1 < /tmp/force_pi4.patch && cd ..

RUN pip3 install --no-cache-dir --no-binary :all: .

# Install other dependencies
RUN pip3 install --no-cache-dir requests

# Copy application files
WORKDIR /app
COPY src/ /app/
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
