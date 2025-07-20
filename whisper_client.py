#!/usr/bin/env python3
"""
Whisper API Client
Makes requests to the Whisper API server instead of using Whisper directly
"""

import requests
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class WhisperAPIClient:
    def __init__(self, api_url="http://127.0.0.1:5555"):
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """Check if the Whisper API server is healthy"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Whisper API health check failed: {e}")
            return False
    
    def transcribe_video_sync(self, video_id: str, max_duration_minutes: int = 15, timeout: int = 300) -> Optional[str]:
        """
        Synchronous transcription - blocks until complete
        Use this for the manual analyzer where you need immediate results
        """
        try:
            payload = {
                'video_id': video_id,
                'max_duration_minutes': max_duration_minutes,
                'timeout': timeout
            }
            
            logger.info(f"🎤 Requesting sync transcription for {video_id}")
            response = self.session.post(
                f"{self.api_url}/transcribe/sync", 
                json=payload, 
                timeout=timeout + 10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'completed':
                    logger.info(f"✅ Sync transcription successful: {video_id}")
                    return result['transcript']
                else:
                    logger.warning(f"❌ Sync transcription failed: {video_id} - {result.get('error', 'Unknown error')}")
                    return None
            else:
                logger.error(f"❌ API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Transcription timeout for {video_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error transcribing {video_id}: {e}")
            return None
    
    def transcribe_video_async(self, video_id: str, max_duration_minutes: int = 15) -> Optional[str]:
        """
        Asynchronous transcription - submit to queue and poll for results
        Use this for the auto discovery where transcription is nice-to-have
        """
        try:
            # Submit request
            payload = {
                'video_id': video_id,
                'max_duration_minutes': max_duration_minutes
            }
            
            logger.info(f"📤 Queuing async transcription for {video_id}")
            response = self.session.post(f"{self.api_url}/transcribe", json=payload, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to queue transcription: {response.status_code}")
                return None
            
            request_data = response.json()
            request_id = request_data['request_id']
            
            # Poll for results (with timeout)
            max_polls = 60  # 5 minutes max wait
            poll_interval = 5  # 5 seconds between polls
            
            for poll in range(max_polls):
                time.sleep(poll_interval)
                
                result_response = self.session.get(f"{self.api_url}/result/{request_id}", timeout=10)
                if result_response.status_code != 200:
                    continue
                
                result = result_response.json()
                
                if result['status'] == 'completed':
                    logger.info(f"✅ Async transcription completed: {video_id}")
                    return result['transcript']
                elif result['status'] == 'failed':
                    logger.warning(f"❌ Async transcription failed: {video_id} - {result.get('error', 'Unknown error')}")
                    return None
                # Status is 'processing', continue polling
            
            logger.warning(f"⏰ Async transcription timeout for {video_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in async transcription for {video_id}: {e}")
            return None
    
    def get_stats(self) -> dict:
        """Get API server statistics"""
        try:
            response = self.session.get(f"{self.api_url}/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

# Backward compatibility class that mimics the original WhisperTranscriber interface
class WhisperTranscriberCompat:
    """
    Drop-in replacement for WhisperTranscriber that uses the API server
    Maintains the same interface for backward compatibility
    """
    
    def __init__(self, model_size="small", api_url="http://127.0.0.1:5555"):
        self.model_size = model_size
        self.api_client = WhisperAPIClient(api_url)
        self.device = "api"  # For compatibility
        self.model = None  # For compatibility
        
        # Check if API server is available
        if not self.api_client.health_check():
            logger.warning("⚠️  Whisper API server not available - transcription will be disabled")
    
    def transcribe_video(self, video_id: str, max_duration_minutes: int = 15) -> Optional[str]:
        """
        Transcribe video using API server (synchronous)
        Maintains the same interface as the original WhisperTranscriber
        """
        if not self.api_client.health_check():
            logger.warning(f"Whisper API not available for {video_id}")
            return None
        
        return self.api_client.transcribe_video_sync(video_id, max_duration_minutes)
    
    def cleanup(self):
        """Cleanup method for compatibility"""
        pass
    
    def __del__(self):
        """Destructor for compatibility"""
        pass 