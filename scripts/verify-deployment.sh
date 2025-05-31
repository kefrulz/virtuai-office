#!/bin/bash

echo "🔍 VirtuAI Office Deployment Verification"
echo "========================================"

# Check Ollama
echo -n "Ollama service: "
if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Backend
echo -n "Backend API: "
if curl -s http://localhost:8000/api/status >/dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Frontend
echo -n "Frontend: "
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Models
echo -n "AI Models: "
if ollama list >/dev/null 2>&1; then
    MODEL_COUNT=$(ollama list | grep -c llama)
    echo "✅ $MODEL_COUNT models installed"
else
    echo "❌ No models found"
fi

echo ""
echo "🌐 Access URLs:"
echo "   Dashboard: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
