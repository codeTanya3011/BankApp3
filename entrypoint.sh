#!/bin/bash

set -e

echo "--- Waiting for database to be ready... ---"

echo "--- Running Alembic Migrations ---"

alembic upgrade head

echo "--- Launching the Uvicorn app ---"

exec uvicorn app_credits.base:app --host 0.0.0.0 --port 8000
