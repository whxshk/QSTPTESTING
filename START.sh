#!/bin/bash
set -e

echo "🚀 Starting Fintech Regulatory Compliance Platform..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 .env file not found. Creating it now..."
    echo ""
    echo "⚠️  IMPORTANT: You need an Anthropic API key to use this application."
    echo "   Get your key from: https://console.anthropic.com/settings/keys"
    echo ""
    read -p "Enter your Anthropic API key (or press Enter to skip): " api_key

    if [ -z "$api_key" ]; then
        echo "⚠️  No API key provided. Creating .env with placeholder..."
        echo "   You'll need to edit .env manually before the app will work."
        api_key="your-api-key-here"
    fi

    cat > .env << EOF
ANTHROPIC_API_KEY=$api_key
PORT=5000
FLASK_DEBUG=False
VITE_API_URL=/api
EOF
    echo "✅ .env file created"
fi

echo ""
echo "🛑 Stopping any existing containers..."
docker-compose down 2>/dev/null || true

echo ""
echo "🔨 Building and starting services..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "🔍 Checking service health..."
backend_status=$(docker-compose ps | grep backend | grep -c "Up" || echo "0")
frontend_status=$(docker-compose ps | grep frontend | grep -c "Up" || echo "0")

if [ "$backend_status" -eq "1" ] && [ "$frontend_status" -eq "1" ]; then
    echo "✅ All services are running!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:5000"
    echo "   Health:   http://localhost:5000/health"
    echo ""
    echo "📝 To view logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🎉 Ready to use! Open http://localhost:3000 in your browser"
else
    echo "⚠️  Some services failed to start. Checking logs..."
    echo ""
    docker-compose logs --tail=50
fi
