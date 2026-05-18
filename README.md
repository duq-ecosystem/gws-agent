# GWS Agent

Google Workspace specialist agent for Duq ecosystem.

## Features

- **Gmail**: Read unread, send, mark as read
- **Calendar**: List, create, update, delete events
- **Drive**: List and search files
- **Tasks**: List, create, complete, delete tasks

## Architecture

Uses A2A protocol for communication with orchestrator (Duq).
Credentials fetched from shared PostgreSQL database.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GWS_AGENT_PORT` | HTTP port (default: 9007) |
| `GWS_AGENT_REDIS_URL` | Redis URL for A2A |
| `DATABASE_URL` | PostgreSQL for credentials |
| `ENCRYPTION_KEY` | Fernet key for token decryption |

## Usage

```
delegate(agent_name="gws-agent", task="Покажи непрочитанные письма")
delegate(agent_name="gws-agent", task="Создай событие завтра в 10:00")
```

## Development

```bash
pip install -e .
python -m gws_agent.main
```
