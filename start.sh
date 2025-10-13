# #!/bin/bash

# echo "🌟 Starting Referral_Pro Django ASGI server..."

# # Activate virtual environment
# source .venv/bin/activate

# # Start Django server via Uvicorn
# exec uvicorn referralpro.asgi:application --reload --host 0.0.0.0 --port 8000
#!/bin/bash

echo "⚡ Starting Referral_Pro Django ASGI server with multiple workers..."

# Activate virtual environment
source .venv/bin/activate

# Number of workers (adjust based on CPU cores)
WORKERS=4
HOST=0.0.0.0
PORT=8000

# Run Gunicorn with Uvicorn workers (recommended)
exec gunicorn referralpro.asgi:application \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind $HOST:$PORT \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
