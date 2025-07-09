#!/bin/bash

# Navigate to script directory
cd "$(dirname "$0")"

# Setup venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run your bot
python telegram_bot.py
