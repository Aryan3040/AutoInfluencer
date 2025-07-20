#!/usr/bin/env python3
"""
Whisper Transcription API Server
Handles all Whisper transcription requests through a queue system
Only this server loads the Whisper model to avoid GPU conflicts
"""

import os
import logging
import time
import threading
from queue import Queue, Empty
from dataclasses import dataclass
from typing import Optional, Dict
from flask import Flask, request, jsonify
import uuid

from whisper_transcriber import WhisperTranscriber

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionRequest:
    request_id: str
    video_id: str
    max_duration_minutes: int
    timestamp: float

@dataclass 
class TranscriptionResult:
    request_id: str
    video_id: str
    success: bool
    transcript: Optional[str]
    error: Optional[str]
    processing_time: float

class WhisperAPIServer:
    def __init__(self, model_size="small", max_queue_size=50):
        self.model_size = model_size
        self.max_queue_size = max_queue_size
        
        # Initialize Whisper transcriber (loads model once)
        logger.info("🚀 Initializing Whisper API Server...")
        logger.info(f"Model: {model_size} | Max queue: {max_queue_size}")
        
        try:
            self.whisper = WhisperTranscriber(model_size=model_size)
            logger.info("✅ Whisper transcriber initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Whisper: {e}")
            raise
        
        # Request queue and results storage
        self.request_queue = Queue(maxsize=max_queue_size)
        self.results = {}  # {request_id: TranscriptionResult}
        self.processing_stats = {
            'total_requests': 0,
            'completed': 0,
            'failed': 0,
            'queue_size': 0
        }
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.info("🔄 Worker thread started")
        
        # Flask app
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'model_loaded': self.whisper.model is not None,
                'device': self.whisper.device,
                'queue_size': self.request_queue.qsize(),
                'stats': self.processing_stats
            })
        
        @self.app.route('/transcribe', methods=['POST'])
        def transcribe_video():
            """Submit transcription request"""
            try:
                data = request.json
                video_id = data.get('video_id')
                max_duration = data.get('max_duration_minutes', 120)  # Increased to 2 hours
                
                if not video_id:
                    return jsonify({'error': 'video_id required'}), 400
                
                # Check queue capacity
                if self.request_queue.qsize() >= self.max_queue_size:
                    return jsonify({'error': 'Queue full, try again later'}), 503
                
                # Create request
                request_id = str(uuid.uuid4())
                transcription_request = TranscriptionRequest(
                    request_id=request_id,
                    video_id=video_id,
                    max_duration_minutes=max_duration,
                    timestamp=time.time()
                )
                
                # Add to queue
                self.request_queue.put(transcription_request)
                self.processing_stats['total_requests'] += 1
                self.processing_stats['queue_size'] = self.request_queue.qsize()
                
                logger.info(f"📤 Queued transcription request: {video_id} (ID: {request_id[:8]})")
                
                return jsonify({
                    'request_id': request_id,
                    'status': 'queued',
                    'queue_position': self.request_queue.qsize()
                })
                
            except Exception as e:
                logger.error(f"Error handling transcription request: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/result/<request_id>', methods=['GET'])
        def get_result(request_id):
            """Get transcription result"""
            try:
                if request_id not in self.results:
                    # Check if still in queue
                    return jsonify({
                        'status': 'processing',
                        'queue_size': self.request_queue.qsize()
                    })
                
                result = self.results[request_id]
                
                response = {
                    'request_id': result.request_id,
                    'video_id': result.video_id,
                    'status': 'completed' if result.success else 'failed',
                    'processing_time': result.processing_time
                }
                
                if result.success:
                    response['transcript'] = result.transcript
                else:
                    response['error'] = result.error
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Error getting result: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/transcribe/sync', methods=['POST'])
        def transcribe_sync():
            """Synchronous transcription (uses queue but waits for result)"""
            try:
                data = request.json
                video_id = data.get('video_id')
                max_duration = data.get('max_duration_minutes', 120)  # Increased to 2 hours
                timeout = data.get('timeout', 1800)  # 30 minute default timeout
                
                if not video_id:
                    return jsonify({'error': 'video_id required'}), 400
                
                # Check queue capacity
                if self.request_queue.qsize() >= self.max_queue_size:
                    return jsonify({'error': 'Queue full, try again later'}), 503
                
                # Create request and add to queue (no more bypassing!)
                request_id = str(uuid.uuid4())
                transcription_request = TranscriptionRequest(
                    request_id=request_id,
                    video_id=video_id,
                    max_duration_minutes=max_duration,
                    timestamp=time.time()
                )
                
                # Add to queue
                self.request_queue.put(transcription_request)
                self.processing_stats['total_requests'] += 1
                self.processing_stats['queue_size'] = self.request_queue.qsize()
                
                logger.info(f"📤 Queued sync transcription request: {video_id} (ID: {request_id[:8]})")
                
                # Wait for result with timeout
                start_wait = time.time()
                while (time.time() - start_wait) < timeout:
                    if request_id in self.results:
                        result = self.results[request_id]
                        
                        response = {
                            'request_id': result.request_id,
                            'video_id': result.video_id,
                            'status': 'completed' if result.success else 'failed',
                            'processing_time': result.processing_time
                        }
                        
                        if result.success:
                            response['transcript'] = result.transcript
                            logger.info(f"✅ Sync transcription completed: {video_id} ({result.processing_time:.1f}s)")
                        else:
                            response['error'] = result.error
                            logger.warning(f"❌ Sync transcription failed: {video_id}")
                        
                        return jsonify(response)
                    
                    # Wait a bit before checking again
                    time.sleep(1)
                
                # Timeout
                logger.warning(f"⏰ Sync transcription timeout: {video_id}")
                return jsonify({
                    'status': 'timeout',
                    'video_id': video_id,
                    'error': 'Transcription timeout',
                    'timeout': timeout
                }), 408
                
            except Exception as e:
                logger.error(f"Error in sync transcription: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get server statistics"""
            return jsonify({
                'stats': self.processing_stats,
                'queue_size': self.request_queue.qsize(),
                'results_cached': len(self.results),
                'device': self.whisper.device,
                'model_size': self.model_size
            })
    
    def _process_queue(self):
        """Worker thread to process transcription queue"""
        logger.info("🔄 Queue processor started")
        
        while True:
            try:
                # Get request from queue (blocks until available)
                req = self.request_queue.get(timeout=1)
                self.processing_stats['queue_size'] = self.request_queue.qsize()
                
                logger.info(f"🎬 Processing: {req.video_id} (ID: {req.request_id[:8]})")
                start_time = time.time()
                
                # Transcribe video
                transcript = self.whisper.transcribe_video(
                    req.video_id, 
                    req.max_duration_minutes
                )
                
                processing_time = time.time() - start_time
                
                # Create result
                if transcript:
                    result = TranscriptionResult(
                        request_id=req.request_id,
                        video_id=req.video_id,
                        success=True,
                        transcript=transcript,
                        error=None,
                        processing_time=processing_time
                    )
                    self.processing_stats['completed'] += 1
                    logger.info(f"✅ Completed: {req.video_id} ({processing_time:.1f}s)")
                else:
                    result = TranscriptionResult(
                        request_id=req.request_id,
                        video_id=req.video_id,
                        success=False,
                        transcript=None,
                        error="Transcription failed",
                        processing_time=processing_time
                    )
                    self.processing_stats['failed'] += 1
                    logger.warning(f"❌ Failed: {req.video_id}")
                
                # Store result
                self.results[req.request_id] = result
                
                # Clean up old results (keep last 100)
                if len(self.results) > 100:
                    oldest_keys = sorted(self.results.keys())[:50]
                    for key in oldest_keys:
                        del self.results[key]
                
                # Mark task as done
                self.request_queue.task_done()
                
            except Empty:
                # Normal queue timeout, just continue
                continue
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                time.sleep(1)
    
    def run(self, host='127.0.0.1', port=5555, debug=False):
        """Run the Flask server"""
        logger.info(f"🌐 Starting Whisper API Server on {host}:{port}")
        logger.info("📡 Available endpoints:")
        logger.info("   GET  /health - Health check")
        logger.info("   POST /transcribe - Queue transcription")
        logger.info("   GET  /result/<id> - Get result")
        logger.info("   POST /transcribe/sync - Sync transcription")
        logger.info("   GET  /stats - Server statistics")
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    """Run the Whisper API server"""
    print("🎤 Whisper Transcription API Server")
    print("=" * 50)
    
    # Create and run server
    server = WhisperAPIServer(model_size="small")
    
    try:
        server.run(host='127.0.0.1', port=5555)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    main() 