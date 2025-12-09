#!/bin/bash
# Startup script to run both webhook API and Web UI

# Get ports from environment or use defaults
WEBHOOK_PORT=${SERVER_PORT:-9090}
WEBUI_PORT=${WEB_UI_PORT:-9091}

# Start the webhook API in the background
gunicorn --bind 0.0.0.0:${WEBHOOK_PORT} --workers 2 --timeout 60 --access-logfile - app.main:app &

# Check if Web UI is enabled
if [ "${WEB_UI_ENABLED:-true}" = "true" ]; then
    # Start the Web UI in the foreground
    gunicorn --bind 0.0.0.0:${WEBUI_PORT} --workers 1 --timeout 60 --access-logfile - app.webui_app:app
else
    # If Web UI is disabled, keep the main process running
    wait
fi
