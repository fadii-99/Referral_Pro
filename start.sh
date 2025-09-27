#!/bin/bash

echo "🌟 Starting Referral_Pro Django ASGI server..."

# Activate virtual environment
source .venv/bin/activate

# Start Django server via Uvicorn
exec uvicorn referralpro.asgi:application --reload --host 0.0.0.0 --port 8000
