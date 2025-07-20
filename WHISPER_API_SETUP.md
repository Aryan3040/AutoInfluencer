# Whisper API System - No More GPU Conflicts! 🎤

## 🎯 **Problem Solved**

Previously: Both scripts tried to load Whisper models → GPU memory conflicts → crashes  
**Now**: Single Whisper API server → Queue system → No conflicts → Both scripts work simultaneously! 

## 🏗️ **Architecture**

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Original App      │    │  Micro Influencer   │    │                     │
│   (Manual Analysis) │    │  Discovery          │    │   Whisper API       │
│                     │    │  (Auto Discovery)   │    │   Server            │
│  HTTP requests ────────────────────────────────────▶│                     │
│                     │    │                     │    │  • Loads model once │
│                     │    │  HTTP requests ─────────▶│  • Queue system     │
└─────────────────────┘    └─────────────────────┘    │  • CUDA management  │
                                                       │  • No conflicts     │
                                                       └─────────────────────┘
```

## 🚀 **Quick Start**

### **Step 1: Start Whisper API Server** (Terminal 1)
```bash
cd channelscrape
source venv/bin/activate
python whisper_api_server.py
```

### **Step 2: Run Your Scripts** (Terminal 2 & 3)
```bash
# Terminal 2: Manual analyzer
streamlit run app.py

# Terminal 3: Auto discovery  
python micro_influencer_finder.py
```

### **Step 3: Verify Everything Works**
```bash
python test_whisper_api.py
```

## 📡 **API Endpoints**

**Whisper API Server** (http://127.0.0.1:5555)

- **GET `/health`** - Check server status
- **POST `/transcribe`** - Queue transcription (async)
- **GET `/result/<id>`** - Get async result
- **POST `/transcribe/sync`** - Direct transcription (sync)
- **GET `/stats`** - Server statistics

## 🔧 **Features**

### **🎯 For Manual Analysis (Original App)**
- **Synchronous transcription** - Blocks until complete
- **Immediate results** - Perfect for interactive use
- **High priority** - Direct processing

### **🤖 For Auto Discovery (Micro Finder)**  
- **Asynchronous transcription** - Queued processing
- **Non-blocking** - Doesn't slow down discovery
- **Lower priority** - Background processing

### **⚡ System Benefits**
- **Single GPU usage** - Only API server uses CUDA
- **Queue management** - No race conditions
- **Memory optimization** - One model loaded
- **Error isolation** - Crashes don't affect other scripts
- **Easy monitoring** - Centralized logging

## 🛠️ **Technical Details**

### **Files Created:**
- `whisper_api_server.py` - Main API server
- `whisper_client.py` - Client library  
- `test_whisper_api.py` - Test script

### **Modified Files:**
- `youtube_analyzer.py` - Now uses API client by default
- `requirements.txt` - Added Flask

### **Backward Compatibility:**
The original `WhisperTranscriber` still works if needed:
```python
# Use API (default, recommended)
yt = YouTubeAnalyzer(api_key, use_whisper_api=True)

# Use direct Whisper (legacy mode)  
yt = YouTubeAnalyzer(api_key, use_whisper_api=False)
```

## 📊 **Monitoring**

### **Check Server Health:**
```bash
curl http://127.0.0.1:5555/health
```

### **View Statistics:**
```bash
curl http://127.0.0.1:5555/stats
```

### **Monitor Queue:**
```bash
# Watch queue size in real-time
watch -n 1 'curl -s http://127.0.0.1:5555/stats | python -m json.tool'
```

## 🔧 **Configuration**

### **API Server Settings:**
Edit `whisper_api_server.py`:
```python
# Model size: "tiny", "base", "small", "medium", "large"
server = WhisperAPIServer(model_size="small")

# Queue capacity
server = WhisperAPIServer(max_queue_size=50)

# Server port
server.run(host='127.0.0.1', port=5555)
```

### **Client Settings:**
```python
# Custom API URL
client = WhisperAPIClient("http://127.0.0.1:5555")

# Timeout settings
client.transcribe_video_sync(video_id, timeout=300)
```

## 🚦 **Usage Examples**

### **Manual Analysis (Sync):**
```python
from whisper_client import WhisperAPIClient

client = WhisperAPIClient()
transcript = client.transcribe_video_sync("dQw4w9WgXcQ")
print(transcript)
```

### **Auto Discovery (Async):**
```python
from whisper_client import WhisperAPIClient

client = WhisperAPIClient()
transcript = client.transcribe_video_async("dQw4w9WgXcQ")
print(transcript)  # May be None if still processing
```

### **Drop-in Replacement:**
```python
from whisper_client import WhisperTranscriberCompat

# Works exactly like the original
whisper = WhisperTranscriberCompat()
transcript = whisper.transcribe_video("dQw4w9WgXcQ")
```

## 🐛 **Troubleshooting**

### **Server Won't Start:**
```bash
# Check if port is in use
lsof -i :5555

# Kill existing server
pkill -f whisper_api_server

# Check GPU status
nvidia-smi
```

### **Client Can't Connect:**
```bash
# Test connectivity
curl http://127.0.0.1:5555/health

# Check server logs
tail -f whisper_api_server.log
```

### **GPU Issues:**
```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Monitor GPU usage
watch nvidia-smi
```

## 🎯 **Benefits Summary**

✅ **No more GPU conflicts**  
✅ **Both scripts run simultaneously**  
✅ **Centralized Whisper management**  
✅ **Queue system prevents overload**  
✅ **Better error handling**  
✅ **Easy monitoring and debugging**  
✅ **Backward compatible**  
✅ **Production ready**  

## 🚀 **Next Steps**

1. **Start the API server** → `python whisper_api_server.py`
2. **Test the setup** → `python test_whisper_api.py`  
3. **Run both scripts** → No more conflicts!
4. **Monitor performance** → Use `/stats` endpoint
5. **Scale if needed** → Add more worker threads

**You're now ready to run both the manual analyzer and auto discovery simultaneously! 🎉** 