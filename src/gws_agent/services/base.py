"""Base class for Google Workspace services.

Provides shared functionality for credential management and gws CLI execution.
Single Responsibility: Credential handling and CLI execution.
"""
import asyncio
import json
import os
import tempfile
from typing import Any

from loguru import logger


class GWSError(Exception):
    """Error from Google Workspace CLI.

    Raised when gws CLI returns an error (missing binary, auth failure, API error).
    This prevents silent failures from being masked as "no data".
    """

    pass


class GWSBaseService:
    """Base class with shared GWS functionality.

    Handles:
    - Credential file creation (secure temp files)
    - gws CLI command execution
    - Error handling and cleanup
    """

    def _get_credentials_file(self, credentials: dict | None) -> str | None:
        """Create temp credentials file in Google authorized_user format.

        Args:
            credentials: Dict with access_token, refresh_token, token_type

        Returns:
            Path to temp credentials file, or None if no credentials
        """
        if not credentials:
            logger.warning("No credentials provided")
            return None

        if not credentials.get("refresh_token"):
            logger.warning("No refresh_token in credentials")
            return None

        # Check required env vars
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            logger.error("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set")
            return None

        # Google authorized_user format
        gws_creds = {
            "type": "authorized_user",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": credentials.get("refresh_token"),
        }

        # Write to temp file with secure permissions
        fd, path = tempfile.mkstemp(suffix=".json", prefix="gws_creds_")
        try:
            # Set secure permissions BEFORE writing (owner read/write only)
            os.chmod(path, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump(gws_creds, f)
            logger.debug(f"Created secure credentials file: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to write credentials file: {e}")
            try:
                os.unlink(path)
            except Exception as e:  # noqa: Silenced
                pass
            return None

    async def _run_gws(self, credentials: dict | None, *args: str, timeout: float = 30.0) -> dict[str, Any]:
        """Run gws CLI command and return JSON result.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            *args: Command arguments (e.g., "gmail", "users", "messages", "list")
            timeout: Command timeout in seconds

        Returns:
            Parsed JSON response or error dict
        """
        cmd = ["gws", *args]
        logger.debug(f"Running gws command: {' '.join(cmd)}")

        # Get credentials file
        creds_file = self._get_credentials_file(credentials)
        if not creds_file:
            logger.warning("No GWS credentials available for user")
            return {"error": "Google аккаунт не подключён. Скажи 'подключи гугл' для авторизации."}

        # Use GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE env var
        env = os.environ.copy()
        env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = creds_file
        env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] = "file"  # Disable keyring, use file
        logger.debug(f"Using per-user credentials file: {creds_file}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode == 0:
                try:
                    return json.loads(stdout.decode())
                except json.JSONDecodeError:
                    # Some commands return plain text
                    return {"output": stdout.decode().strip()}
            else:
                error_msg = stderr.decode() or stdout.decode()
                logger.error(f"gws command failed: {error_msg[:200]}")
                return {"error": error_msg}

        except asyncio.TimeoutError:
            logger.error(f"gws command timeout: {' '.join(cmd)}")
            return {"error": "Command timeout"}
        except FileNotFoundError:
            logger.error("gws CLI not found in PATH")
            return {"error": "gws CLI not found"}
        except Exception as e:
            logger.error(f"gws command failed: {str(e)}")
            return {"error": str(e)}
        finally:
            # Clean up temp credentials file
            if creds_file and os.path.exists(creds_file):
                try:
                    os.unlink(creds_file)
                    logger.debug(f"Cleaned up credentials file: {creds_file}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup credentials file: {e}")
