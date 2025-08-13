#! /usr/bin/env sh
set -e

echo "Starting Amarillo enhancer/syncer/gtfs(rt) generation as background process"
python enhancer.py &
# Start Gunicorn
echo "Starting uvicorn with $MAX_WORKERS workers"
exec uvicorn amarillo.main:app --host 0.0.0.0 --port 8000 --workers "$MAX_WORKERS"

 