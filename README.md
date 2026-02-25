# 300 Best SCTR Picks Dreamlist by CODEX

FastAPI + Celery + Redis app that:
- Scrapes top 300 SCTR picks (symbol + rank + optional SCTR score)
- Calculates 1D/5D/20D/60D + RSI(14) with yfinance
- Stores run history in SQLite
- Schedules daily run at 06:00 Asia/Taipei
- Supports manual update from UI/API
- Exports latest results to CSV
- Retries failed jobs and sends Slack/Email notifications

## Architecture

- `web` (FastAPI): UI, APIs, daily scheduler
- `worker` (Celery): background scrape/calc task
- `redis`: broker + result backend

## APIs

- `GET /api/picks/latest?q=&page=1&page_size=50`
- `GET /api/runs/latest?limit=10`
- `POST /api/jobs/run` -> returns `task_id`
- `GET /api/jobs/status/{task_id}`
- `GET /api/export/latest.csv` -> download latest CSV

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

## Railway Start Commands

- web: `python run_web.py`
- worker: `celery -A app.celery_app:celery_app worker --loglevel=INFO`

## Notes

- StockCharts HTML can change. If parser breaks, update `app/services/sctr.py`.
- For high scale, replace SQLite with Postgres.
