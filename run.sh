#!/bin/bash
set -e
# Применяем миграции (если бы использовали alembic, но здесь создаём таблицы через lifespan)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info