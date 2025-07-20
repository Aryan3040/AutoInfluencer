import re
import logging
from googleapiclient.discovery import build
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled, 
    NoTranscriptFound, 
    VideoUnavailable,
    TooManyRequests
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedYouTubeAnalyzer:
    def __init__(self, api_key, use_whisper=False, use_whisper_api=False):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.max_comments_per_video = 5
        self.max_transcript_words = 10000
        self.use_whisper = use_whisper
        self.use_whisper_api = use_whisper_api
        self.whisper_transcriber = None
        
        # Cache for video data to avoid redundant API calls
        self.video_cache = {}
        
        # Initialize Whisper transcriber if enabled
        if self.use_whisper:
            try:
                if self.use_whisper_api:
                    # Use API client (preferred - no GPU conflicts)
                    from whisper_client import WhisperTranscriberCompat
                    self.whisper_transcriber = WhisperTranscriberCompat(model_size="small")
                    logger.info("Whisper API client initialized as fallback")
                else:
                    # Use direct Whisper (legacy mode)
                    from whisper_transcriber import WhisperTranscriber
                    self.whisper_transcriber = WhisperTranscriber(model_size="small")
                    logger.info("Whisper transcriber (small model) initialized as fallback")
            except Exception as e:
                logger.warning(f"Could not initialize Whisper transcriber: {str(e)}")
                self.use_whisper = False
    
    def get_channel_videos_with_stats(self, channel_id, max_results=10):
        """Get recent videos with stats in a single optimized call - MAIN OPTIMIZATION"""
        try:
            # OPTIMIZATION 1: Reduce maxResults from 50 to just what we need
            search_response = self.youtube.search().list(
                q='',
                channelId=channel_id,
                part='snippet',
                type='video',
                order='date',
                maxResults=max_results  # Only get what we actually need!
            ).execute()
            
            if not search_response.get('items'):
                return []
            
            # Get video IDs
            video_ids = [video['id']['videoId'] for video in search_response['items']]
            
            # OPTIMIZATION 2: Batch request for all video details + stats in ONE call
            videos_response = self.youtube.videos().list(
                part='contentDetails,snippet,statistics',  # Get stats in same call
                id=','.join(video_ids)
            ).execute()
            
            # Process all videos with stats included
            processed_videos = []
            for video in videos_response['items']:
                video_data = {
                    'id': {'videoId': video['id']},
                    'snippet': video['snippet'],
                    'statistics': video.get('statistics', {}),
                    'duration_seconds': self._parse_duration(video['contentDetails']['duration'])
                }
                processed_videos.append(video_data)
                
                # OPTIMIZATION 3: Cache video data to avoid duplicate API calls
                self.video_cache[video['id']] = video_data
            
            logger.info(f"Fetched {len(processed_videos)} videos with stats in 2 API calls (optimized)")
            return processed_videos
            
        except Exception as e:
            logger.error(f"Error getting optimized channel videos: {str(e)}")
            return []
    
    def calculate_engagement_from_cached_videos(self, videos):
        """Calculate engagement metrics from already-fetched video data - NO ADDITIONAL API CALLS"""
        try:
            if not videos:
                return "No recent videos"
            
            total_views = 0
            total_comments = 0
            video_count = 0
            
            # Use first 5 videos for engagement calculation
            for video in videos[:5]:
                stats = video.get('statistics', {})
                views = int(stats.get('viewCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                total_views += views
                total_comments += comments
                video_count += 1
            
            if video_count == 0:
                return "No video data"
            
            avg_views = total_views // video_count
            avg_comments = total_comments // video_count
            
            # Estimate engagement rate
            if avg_views > 0:
                engagement_rate = (avg_comments / avg_views) * 100
                return f"{avg_comments} avg comments, {engagement_rate:.2f}% engagement rate"
            else:
                return f"{avg_comments} avg comments per video"
                
        except Exception as e:
            logger.error(f"Error calculating engagement: {e}")
            return "Could not calculate"
    
    def verify_niche_from_cached_videos(self, channel_info, videos, ai_analyzer):
        """Verify niche fit using already-fetched video data - NO ADDITIONAL API CALLS"""
        try:
            if not videos:
                return False, "Could not fetch videos", ""
            
            # Use first 5 videos for analysis
            sample_videos = videos[:5]
            
            # Analyze video titles and descriptions
            video_content = []
            for video in sample_videos:
                title = video['snippet']['title']
                description = video['snippet'].get('description', '')[:200]
                video_content.append(f"Title: {title}\nDescription: {description}...")
            
            content_text = "\n\n".join(video_content)
            
            # AI prompt for niche verification
            verification_prompt = f"""
Analyze these YouTube videos and determine if this channel fits our target niche: DATING ADVICE + SELF-IMPROVEMENT for men.

Video Content:
{content_text}

Channel Description: {channel_info.get('description', '')[:300]}

PRIORITY 1 - DATING FOCUSED (automatic YES):
- Dating advice & tips
- How to attract women/get girlfriend
- Relationship advice & psychology
- Flirting & conversation with women
- Masculinity & attraction tips
- Dating confidence & mindset
- Texting game (e.g. texting girls, texting on Tinder, Hinge, Bumble, DMs)
- Dating apps (Tinder, Hinge, Bumble, etc.)
- Pickup, cold approach, rizz, social skills for dating

PRIORITY 2 - SELF-IMPROVEMENT WITH DATING ELEMENTS (YES if includes some dating):
- Confidence building (mentions dating/women)
- Social skills (includes talking to women)
- Personal development (touches on relationships)
- Psychology tips (covers attraction/dating)
- Charisma & communication (mentions dating context)

REJECT - PURE GENERAL CONTENT (NO unless dating mentioned):
- Pure productivity/business only
- Fitness only (unless looks/attraction focused)
- Mental health only (unless dating anxiety)
- Pure motivational content

QUESTION: Does this channel help men with dating, attracting women, OR self-improvement that includes dating/relationship elements? (INCLUDING texting game, dating apps, flirting, pickup, DMs, etc.)

Respond with:
1. YES or NO
2. One sentence explaining why (mention dating relevance)
3. Specific category (e.g. "Dating Advice", "Dating + Self-Improvement", "Texting Game", "Dating Apps", "Social Skills + Dating", "Masculinity", etc.)

Format: YES/NO | Explanation | Category
"""
            
            # Get AI analysis
            ai_response = ai_analyzer.analyze_content(verification_prompt)
            
            # Parse response
            parts = ai_response.split('|')
            if len(parts) >= 3:
                decision = parts[0].strip().upper()
                explanation = parts[1].strip()
                category = parts[2].strip()
                
                is_match = decision == "YES"
                return is_match, explanation, category
            else:
                return False, "Could not parse AI response", ""
                
        except Exception as e:
            logger.error(f"Error verifying niche: {e}")
            return False, f"Verification error: {e}", ""
    
    def _parse_duration(self, duration):
        """Parse YouTube's ISO 8601 duration format (PT1M30S) to seconds"""
        import re
        
        # Handle format like PT1M30S, PT45S, PT2H5M30S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def cleanup(self):
        """Clean up resources"""
        if self.whisper_transcriber:
            self.whisper_transcriber.cleanup()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.cleanup()
        except Exception:
            pass 