"""GWS Agent entry point."""

from __future__ import annotations

import sys

from loguru import logger

from duq_agent_core import AgentConfig


def configure_logging(level: str = "INFO") -> None:
    """Configure loguru logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )


def main() -> None:
    """Run gws-agent."""
    from gws_agent.agent import GWSAgent

    # Load configuration from environment
    config = AgentConfig.from_env(prefix="GWS_AGENT_")

    # Configure logging
    configure_logging(config.log_level)

    logger.info("Starting GWS Agent")
    logger.info(f"Port: {config.port}")
    logger.info(f"Redis URL: {config.redis_url}")

    # Create and run agent
    agent = GWSAgent(config=config)
    agent.run()


if __name__ == "__main__":
    main()
