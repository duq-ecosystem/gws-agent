# GWS Agent Dockerfile
# Google Workspace: Gmail, Calendar, Drive, Tasks

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# Install duq-agent-core first (local dependency)
COPY duq-agent-core/pyproject.toml duq-agent-core/README.md /duq-agent-core/
COPY duq-agent-core/src/ /duq-agent-core/src/
RUN uv pip install --system /duq-agent-core

# Copy gws-agent files
COPY gws-agent/pyproject.toml gws-agent/README.md ./
COPY gws-agent/src/ ./src/

# Install gws-agent
RUN uv pip install --system .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV GWS_AGENT_PORT=9007

# Expose port
EXPOSE 9007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:9007/.well-known/agent-card.json || exit 1

CMD ["python", "-m", "gws_agent.main"]
