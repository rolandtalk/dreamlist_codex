# 300 Best SCTR Picks Dreamlist by CODEX

FastAPI + Celery + Redis app that:
- Scrapes top 300 SCTR picks (symbol + rank + optional SCTR score)
- Calculates 1D/5D/20D/60D + RSI(14) with yfinance
- Stores run history in SQLite
- Schedules daily run at 06:00 Asia/Taipei
- Supports manual update from UI/API
- Exports latest results to Google Sheets
- Retries failed jobs and sends Slack/Email notifications

## Architecture

- `web` (FastAPI): UI, APIs, daily scheduler
- `worker` (Celery): background tasks (scrape + calculate + export)
- `redis`: broker + result backend

## Local Setup (Python)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Required in `.env`:
- `GOOGLE_SHEET_ID`
- `GOOGLE_CREDENTIALS_JSON` (path to service-account json)

## Local Run (Docker Compose, recommended)

```bash
docker compose up --build
```

Then open: `http://127.0.0.1:8000`

## Local Run (without Docker)

Terminal 1 (Redis):
```bash
redis-server
```

Terminal 2 (Web API):
```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 3 (Worker):
```bash
source .venv/bin/activate
celery -A app.celery_app:celery_app worker --loglevel=INFO
```

## APIs

- `GET /api/picks/latest?q=&page=1&page_size=50`
- `GET /api/runs/latest?limit=10`
- `POST /api/jobs/run` -> returns `task_id`
- `POST /api/jobs/export-latest` -> returns `task_id`
- `GET /api/jobs/status/{task_id}`

## Scheduler (06:00 Taiwan time)

Configured by:
- `APP_TIMEZONE=Asia/Taipei`
- `SCHEDULE_HOUR=6`
- `SCHEDULE_MINUTE=0`

The scheduler runs inside the web process and enqueues Celery tasks.

## Retry + Notifications

- Celery retry config: `TASK_MAX_RETRIES` (default 3)
- Slack: set `SLACK_WEBHOOK_URL`
- Email: set `NOTIFY_EMAIL_ENABLED=true` and SMTP envs

## Google Sheets Export

1. Create Google Cloud service account key JSON.
2. Put key file in project, e.g. `./service-account.json`.
3. Set `.env`:
   - `GOOGLE_CREDENTIALS_JSON=./service-account.json`
   - `GOOGLE_SHEET_ID=<your spreadsheet id>`
4. Share the target sheet with service account email.

Optional:
- `AUTO_EXPORT_ON_SUCCESS=true` to export automatically after every successful scrape.

## Deploy

### Railway

1. Push this repo to GitHub.
2. Create Railway project from GitHub repo.
3. Add 2 services from same repo:
   - Web service command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Worker service command: `celery -A app.celery_app:celery_app worker --loglevel=INFO`
4. Add Redis plugin/service.
5. Set env vars for both services:
   - `APP_TIMEZONE=Asia/Taipei`
   - `SCHEDULE_HOUR=6`
   - `SCHEDULE_MINUTE=0`
   - `CELERY_BROKER_URL=<redis url>`
   - `CELERY_RESULT_BACKEND=<redis url>`
   - plus Google + notification variables

### Render

- `render.yaml` is included.
- Create Blueprint from repo and set missing env vars.

### GCP (Cloud Run)

Use two Cloud Run services + one Memorystore Redis:
1. Service A: web (`uvicorn ...`)
2. Service B: worker (`celery ...`)
3. Redis: Memorystore Standard
4. Set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` to Redis endpoint
5. Store Google service account JSON in Secret Manager and mount to container

## Notes

- StockCharts HTML can change. If parser breaks, update `app/services/sctr.py`.
- For high scale, replace SQLite with Postgres.
