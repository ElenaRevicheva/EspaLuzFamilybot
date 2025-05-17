#!/bin/bash

echo "🔧 Cleaning webhook before polling..."
python webhook_cleaner.py
sleep 2

echo "🚀 Starting Espaluz bot..."
python main.py
