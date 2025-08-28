#!/usr/bin/env bash
set -euo pipefail

# Stop rag-tech processes
echo "🛑 Stopping rag-tech..."

# Kill FastAPI server
pkill -f "uvicorn.*app.main" 2>/dev/null && echo "✅ FastAPI server stopped" || echo "ℹ️  No FastAPI server running"

# Clean up port 8000
if lsof -ti:8000 >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill 2>/dev/null
    echo "✅ Port 8000 cleaned up"
fi

echo "🏁 rag-tech stopped successfully"
