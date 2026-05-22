# GWS Agent Dockerfile
# Google Workspace: Gmail, Calendar, Drive, Tasks
# Optimized: deps layer cached, source layer separate

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# ============================================================
# DEPS LAYER (cached unless pyproject.toml changes)
# ============================================================

# duq-agent-core: copy pyproject.toml, create stub, install deps
COPY duq-agent-core/pyproject.toml duq-agent-core/README.md /duq-agent-core/
RUN mkdir -p /duq-agent-core/src/duq_agent_core && \
    touch /duq-agent-core/src/duq_agent_core/__init__.py
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e /duq-agent-core

# gws-agent: copy pyproject.toml, create stub, install deps
COPY gws-agent/pyproject.toml gws-agent/README.md ./
RUN mkdir -p /app/src/gws_agent && \
    touch /app/src/gws_agent/__init__.py
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-sources -e ".[dev]"

# ============================================================
# SOURCE LAYER (rebuilt on code changes only)
# ============================================================

# Copy real source (overwrites stubs, editable install picks up changes)
COPY duq-agent-core/src/ /duq-agent-core/src/
COPY gws-agent/src/ ./src/

# Set environment
ENV PYTHONUNBUFFERED=1
ENV GWS_AGENT_PORT=9007

# Expose port
EXPOSE 9007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:9007/.well-known/agent-card.json || exit 1

CMD ["python", "-m", "gws_agent.main"]
