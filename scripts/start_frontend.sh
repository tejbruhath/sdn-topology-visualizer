#!/bin/bash
# Open Frontend in Browser

echo "=========================================="
echo "Opening SDN Visualizer Frontend"
echo "=========================================="

# Check if backend is running
if ! pgrep -f "python.*app.py" > /dev/null; then
    echo "⚠️  WARNING: Backend is not running!"
    echo "   Please start backend first: ./scripts/start_backend.sh"
    exit 1
fi

# Test if backend is responding
if curl -s -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ Backend is responding"
else
    echo "⚠️  WARNING: Backend is not responding on http://localhost:5000"
    exit 1
fi

echo ""
echo "Opening browser to: http://localhost:5000"
echo ""

# Detect and open browser
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5000
elif command -v gnome-open > /dev/null; then
    gnome-open http://localhost:5000
elif command -v firefox > /dev/null; then
    firefox http://localhost:5000 &
elif command -v chromium-browser > /dev/null; then
    chromium-browser http://localhost:5000 &
else
    echo "Could not detect browser. Please open manually:"
    echo "  http://localhost:5000"
fi

echo ""
echo "If browser didn't open automatically, navigate to:"
echo "  http://localhost:5000"
echo ""
