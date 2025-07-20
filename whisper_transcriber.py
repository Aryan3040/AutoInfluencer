import os
import tempfile
import logging
from typing import Optional
import yt_dlp
import whisper
import torch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperTranscriber:
    def __init__(self, model_size="small"):
        """
        Initialize Whisper transcriber
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
                       "small" is good for 4GB VRAM GPUs
        """
        self.model_size = model_size
        self.model = None
        self.temp_dir = tempfile.mkdtemp()
        
        # Check CUDA availability with proper error handling
        self.device = self._get_best_device()
        logger.info(f"Using device: {self.device}")
    
    def _get_best_device(self):
        """Determine the best device to use with proper error handling"""
        # Set CUDA environment variables before checking
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
        
        # Force reload CUDA context
        if hasattr(torch.cuda, '_lazy_init'):
            torch.cuda._lazy_init()
        
        if not torch.cuda.is_available():
            logger.warning("CUDA not available according to PyTorch")
            return "cpu"
        
        try:
            # Test CUDA availability with proper initialization
            logger.info("Testing CUDA availability...")
            device_count = torch.cuda.device_count()
            logger.info(f"Found {device_count} CUDA device(s)")
            
            if device_count == 0:
                logger.warning("No CUDA devices found")
                return "cpu"
            
            # Get device properties
            device_props = torch.cuda.get_device_properties(0)
            logger.info(f"GPU: {device_props.name}, Memory: {device_props.total_memory / 1024**3:.1f}GB")
            
            # Try to allocate a small tensor to test if CUDA is really available
            test_tensor = torch.zeros(1, device='cuda:0')
            del test_tensor
            torch.cuda.empty_cache()
            
            logger.info("CUDA test successful, using GPU")
            return "cuda"
            
        except Exception as e:
            logger.error(f"CUDA test failed: {str(e)}")
            logger.info("Falling back to CPU")
            return "cpu"
    
    def _load_model(self):
        """Lazy load the Whisper model with CUDA error handling"""
        if self.model is None:
            try:
                logger.info(f"Loading Whisper {self.model_size} model on {self.device}...")
                
                # Try to load model on the selected device
                self.model = whisper.load_model(self.model_size, device=self.device)
                logger.info(f"Whisper model loaded successfully on {self.device}")
                
            except Exception as e:
                if "CUDA" in str(e) and self.device == "cuda":
                    logger.warning(f"CUDA error loading model: {str(e)}")
                    logger.info("Falling back to CPU...")
                    
                    # Clear CUDA cache and try CPU
                    torch.cuda.empty_cache()
                    self.device = "cpu"
                    
                    try:
                        self.model = whisper.load_model(self.model_size, device="cpu")
                        logger.info("Whisper model loaded successfully on CPU")
                    except Exception as cpu_e:
                        logger.error(f"Error loading Whisper model on CPU: {str(cpu_e)}")
                        raise
                else:
                    logger.error(f"Error loading Whisper model: {str(e)}")
                    raise
    
    def transcribe_video(self, video_id: str, max_duration_minutes: int = 120) -> Optional[str]:
        """
        Transcribe a YouTube video using Whisper
        
        Args:
            video_id: YouTube video ID
            max_duration_minutes: Maximum video duration to process (to avoid very long videos)
            
        Returns:
            Transcribed text or None if failed
        """
        audio_path = None
        try:
            # Download audio
            audio_path = self._download_audio(video_id, max_duration_minutes)
            if not audio_path:
                return None
            
            # Load model if not already loaded
            self._load_model()
            
            # Transcribe audio
            logger.info(f"Transcribing video {video_id} with Whisper on {self.device}...")
            
            # Use conservative settings to avoid NaN errors
            # Disable FP16 for now to avoid numerical issues
            result = self.model.transcribe(
                audio_path,
                language=None,  # Auto-detect language
                task="transcribe",
                fp16=False,  # Disable FP16 to avoid NaN issues
                beam_size=1,  # Simplest beam search
                best_of=1,    # Use single pass
                temperature=0,  # Deterministic output
                verbose=False
            )
            
            transcript_text = result["text"].strip()
            logger.info(f"Successfully transcribed video {video_id}")
            return transcript_text
            
        except Exception as e:
            if "CUDA" in str(e) and self.device == "cuda":
                logger.warning(f"CUDA error during transcription: {str(e)}")
                logger.info("CUDA memory might be full, clearing cache...")
                torch.cuda.empty_cache()
            logger.error(f"Error transcribing video {video_id}: {str(e)}")
            return None
        finally:
            # Clean up audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception as e:
                    logger.warning(f"Could not remove audio file {audio_path}: {str(e)}")
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda":
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
    
    def _download_audio(self, video_id: str, max_duration_minutes: int) -> Optional[str]:
        """Download audio from YouTube video"""
        url = f"https://www.youtube.com/watch?v={video_id}"
        audio_path = os.path.join(self.temp_dir, f"{video_id}.mp3")
        
        # yt-dlp options for audio extraction with better timeout handling
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': audio_path.replace('.mp3', '.%(ext)s'),
            'noplaylist': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 60,  # Increased timeout for larger files
            'retries': 3,
            'fragment_retries': 3
            # Removed match_filter to allow long videos
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first to check duration
                info = ydl.extract_info(url, download=False)
                duration = info.get('duration', 0)
                
                # Log duration but don't skip (user explicitly wants to process long videos)
                if duration > 0:
                    logger.info(f"Video {video_id} duration: {duration/60:.1f} minutes - proceeding with transcription")
                
                # Download audio
                ydl.download([url])
                
                # Find the downloaded file (yt-dlp might change the extension)
                base_path = audio_path.replace('.mp3', '')
                for ext in ['.mp3', '.m4a', '.webm', '.wav']:
                    potential_path = base_path + ext
                    if os.path.exists(potential_path):
                        return potential_path
                
                logger.error(f"Could not find downloaded audio file for {video_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading audio for video {video_id}: {str(e)}")
            return None
    
    def _duration_filter(self, max_minutes: int):
        """Filter to reject videos that are too long"""
        def filter_func(info_dict):
            duration = info_dict.get('duration')
            if duration and duration > max_minutes * 60:
                return f"Video too long: {duration/60:.1f} minutes"
            return None
        return filter_func
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {str(e)}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup() 