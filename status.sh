#!/bin/bash

echo "📊 VirtuAI Office Status"
echo "======================="

echo -n "Ollama:   "
if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "🟢 Running"
else
    echo "🔴 Stopped"
fi

echo -n "Backend:  "
if curl -s http://localhost:8000/api/status >/dev/null 2>&1; then
    echo "🟢 Running"
else
    echo "🔴 Stopped"
fi

echo -n "Frontend: "
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "🟢 Running"
else
    echo "🔴 Stopped"
fi

echo ""
if command -v ollama >/dev/null 2>&1; then
    echo "AI Models:"
    ollama list 2>/dev/null || echo "No models found"
fi
