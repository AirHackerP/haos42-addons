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

# Clone rpi-ws281x-python with submodules (includes latest native library)
# Force fresh clone to ensure latest code with Pi 4 Rev 1.4 support
RUN cd /tmp && \
    git clone --depth 1 --recurse-submodules https://github.com/rpi-ws281x/rpi-ws281x-python.git && \
    cd rpi-ws281x-python && \
    git submodule update --init --recursive && \
    pip3 install --no-cache-dir --no-binary :all: .

# Install other dependencies
RUN pip3 install --no-cache-dir requests

# Copy application files
COPY src/ /app/
COPY run.sh /

RUN chmod a+x /run.sh

WORKDIR /app

CMD [ "/run.sh" ]
