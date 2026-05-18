"""Credentials service for GWS Agent.

Fetches user OAuth credentials from shared database.
"""

import os

import asyncpg
from cryptography.fernet import Fernet
from loguru import logger


# Connection pool (singleton)
_pool: asyncpg.Pool | None = None


def _get_fernet() -> Fernet | None:
    """Get Fernet cipher for token decryption."""
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        return None
    return Fernet(key.encode())


def decrypt_token(encrypted: str | None) -> str | None:
    """Decrypt token if encrypted, return as-is if plain text."""
    if not encrypted:
        return None

    fernet = _get_fernet()
    if not fernet:
        # No encryption key - assume plain text (legacy)
        return encrypted

    try:
        return fernet.decrypt(encrypted.encode()).decode()
    except Exception:
        # Not encrypted or invalid - return as-is
        return encrypted


async def _get_pool() -> asyncpg.Pool:
    """Get or create connection pool."""
    global _pool

    if _pool is None:
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            raise RuntimeError("DATABASE_URL not set")

        # Convert SQLAlchemy URL format if needed
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

        logger.info("[credentials] Creating connection pool")
        _pool = await asyncpg.create_pool(
            db_url,
            min_size=1,
            max_size=3,
            command_timeout=30,
        )

    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("[credentials] Connection pool closed")


async def get_user_gws_credentials(user_id: int | str) -> dict | None:
    """Get Google Workspace credentials for user.

    Args:
        user_id: User ID (telegram_id or db user_id)

    Returns:
        dict with access_token, refresh_token, token_type or None
    """
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid user_id: {user_id}")
        return None

    logger.debug(f"[credentials] Getting GWS credentials for user {user_id}")

    try:
        pool = await _get_pool()
    except Exception as e:
        logger.error(f"[credentials] Failed to get connection pool: {e}")
        return None

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT access_token, refresh_token, token_type, expires_at
                FROM user_credentials
                WHERE user_id = $1 AND provider = 'google'
                """,
                user_id_int
            )

            if not row:
                logger.debug(f"[credentials] No credentials found for user {user_id}")
                return None

            access_token = decrypt_token(row["access_token"])
            refresh_token = decrypt_token(row["refresh_token"])
            token_type = row["token_type"] or "Bearer"

            if not refresh_token or not access_token:
                logger.warning(f"[credentials] Missing tokens for user {user_id}")
                return None

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": token_type,
            }

    except Exception as e:
        logger.error(f"[credentials] Query failed: {e}")
        return None
