#!/usr/bin/env bash
set -e

source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081