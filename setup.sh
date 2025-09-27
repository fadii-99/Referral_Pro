#!/bin/bash

echo "🚀 Setting up Referral_Pro Backend for the first time..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️ No requirements.txt found, skipping dependency installation..."
fi

# Run migrations
echo "🗂 Running migrations..."
python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Setup completed! You can now run ./start.sh"
