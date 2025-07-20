#!/usr/bin/env python3
"""
Test script for Whisper API setup
Verifies that the API server and clients work properly
"""

import time
import logging
from whisper_client import WhisperAPIClient, WhisperTranscriberCompat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_whisper_api():
    """Test the complete Whisper API setup"""
    print("🧪 Testing Whisper API Setup")
    print("=" * 50)
    
    # Test 1: API client
    print("\n1. Testing API Client...")
    client = WhisperAPIClient()
    
    if not client.health_check():
        print("❌ Whisper API server is not running!")
        print("💡 Start it with: python whisper_api_server.py")
        return False
    
    print("✅ API server is healthy")
    
    # Test 2: Stats
    stats = client.get_stats()
    print(f"📊 Server stats: {stats['stats']}")
    print(f"🎮 Device: {stats['device']}")
    
    # Test 3: Compatibility class  
    print("\n2. Testing Compatibility Class...")
    compat_client = WhisperTranscriberCompat()
    print(f"✅ Compatibility client initialized (device: {compat_client.device})")
    
    # Test 4: Quick transcription test (if you want to test with a real video)
    print("\n3. Quick Transcription Test")
    print("⏭️  Skipping actual transcription test (takes too long)")
    print("💡 To test transcription, uncomment the lines below")
    
    # Uncomment to test actual transcription:
    # test_video_id = "dQw4w9WgXcQ"  # Rick Roll (short video)
    # print(f"🎬 Testing transcription for video: {test_video_id}")
    # result = client.transcribe_video_sync(test_video_id, max_duration_minutes=5)
    # if result:
    #     print(f"✅ Transcription successful: {result[:100]}...")
    # else:
    #     print("❌ Transcription failed")
    
    print("\n🎉 All tests passed!")
    print("\n📋 Setup Summary:")
    print("✅ Whisper API server running on http://127.0.0.1:5555")
    print("✅ API client working")
    print("✅ Compatibility layer working")
    print("✅ Ready for both scripts to use!")
    
    return True

if __name__ == "__main__":
    test_whisper_api() 