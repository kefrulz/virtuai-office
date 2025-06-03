#!/bin/bash

echo "🛑 Stopping VirtuAI Office..."

pkill -f "python backend.py" 2>/dev/null
pkill -f "npm start" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo "✅ VirtuAI Office stopped"
