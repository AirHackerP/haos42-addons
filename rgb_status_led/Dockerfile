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

# Clone and build rpi_ws281x native library from source
RUN cd /tmp && \
    git clone https://github.com/jgarff/rpi_ws281x.git && \
    cd rpi_ws281x && \
    scons && \
    mkdir build && \
    cd build && \
    cmake -D BUILD_SHARED=ON -D BUILD_TEST=ON .. && \
    make && \
    make install && \
    ldconfig

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python bindings (uses the native library we just built)
RUN pip3 install --no-cache-dir \
    rpi_ws281x \
    requests

# Copy application files
COPY src/ /app/
COPY run.sh /

RUN chmod a+x /run.sh

WORKDIR /app

CMD [ "/run.sh" ]
