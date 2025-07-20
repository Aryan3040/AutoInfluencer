#!/bin/bash
# Startup script for YouTube Influencer Analysis System

echo "🚀 Starting YouTube Influencer Analysis System"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "whisper_api_server.py" ]; then
    echo "❌ Please run this script from the channelscrape directory"
    exit 1
fi

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

echo ""
echo "Available options:"
echo "1. Start Whisper API Server only"
echo "2. Start Streamlit App (Manual Analysis)"
echo "3. Start Micro Influencer Finder"
echo "4. Start All Services"
echo "5. Test System"
echo ""

read -p "Choose option (1-5): " choice

case $choice in
    1)
        echo "🎤 Starting Whisper API Server..."
        python3 whisper_api_server.py
        ;;
    2)
        echo "🌐 Starting Streamlit App..."
        echo "💡 Make sure Whisper API server is running in another terminal!"
        streamlit run app.py
        ;;
    3)
        echo "🔍 Starting Micro Influencer Finder..."
        echo "💡 Make sure Whisper API server is running in another terminal!"
        python3 micro_influencer_finder.py
        ;;
    4)
        echo "🚀 Starting all services..."
        echo "🎤 Starting Whisper API Server in background..."
        python3 whisper_api_server.py &
        WHISPER_PID=$!
        
        sleep 5
        echo "📊 Testing API server..."
        if curl -s http://127.0.0.1:5555/health > /dev/null; then
            echo "✅ Whisper API server is ready!"
            echo ""
            echo "🌐 Open these URLs:"
            echo "   Streamlit App: http://localhost:8501"
            echo "   Whisper API: http://127.0.0.1:5555/health"
            echo ""
            echo "🔍 Starting Streamlit in foreground..."
            echo "💡 Run 'python3 micro_influencer_finder.py' in another terminal for auto discovery"
            streamlit run app.py
        else
            echo "❌ Whisper API server failed to start"
            kill $WHISPER_PID 2>/dev/null
            exit 1
        fi
        ;;
    5)
        echo "🧪 Running system tests..."
        python3 test_whisper_api.py
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac 