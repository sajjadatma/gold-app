# Delivery

## Repositories

| Remote | URL | Purpose |
| --- | --- | --- |
| `origin` | https://github.com/sajjadatma/gold-app.git | Delivery repository |
| `upstream` | https://github.com/fastapi/full-stack-fastapi-template.git | Base template |

Delivery branch: `main`.

## Local baseline

- Python: 3.14 (`.python-version`, managed by `uv`)
- Node: 22, package manager: `bun`
- PostgreSQL: Docker Compose service `db`, exposed on host port `5433`
- Mailpit: http://localhost:8025
- Backend (dev): http://localhost:8000
- Frontend (dev): http://localhost:5173

Host port `5432` is intentionally avoided because a pre-existing local PostgreSQL
installation uses it on some development machines.

## Baseline commands

```bash
docker compose up -d --wait db mailpit
cd backend && uv run bash scripts/prestart.sh
cd backend && uv run pytest
cd frontend && bun install && bun run build
```
