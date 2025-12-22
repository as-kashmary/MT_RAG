# Stage 1: Builder - install dependencies and gather required runtime libs
FROM python:3.13.1-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies into a separate folder to copy into the runtime image
RUN pip install --no-cache-dir --target /python_deps -r requirements.txt

# Copy application source
COPY . .

# Collect shared libraries needed at runtime (e.g., for mysqlclient)
RUN mkdir -p /runtime_libs && \
    cp -v /usr/lib/x86_64-linux-gnu/libmysqlclient.so* /runtime_libs/ || true && \
    cp -v /usr/lib/x86_64-linux-gnu/libssl.so* /runtime_libs/ || true && \
    cp -v /usr/lib/x86_64-linux-gnu/libcrypto.so* /runtime_libs/ || true && \
    cp -v /usr/lib/x86_64-linux-gnu/libz.so* /runtime_libs/ || true


# Stage 2: Runtime - use a minimal distroless Python 3 image
FROM gcr.io/distroless/python3-debian12 AS runtime

WORKDIR /app

# Copy Python dependencies and application code
COPY --from=builder /python_deps /python_deps
COPY --from=builder /app /app

# Copy required shared libraries for mysqlclient
COPY --from=builder /runtime_libs/ /usr/lib/x86_64-linux-gnu/

# Ensure Python can find the installed dependencies
ENV PYTHONPATH=/python_deps

EXPOSE 8000

# Distroless python3 image has python3 as entrypoint; pass module to run
ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "src.admin_server"]