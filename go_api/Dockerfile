# ============================================================================
# Go API - Dockerfile for Zero-Bottleneck Orchestrator
# ============================================================================

# Build stage
FROM golang:1.22-bookworm as builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Build with optimizations
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s -extldflags '-static'" \
    -o orchestrator ./cmd/orchestrator

# Runtime stage - minimal scratch image
FROM scratch

WORKDIR /app

# Copy binary
COPY --from=builder /app/orchestrator /app/orchestrator

# Copy CA certificates for HTTPS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Expose port
EXPOSE 8090

# Health check (requires curl in scratch, so we use TCP check)
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/app/orchestrator", "-health-check"]

# Run
ENTRYPOINT ["/app/orchestrator"]
