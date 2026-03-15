# ============================================================================
# Rust Engine - Dockerfile for Zero-Bottleneck Gateway
# ============================================================================

# Build stage
FROM rust:1.75-slim-bookworm as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Create dummy main.rs to cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy actual source
COPY src ./src

# Build for release with maximum optimizations
RUN cargo build --release

# Runtime stage - minimal image
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /app/target/release/cenayang-gateway /app/cenayang-gateway

# Create non-root user
RUN useradd -r -s /bin/false cenayang && \
    chown -R cenayang:cenayang /app

USER cenayang

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with optimizations
ENV RUST_LOG=info
ENV RUST_BACKTRACE=1

CMD ["./cenayang-gateway"]
