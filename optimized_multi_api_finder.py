#!/usr/bin/env python3
"""
OPTIMIZED Multi-API Micro Influencer Finder
Reduces API usage from ~11 calls per channel to ~3 calls per channel (73% reduction)
"""

import os
import csv
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from googleapiclient.errors import HttpError
import re

from optimized_youtube_analyzer import OptimizedYouTubeAnalyzer
from ai_analyzer import AIAnalyzer

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_multi_api_micro_finder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors"""
    pass

class QuotaExceededError(YouTubeAPIError):
    """Raised when YouTube API quota is exceeded"""
    pass

@dataclass
class InfluencerData:
    name: str
    sex: str
    handle: str
    platform: str
    follower_count: str
    contact: str
    engagement: str
    niche: str
    notes: str
    status: str

class OptimizedMultiAPIKeyFinder:
    def __init__(self):
        # Load multiple API keys from environment
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.current_analyzer = None
        
        # Initialize with first working key
        self._initialize_current_analyzer()
        
        # Get AI API keys from environment
        groq_api_key = os.getenv('GROQ_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        self.ai_analyzer = AIAnalyzer(groq_api_key, openai_api_key)
        
        # API usage tracking per key
        self.api_calls_per_key = {i: 0 for i in range(len(self.api_keys))}
        
        # RATE LIMITING CONFIGURATION
        # Delay between AI analysis calls to prevent Groq rate limiting
        self.ai_delay_seconds = float(os.getenv('AI_DELAY_SECONDS', '2.0'))  # Default 2 seconds
        self.last_ai_call_time = 0
        
        logger.info(f"🕐 AI rate limiting: {self.ai_delay_seconds}s delay between Groq calls")
        
        # Comprehensive search keywords - high-converting dating/self-improvement terms
        self.search_keywords = [
            "how to text girls",
            "how to cold approach in college",
            "how to cold approach in gym",
            "how to glow up as a guy",
            "how to glow up over the summer",
            "how to glow up before school",
            "how to be more attractive men",
            "how to be more attractive to women",
            "how to be more social",
            "how to be more masculine",
            "how to be more confident",
            "how to be more charismatic",
            "cold approaching",
            "how to get girls as a short guy",
            "how to get a girl to like u",
            "how to get a girl to kiss you",
            "how to talk to your crush",
            "how to talk to a girl",
            "how to talk to women",
            "how to talk to women at a bar",
            "how to talk to women in public",
            "first date tips",
            "first date tips for men",
            "how to kiss on first date",
            "how to ask a girl out",
            "body language signs a girl likes you",
            "how to stop being a nice guy",
            "how to stop being shy",
            "how to stop being socially awkward",
            "how to get matches on tinder",
            "how to get matches on hinge",
            "how to get matches on bumble",
            "how to get matches on dating apps",
            "rizz tips",
            "rizz tutorial",
            "rizz text",
            "rizz text messages",
            "rizz to say to a girl",
            "how to get girls as an introvert",
            "how to get girls as an asian guy",
            "how to get girls as an indian guy",
            "flirting with girls"
        ]
        
        # Subscriber count range for micro influencers
        self.min_subscribers = 10000
        self.max_subscribers = 100000
        
        # Output CSV file
        self.csv_filename = f"optimized_micro_influencers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.discovered_channels = set()  # Track to avoid duplicates

        # --- NEW: Load discovered handles and channel IDs from discovered.csv ---
        self.discovered_handles = set()
        self.discovered_channel_ids = set()
        try:
            with open('discovered.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    handle = row.get('Handle', '').strip()
                    # Normalize: remove @, lowercase, split if comma/space separated
                    for h in re.split(r'[ ,]+', handle):
                        h = h.strip().lstrip('@').lower()
                        if h:
                            self.discovered_handles.add(h)
                    # Try to get channel ID if present (optional, for future-proofing)
                    channel_id = row.get('Channel ID', '').strip()
                    if channel_id and channel_id.startswith('UC'):
                        self.discovered_channel_ids.add(channel_id)
        except Exception as e:
            logger.warning(f"Could not load discovered.csv: {e}")
    
    def _ensure_ai_rate_limit(self):
        """Ensure we don't exceed AI API rate limits by adding delays"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_ai_call_time
        
        if time_since_last_call < self.ai_delay_seconds:
            sleep_time = self.ai_delay_seconds - time_since_last_call
            logger.debug(f"⏰ AI rate limit: sleeping {sleep_time:.1f}s to prevent Groq rate limiting")
            time.sleep(sleep_time)
        
        self.last_ai_call_time = time.time()
    
    def _load_api_keys(self) -> List[str]:
        """Load multiple YouTube API keys from environment"""
        api_keys = []
        
        # Primary key
        primary_key = os.getenv('YOUTUBE_API_KEY')
        if primary_key:
            api_keys.append(primary_key)
        
        # Secondary keys
        i = 2
        while True:
            key = os.getenv(f'YOUTUBE_API_KEY_{i}')
            if key:
                api_keys.append(key)
                i += 1
            else:
                break
        
        if not api_keys:
            raise ValueError("No YOUTUBE_API_KEY found in environment variables")
        
        logger.info(f"🔑 Loaded {len(api_keys)} YouTube API keys")
        return api_keys
    
    def _initialize_current_analyzer(self):
        """Initialize current analyzer with active API key"""
        if self.current_key_index < len(self.api_keys):
            api_key = self.api_keys[self.current_key_index]
            # Enable Whisper API client for fallback transcription
            self.current_analyzer = OptimizedYouTubeAnalyzer(
                api_key, 
                use_whisper=True, 
                use_whisper_api=True
            )
            logger.info(f"🔄 Initialized OptimizedYouTubeAnalyzer with key #{self.current_key_index + 1} (Whisper API enabled)")
        else:
            raise QuotaExceededError("All API keys exhausted")
    
    def switch_to_next_api_key(self):
        """Switch to the next available API key"""
        self.current_key_index += 1
        if self.current_key_index >= len(self.api_keys):
            raise QuotaExceededError("All API keys exhausted")
        
        # Cleanup current analyzer
        if self.current_analyzer:
            self.current_analyzer.cleanup()
        
        # Initialize new analyzer
        self._initialize_current_analyzer()
        
        logger.info(f"🔄 Switched to API key #{self.current_key_index + 1}")
    
    def track_api_usage(self):
        """Track API usage for current key"""
        self.api_calls_per_key[self.current_key_index] += 1
        total_calls = sum(self.api_calls_per_key.values())
        logger.debug(f"📊 API call #{total_calls} (Key #{self.current_key_index + 1}: {self.api_calls_per_key[self.current_key_index]})")
    
    def _is_discovered(self, channel_info, item=None):
        """Check if a channel is already discovered by handle, channelTitle, customUrl, or channelId"""
        # Handles from channel_info
        handle = channel_info.get('handle', '').strip().lstrip('@').lower()
        custom_url = channel_info.get('handle', '').strip().replace('@', '').lower()
        channel_id = channel_info.get('channel_id', '').strip()
        title = channel_info.get('title', '').strip().lower()
        # Handles from item (search result)
        item_title = ''
        if item:
            item_title = item['snippet'].get('channelTitle', '').strip().lstrip('@').lower()
        # Check all forms
        for h in [handle, custom_url, title, item_title]:
            if h and h in self.discovered_handles:
                return True
        if channel_id and channel_id in self.discovered_channel_ids:
            return True
        return False

    def search_channels_by_keyword(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Video-to-Channel Discovery: Search for VIDEOS then extract their CHANNELS"""
        try:
            logger.info(f"🔍 Video-to-Channel search: '{keyword}' (Key #{self.current_key_index + 1})")
            
            # Track API usage
            self.track_api_usage()
            
            # VIDEO-TO-CHANNEL STRATEGY: Search for recent VIDEOS, extract their channels
            from datetime import datetime, timedelta
            
            # Recent content bias: only 2024+ content for active creators
            recent_date = "2024-01-01T00:00:00Z"
            
            search_response = self.current_analyzer.youtube.search().list(
                q=keyword,
                part='snippet',
                type='video',  # Search VIDEOS not channels
                maxResults=max_results,  # 50 videos per keyword!
                order='relevance',
                publishedAfter=recent_date  # Recent content bias
            ).execute()
            
            channels_found = []
            channel_ids_seen = set()
            
            # Extract unique channels from video creators
            for item in search_response.get('items', []):
                channel_id = item['snippet']['channelId']
                
                # Skip if already seen this session
                if channel_id in channel_ids_seen or channel_id in self.discovered_channels:
                    continue
                    
                # --- NEW: Use improved discovered check ---
                fake_channel_info = {
                    'handle': item['snippet'].get('channelTitle', ''),
                    'channel_id': channel_id,
                    'title': item['snippet'].get('channelTitle', '')
                }
                if self._is_discovered(fake_channel_info, item):
                    logger.info(f"Skipping already discovered channel: {fake_channel_info['handle']} (ID: {channel_id})")
                    continue
                    
                channel_ids_seen.add(channel_id)
                
                # Get channel details with subscriber filtering
                channel_info = self.get_channel_details(channel_id)
                if channel_info:
                    if self._is_discovered(channel_info, item):
                        logger.info(f"Skipping already discovered channel (details): {channel_info.get('handle', '')} (ID: {channel_id})")
                        continue
                    channels_found.append(channel_info)
            
            logger.info(f"📺 Found {len(search_response.get('items', []))} videos → {len(channels_found)} qualifying channels for '{keyword}'")
            return channels_found
            
        except HttpError as e:
            if e.resp.status == 403 and ('quotaExceeded' in str(e) or 'dailyLimitExceeded' in str(e)):
                logger.error(f"Quota exceeded, switching to next key...")
                self.switch_to_next_api_key()
                return self.search_channels_by_keyword(keyword, max_results)
            else:
                logger.error(f"YouTube API error: {str(e)}")
                return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def get_channel_details(self, channel_id: str) -> Optional[Dict]:
        """Get channel details - 1 API call"""
        try:
            self.track_api_usage()
            
            response = self.current_analyzer.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            ).execute()
            
            if not response.get('items'):
                return None
                
            channel = response['items'][0]
            snippet = channel['snippet']
            stats = channel['statistics']
            
            # Check subscriber count
            subscriber_count = stats.get('subscriberCount')
            if not subscriber_count:
                return None
                
            subscriber_count = int(subscriber_count)
            if not (self.min_subscribers <= subscriber_count <= self.max_subscribers):
                return None
            
            return {
                'channel_id': channel_id,
                'title': snippet['title'],
                'handle': f"@{snippet.get('customUrl', channel_id)}",
                'description': snippet.get('description', ''),
                'subscriber_count': subscriber_count,
                'video_count': int(stats.get('videoCount', 0)),
                'view_count': int(stats.get('viewCount', 0))
            }
            
        except Exception as e:
            logger.error(f"Error getting channel details: {e}")
            return None
    
    def process_channel_optimized(self, channel_info: Dict) -> bool:
        """OPTIMIZED: Process channel with minimal API calls (2 total instead of 7+)"""
        try:
            # Skip if already processed
            if channel_info['channel_id'] in self.discovered_channels:
                return False
            
            # OPTIMIZATION: Get videos with stats in one efficient call (2 API calls total)
            videos = self.current_analyzer.get_channel_videos_with_stats(
                channel_info['channel_id'], max_results=15
            )
            
            if not videos:
                return False
            
            # --- NEW: Filter for minimum views ---
            min_views_per_video = 1000
            min_videos_with_min_views = 8
            videos_with_min_views = [v for v in videos if int(v.get('statistics', {}).get('viewCount', 0)) >= min_views_per_video]
            if len(videos_with_min_views) < min_videos_with_min_views:
                logger.info(f"Skipping {channel_info['title']} - only {len(videos_with_min_views)}/{len(videos)} videos have at least {min_views_per_video} views")
                return False
            
            # Track the 2 API calls from get_channel_videos_with_stats
            self.track_api_usage()  # For search
            self.track_api_usage()  # For videos.list with stats
            
            # OPTIMIZATION: Use cached video data for BOTH niche verification AND engagement
            # This eliminates 7+ additional API calls per channel!
            
            # RATE LIMITING: Ensure we don't exceed Groq API limits
            self._ensure_ai_rate_limit()
            
            # Verify niche fit using cached videos (0 additional API calls)
            is_match, explanation, category = self.current_analyzer.verify_niche_from_cached_videos(
                channel_info, videos, self.ai_analyzer
            )
            
            if not is_match:
                logger.info(f"❌ {channel_info['title']} - Not a match: {explanation} (Category: {category})")
                return False
            
            # Calculate engagement using cached videos (0 additional API calls)  
            engagement = self.current_analyzer.calculate_engagement_from_cached_videos(videos)
            
            logger.info(f"✅ MATCH FOUND: {channel_info['title']} - {category}")
            
            # Format data and save
            sub_count = channel_info['subscriber_count']
            follower_display = f"{sub_count/1000:.1f}K YT" if sub_count >= 1000 else f"{sub_count} YT"
            
            influencer = InfluencerData(
                name=channel_info['title'],
                sex="",
                handle=channel_info['handle'],
                platform="YT",
                follower_count=follower_display,
                contact="",
                engagement=engagement,
                niche=category,
                notes=f"Optimized finder: {explanation}",
                status="Found"
            )
            
            self.save_to_csv(influencer)
            self.discovered_channels.add(channel_info['channel_id'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing channel: {e}")
            return False
    
    def save_to_csv(self, influencer: InfluencerData):
        """Save influencer data to CSV file"""
        file_exists = os.path.exists(self.csv_filename)
        
        with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'Sex', 'Handle', 'Platform', 'Follower Count', 
                         'Contact', 'Engagement', 'Niche', 'Notes', 'Status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'Name': influencer.name,
                'Sex': influencer.sex,
                'Handle': influencer.handle,
                'Platform': influencer.platform,
                'Follower Count': influencer.follower_count,
                'Contact': influencer.contact,
                'Engagement': influencer.engagement,
                'Niche': influencer.niche,
                'Notes': influencer.notes,
                'Status': influencer.status
            })
    
    def run_optimized_discovery(self, target_influencers: int = 30, max_channels_per_keyword: int = 50):
        """Run optimized discovery to find a specific number of micro influencers"""
        logger.info(f"🚀 OPTIMIZED discovery - targeting {target_influencers} micro influencers")
        logger.info(f"📋 Will analyze up to {max_channels_per_keyword} channels per keyword")
        
        channels_processed = 0
        matches_found = 0
        
        # Shuffle keywords for variety
        keywords = self.search_keywords.copy()
        random.shuffle(keywords)
        
        try:
            for keyword in keywords:
                if matches_found >= target_influencers:
                    logger.info(f"🎯 TARGET REACHED! Found {matches_found} influencers")
                    break
                
                logger.info(f"🔍 Searching keyword: '{keyword}' (Need {target_influencers - matches_found} more matches)")
                channels_in_keyword = 0
                    
                # Video-to-Channel discovery with 50 results per keyword
                channels = self.search_channels_by_keyword(keyword, max_results=50)
                
                for channel_info in channels:
                    if matches_found >= target_influencers:
                        break
                    if channels_in_keyword >= max_channels_per_keyword:
                        logger.info(f"Max channels reached for keyword '{keyword}'")
                        break
                    
                    # Process with optimized method
                    if self.process_channel_optimized(channel_info):
                        matches_found += 1
                        logger.info(f"🎉 MATCH #{matches_found}/{target_influencers}: {channel_info['title']}")
                    
                    channels_processed += 1
                    channels_in_keyword += 1
                    
                    # Small additional delay between channels to be extra safe
                    time.sleep(0.5)
                
                if not channels:
                    logger.info(f"No channels found for keyword '{keyword}'")
        
        except QuotaExceededError:
            logger.error(f"❌ All API keys exhausted after finding {matches_found} influencers.")
        except KeyboardInterrupt:
            logger.info(f"🛑 Stopped by user after finding {matches_found} influencers.")
            
        total_calls = sum(self.api_calls_per_key.values())
        efficiency = total_calls / max(channels_processed, 1)
        
        logger.info(f"\n🎯 FINAL RESULTS:")
        logger.info(f"✅ Found: {matches_found}/{target_influencers} micro influencers ({matches_found/target_influencers*100:.1f}% of target)")
        logger.info(f"📊 Channels analyzed: {channels_processed}")
        logger.info(f"📞 Total API calls: {total_calls}")
        logger.info(f"🔥 Efficiency: {efficiency:.1f} calls per channel (vs ~11 in old version)")
        logger.info(f"💾 Results saved in: {self.csv_filename}")
        
        return matches_found

def main():
    """Main function"""
    import sys
    
    # Parse command line arguments
    target_count = 30  # default
    if len(sys.argv) > 1:
        try:
            target_count = int(sys.argv[1])
            if target_count <= 0:
                print("❌ Target count must be a positive number")
                sys.exit(1)
        except ValueError:
            print("❌ Invalid number. Usage: python optimized_multi_api_finder.py [target_count]")
            print("Example: python optimized_multi_api_finder.py 100")
            sys.exit(1)
    
    try:
        finder = OptimizedMultiAPIKeyFinder()
        
        print("🚀 ADVANCED Video-to-Channel Discovery System")
        print(f"🎯 Target: {target_count} micro influencers")
        print(f"🔑 Using {len(finder.api_keys)} API keys")
        print(f"📺 Strategy: 42 keywords × 50 videos = 2,100 potential channels")
        print(f"📊 Efficiency: ~4 calls per channel (vs ~11 in old version)")
        print(f"⏰ Recent content bias: 2024+ videos only (active creators)")
        print("=" * 60)
        
        # Run discovery
        matches = finder.run_optimized_discovery(target_influencers=target_count)
        
        if matches >= target_count:
            print(f"\n🎉 SUCCESS! Found all {matches} requested micro influencers!")
        else:
            print(f"\n✅ Found {matches} micro influencers (fell short of {target_count} target)")
            print("💡 Try running again or add more API keys for higher success rate")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main() 