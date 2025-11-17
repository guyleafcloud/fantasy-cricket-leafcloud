#!/bin/bash
# Start Mock KNCB Server
# Runs on port 5001 inside the container

echo "🚀 Starting Mock KNCB Server..."

# Check if already running
if pgrep -f "mock_kncb_server.py" > /dev/null; then
    echo "⚠️  Mock server is already running"
    exit 0
fi

# Start server in background
nohup python3 /app/mock_kncb_server.py > /var/log/mock_kncb_server.log 2>&1 &

echo "✅ Mock server started on port 5001"
echo "📋 Logs: /var/log/mock_kncb_server.log"
echo "🔍 Check status: curl http://localhost:5001/health"
