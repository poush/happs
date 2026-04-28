ARG BUILD_FROM
ARG UPSTREAM_REPO=https://github.com/lharries/whatsapp-mcp.git
ARG UPSTREAM_REF=main

# ---------------------------------------------------------------------------
# Stage 1: Build the Go bridge
# ---------------------------------------------------------------------------
FROM golang:1.24-alpine AS go-builder

ARG UPSTREAM_REPO
ARG UPSTREAM_REF

# CGO is required for go-sqlite3
RUN apk add --no-cache git gcc musl-dev sqlite-dev

WORKDIR /build
RUN git clone --depth 1 --branch "${UPSTREAM_REF}" "${UPSTREAM_REPO}" .

WORKDIR /build/whatsapp-bridge
# Force-update whatsmeow to latest before building.
# WhatsApp periodically requires a newer client version; the upstream go.sum
# may lag behind, causing "Client outdated (405)" connection failures.
RUN go get go.mau.fi/whatsmeow@latest && go mod tidy
RUN CGO_ENABLED=1 GOOS=linux go build -o /usr/local/bin/whatsapp-bridge .

# ---------------------------------------------------------------------------
# Stage 2: Runtime image (hassio-addons base = Alpine + S6-overlay + bashio)
# ---------------------------------------------------------------------------
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg \
    sqlite-libs \
    curl

# Install uv (fast Python package manager / venv runner)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy compiled Go binary
COPY --from=go-builder /usr/local/bin/whatsapp-bridge /usr/local/bin/whatsapp-bridge

# Copy Python server source
COPY --from=go-builder /build/whatsapp-mcp-server /opt/whatsapp-mcp-server

# Pre-install Python deps into the project's virtual environment
WORKDIR /opt/whatsapp-mcp-server
RUN uv sync --no-dev

# whatsapp.py resolves the DB path as:
#   dirname(__file__)/../whatsapp-bridge/store/messages.db
#   = /opt/whatsapp-mcp-server/../whatsapp-bridge/store/messages.db
#   = /opt/whatsapp-bridge/store/messages.db
#
# The Go bridge writes to ./store/ relative to its CWD (/data).
# So we symlink /opt/whatsapp-bridge/store -> /data/store.
# The symlink target (/data/store) is created at runtime by the run script.
RUN mkdir -p /opt/whatsapp-bridge && \
    ln -sf /data/store /opt/whatsapp-bridge/store

# Copy S6 service definitions and helper scripts
COPY rootfs /

RUN find /etc/s6-overlay -name "run" -o -name "finish" | xargs chmod a+x

WORKDIR /data
