#!/bin/bash
# Stop Mock KNCB Server

echo "🛑 Stopping Mock KNCB Server..."

if pgrep -f "mock_kncb_server.py" > /dev/null; then
    pkill -f "mock_kncb_server.py"
    echo "✅ Mock server stopped"
else
    echo "⚠️  Mock server is not running"
fi
