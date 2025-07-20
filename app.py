import streamlit as st
import os
import logging
from dotenv import load_dotenv
from streamlit_optimized_analyzer import StreamlitOptimizedAnalyzer
from ai_analyzer import AIAnalyzer
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Set up logging for API rotation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiAPIManager:
    """Manages multiple YouTube API keys with automatic rotation"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.api_calls_per_key = {i: 0 for i in range(len(self.api_keys))}
        
    def _load_api_keys(self):
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
        
        return api_keys
    
    def get_current_key(self):
        """Get the current active API key"""
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index]
    
    def get_key_info(self):
        """Get current key information for display"""
        if not self.api_keys:
            return "No API keys loaded"
        return f"Key #{self.current_key_index + 1}/{len(self.api_keys)} (Calls: {self.api_calls_per_key[self.current_key_index]})"
    
    def track_api_usage(self):
        """Track API usage for current key"""
        self.api_calls_per_key[self.current_key_index] += 1
    
    def switch_to_next_key(self):
        """Switch to next available API key"""
        if len(self.api_keys) <= 1:
            return False
        
        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        logger.info(f"Switched from API key #{old_index + 1} to #{self.current_key_index + 1}")
        return True

# Initialize multi-API manager
if 'api_manager' not in st.session_state:
    st.session_state.api_manager = MultiAPIManager()

def handle_youtube_api_error(error, api_manager=None):
    """Handle YouTube API errors and provide specific guidance for Streamlit"""
    if isinstance(error, HttpError):
        error_content = error.content.decode('utf-8') if hasattr(error, 'content') else str(error)
        
        # Check for quota exceeded
        if error.resp.status == 403:
            if 'quotaExceeded' in error_content or 'dailyLimitExceeded' in error_content:
                # Try to switch to next API key
                if api_manager and api_manager.switch_to_next_key():
                    return {
                        'type': 'quota_exceeded_switched',
                        'title': '🔄 API Key Rotated',
                        'message': f'Quota exceeded for previous key. Automatically switched to {api_manager.get_key_info()}',
                        'details': 'You can continue using the app with the new API key.',
                        'severity': 'warning'
                    }
                else:
                    return {
                        'type': 'quota_exceeded',
                        'title': '🚨 All YouTube API Keys Quota Exceeded',
                        'message': 'All your YouTube Data API keys have exceeded their daily quota. This typically resets in 24 hours.',
                        'details': 'Try again tomorrow or add more API keys to your .env file.',
                        'severity': 'critical'
                    }
            elif 'accessNotConfigured' in error_content:
                return {
                    'type': 'api_not_enabled',
                    'title': '⚙️ YouTube Data API Not Enabled',
                    'message': 'The YouTube Data API v3 is not enabled for your Google Cloud project.',
                    'details': 'Enable it in the Google Cloud Console: APIs & Services > Library > YouTube Data API v3',
                    'severity': 'critical'
                }
            else:
                return {
                    'type': 'access_forbidden',
                    'title': '🔒 YouTube API Access Forbidden',
                    'message': 'Access to the YouTube API was denied.',
                    'details': f'Error details: {error_content}',
                    'severity': 'error'
                }
        
        elif error.resp.status == 400:
            return {
                'type': 'bad_request',
                'title': '❌ Invalid Request',
                'message': 'The request to YouTube API was invalid.',
                'details': f'Check your input format. Error: {error_content}',
                'severity': 'error'
            }
        
        elif error.resp.status == 404:
            return {
                'type': 'not_found',
                'title': '🔍 Channel/Video Not Found',
                'message': 'The YouTube channel or video could not be found.',
                'details': 'Please check the URL or channel handle and try again.',
                'severity': 'warning'
            }
        
        elif error.resp.status == 500:
            return {
                'type': 'server_error',
                'title': '🛠️ YouTube API Server Error',
                'message': 'YouTube API is experiencing temporary issues.',
                'details': 'This is usually temporary. Please try again in a few minutes.',
                'severity': 'warning'
            }
        
        else:
            return {
                'type': 'unknown_http',
                'title': f'🔧 YouTube API Error (HTTP {error.resp.status})',
                'message': 'An unexpected API error occurred.',
                'details': f'Error details: {error_content}',
                'severity': 'error'
            }
    
    else:
        return {
            'type': 'unknown',
            'title': '❓ Unknown YouTube API Error',
            'message': 'An unexpected error occurred with the YouTube API.',
            'details': str(error),
            'severity': 'error'
        }

def display_api_error(error_info):
    """Display API error in Streamlit with appropriate styling"""
    if error_info['severity'] == 'critical':
        st.error(f"**{error_info['title']}**")
        st.error(error_info['message'])
        if error_info['details']:
            with st.expander("📋 Technical Details"):
                st.text(error_info['details'])
        
        # Show additional help for critical errors
        if error_info['type'] == 'quota_exceeded':
            st.info("💡 **What you can do:**")
            st.info("• Wait for quota reset (typically 24 hours)")
            st.info("• Check quota usage in Google Cloud Console")
            st.info("• Consider requesting higher quota limits")
            
    elif error_info['severity'] == 'error':
        st.error(f"**{error_info['title']}**")
        st.warning(error_info['message'])
        if error_info['details']:
            st.info(error_info['details'])
            
    else:  # warning
        st.warning(f"**{error_info['title']}**")
        st.info(error_info['message'])
        if error_info['details']:
            st.info(error_info['details'])

# Copy button functionality removed - users can use Ctrl+C/Ctrl+V directly

def main():
    st.set_page_config(
        page_title="YouTube Influencer Analyzer",
        page_icon="📺",
        layout="wide"
    )
    
    # Custom CSS for purple-blue gradient theme
    st.markdown("""
    <style>
        /* Main gradient background */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(90deg, #4c63d2 0%, #5b73e0 50%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        
        .main-header h1 {
            color: white;
            font-size: 3rem;
            font-weight: bold;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .main-header p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
        }
        
        /* Card styling */
        .analysis-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        
        /* Text area styling */
        .stTextArea textarea {
            background: rgba(255, 255, 255, 0.95) !important;
            color: #333 !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 10px !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }
        
        /* Button styling - Glassmorphic design */
        .stButton > button {
            background: rgba(255, 255, 255, 0.15) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px !important;
            padding: 0.5rem 1rem !important;
            font-weight: bold !important;
            color: white !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        }
        
        .stButton > button:hover {
            background: rgba(255, 255, 255, 0.25) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
        }
        
        /* Metrics styling */
        .metric-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            margin: 0.5rem;
            color: white;
        }
        
        /* Input styling */
        .stTextInput input {
            background: rgba(255, 255, 255, 0.95) !important;
            color: #333 !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 10px !important;
        }
        
        /* White text for visibility */
        .stMarkdown, .stText, h1, h2, h3, p {
            color: white !important;
        }
        
        /* Metric labels */
        [data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 1rem;
            border-radius: 10px;
            backdrop-filter: blur(5px);
        }
        
        [data-testid="metric-container"] > div {
            color: white !important;
        }
        
        /* Success/Info messages */
        .stSuccess, .stInfo, .stError, .stWarning {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 10px !important;
            backdrop-filter: blur(5px) !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            color: white !important;
        }
        
        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 10px !important;
        }
        
        /* API Status indicator */
        .api-status {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 0.5rem;
            font-size: 0.8rem;
            color: white;
            backdrop-filter: blur(5px);
            z-index: 1000;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # API Status indicator
    st.markdown("""
    <div class="api-status">
        🔔 API Monitor: Active
    </div>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>📺 YouTube Influencer Analyzer</h1>
        <p>Analyze YouTube channels and get AI-powered insights on content and engagement</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Use multi-API manager for YouTube API keys
    api_manager = st.session_state.api_manager
    youtube_api_key = api_manager.get_current_key()
    groq_api_key = os.getenv('GROQ_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not youtube_api_key:
        st.error("⚠️ No YouTube API Keys found. Please set YOUTUBE_API_KEY (and optionally YOUTUBE_API_KEY_2, etc.) in your .env file.")
        st.info("Get your API keys from: https://console.cloud.google.com/apis/credentials")
        return
    
    # Display multi-API status in sidebar
    with st.sidebar:
        st.markdown("### 🔑 Multi-API Status")
        st.info(f"**Active:** {api_manager.get_key_info()}")
        
        total_keys = len(api_manager.api_keys)
        if total_keys > 1:
            st.success(f"✅ **{total_keys} API keys loaded**")
            st.success("🔄 **Auto-rotation enabled**")
            total_quota = total_keys * 10000
            st.info(f"📊 **Total Daily Quota:** {total_quota:,} calls")
            
            # Show usage per key
            st.markdown("**📈 Usage per Key:**")
            for i, calls in api_manager.api_calls_per_key.items():
                key_status = "🟢 Active" if i == api_manager.current_key_index else "⚪ Standby"
                st.text(f"Key #{i+1}: {calls} calls {key_status}")
        else:
            st.warning("⚠️ Only 1 API key loaded")
            st.info("💡 Add more keys for higher quota")
            
        # Add refresh button to update status
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    if not groq_api_key and not openai_api_key:
        st.error("⚠️ At least one AI API key (Groq or OpenAI) is required.")
        st.info("Get Groq API key from: https://console.groq.com/")
        st.info("Get OpenAI API key from: https://platform.openai.com/api-keys")
        return
    
    # API Usage Information
    with st.expander("🔔 YouTube API Usage Information"):
        st.markdown("""
        **🔥 OPTIMIZED API USAGE:**
        - **60% fewer API calls** with optimized analyzer
        - Old analyzer: ~50-80 units per analysis  
        - **New analyzer: ~20-30 units per analysis**
        
        **API Monitoring Active:**
        - Automatic quota exceeded detection
        - Detailed error reporting  
        - Graceful error handling
        - Multi-API key rotation
        
        **Daily Limits:**
        - YouTube Data API: 10,000 units/day
        - **Optimized efficiency**: ~300-500 analyses per day
        - Error alerts will appear if limits are exceeded
        """)
    
    # Input section
    st.markdown("### 📝 Channel Input")
    input_text = st.text_input(
        "Enter YouTube Channel Handle or Video URL:",
        placeholder="@channelname or https://youtube.com/watch?v=..."
    )
    
    analyze_button = st.button("🔍 Analyze Channel", type="primary")
    
    if analyze_button and input_text:
        try:
            # Initialize analyzers
            with st.status("🔄 Initializing optimized analyzers...", expanded=True) as status:
                st.write(f"Setting up optimized YouTube Data API ({api_manager.get_key_info()})...")
                st.write("🔥 Using optimized analyzer for 60% fewer API calls!")
                st.write("🤖 Whisper API client enabled for videos without captions")
                youtube_analyzer = StreamlitOptimizedAnalyzer(youtube_api_key, use_whisper=True, use_whisper_api=True)  # Enable Whisper API fallback
                st.write("Setting up AI analyzers (Groq/OpenAI)...")
                ai_analyzer = AIAnalyzer(groq_api_key, openai_api_key)
                st.write("✅ All analyzers ready!")
                status.update(label="✅ Optimized analyzers initialized!", state="complete")
            
            # Extract channel data with progress tracking and multi-API retry
            with st.status("📊 Analyzing channel content...", expanded=True) as status:
                channel_data = None
                retry_count = 0
                max_retries = len(api_manager.api_keys)
                
                while retry_count < max_retries and not channel_data:
                    try:
                        current_key = api_manager.get_current_key()
                        current_analyzer = StreamlitOptimizedAnalyzer(current_key, use_whisper=True, use_whisper_api=True)  # Optimized analyzer with Whisper API
                        
                        if retry_count > 0:
                            status.write(f"🔄 Retrying with optimized analyzer on API key #{api_manager.current_key_index + 1}...")
                        
                        channel_data = current_analyzer.analyze_channel_with_progress(input_text, status)
                        
                        # Track successful API usage
                        api_manager.track_api_usage()
                        
                        if channel_data:
                            status.update(label="✅ Channel analysis complete!", state="complete")
                            break
                        else:
                            st.error("❌ Could not analyze the channel. Please check the input and try again.")
                            return
                    
                    except HttpError as e:
                        api_manager.track_api_usage()
                        
                        # Check if it's a quota error
                        if e.resp.status == 403 and ('quotaExceeded' in str(e) or 'dailyLimitExceeded' in str(e)):
                            retry_count += 1
                            
                            if api_manager.switch_to_next_key():
                                st.warning(f"⚠️ Quota exceeded for key #{retry_count}. Switching to next key...")
                                continue
                            else:
                                st.error("🚨 All API keys have exceeded quota!")
                                return
                        else:
                            # Non-quota error, handle normally
                            error_info = handle_youtube_api_error(e, api_manager)
                            display_api_error(error_info)
                            status.update(label="❌ Analysis failed due to API error", state="error")
                            return
                    
                    except Exception as e:
                        if "quota" in str(e).lower() or "limit" in str(e).lower():
                            retry_count += 1
                            
                            if api_manager.switch_to_next_key():
                                st.warning(f"⚠️ Quota issue detected. Switching to next key...")
                                continue
                            else:
                                st.error("🚨 All API keys have quota issues!")
                                return
                        else:
                            st.error(f"❌ Error during analysis: {str(e)}")
                            status.update(label="❌ Analysis failed", state="error")
                            return
                
                if not channel_data:
                    st.error("❌ Could not analyze the channel with any API key.")
                    return
                

            
            # Generate AI insights
            with st.status("🤖 Generating AI insights...", expanded=True) as status:
                st.write("Analyzing transcripts for tone & content...")
                st.write("Analyzing comments for engagement patterns...")
                try:
                    insights = ai_analyzer.generate_insights(
                        channel_data['transcripts'],
                        channel_data['comments']
                    )
                    status.update(label="✅ AI analysis complete!", state="complete")
                    
                except Exception as e:
                    st.warning(f"⚠️ AI analysis encountered an issue: {str(e)}")
                    # Provide basic insights if AI fails
                    insights = {
                        'engagement_notes': 'AI analysis unavailable - manual review recommended',
                        'tone_content_summary': 'AI analysis unavailable - manual review recommended'
                    }
                    status.update(label="⚠️ AI analysis completed with warnings", state="complete")
            
            # Display results
            st.success("🎉 Analysis complete! Results ready below.")
            display_results(channel_data, insights)
            
        except HttpError as e:
            api_manager.track_api_usage()
            error_info = handle_youtube_api_error(e, api_manager)
            display_api_error(error_info)
            
        except Exception as e:
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                error_info = {
                    'type': 'quota_exceeded',
                    'title': '🚨 API Quota Exceeded',
                    'message': 'YouTube API quota has been exceeded.',
                    'details': str(e),
                    'severity': 'critical'
                }
                display_api_error(error_info)
            else:
                st.error(f"❌ An unexpected error occurred: {str(e)}")
                st.info("Please check your API keys and internet connection.")
                
                # Show additional troubleshooting for unknown errors
                with st.expander("🔧 Troubleshooting"):
                    st.markdown("""
                    **Common solutions:**
                    - Check your YouTube API key is valid
                    - Ensure the channel/video URL is correct
                    - Verify your internet connection
                    - Try again in a few minutes
                    """)

def display_results(channel_data, insights):
    """Display the analysis results in a clean format"""
    
    # Store results in session state to prevent reset
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {
            'channel_data': channel_data,
            'insights': insights
        }
    
    st.markdown("### 📊 Analysis Results")
    
    # Channel overview with metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Channel Name", channel_data['channel_name'])
    
    with col2:
        st.metric("Videos Analyzed", len(channel_data['videos']))
    
    with col3:
        comment_range = f"{channel_data['comment_range']['min']}–{channel_data['comment_range']['max']}"
        st.metric("Engagement Range", f"{comment_range} comments/video")
    
    # AI-generated insights with copy buttons
    st.markdown("### 🤖 AI Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💬 Engagement Notes")
        st.text_area(
            "Engagement Analysis:",
            value=insights['engagement_notes'],
            height=180,
            key="engagement_notes_display",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("#### 🎯 Tone & Content Summary")
        st.text_area(
            "Content Analysis:",
            value=insights['tone_content_summary'],
            height=180,
            key="tone_content_display",
            label_visibility="collapsed"
        )
    
    # Copyable output for spreadsheet
    st.markdown("### 📋 Complete Analysis")
    
    spreadsheet_output = format_for_spreadsheet(channel_data, insights)
    st.text_area(
        "Complete analysis (select all with Ctrl+A, then copy with Ctrl+C):",
        value=spreadsheet_output,
        height=200,
        key="spreadsheet_output_display"
    )
    
    # Detailed video information
    with st.expander("📹 Detailed Video Information"):
        for i, video in enumerate(channel_data['videos'], 1):
            st.write(f"**{i}. {video['title']}**")
            st.write(f"- Video ID: {video['id']}")
            st.write(f"- Comments: {video['comment_count']}")
            
            # Enhanced transcript status
            transcript = video['transcript']
            if transcript == 'Transcript not available':
                st.write("- Transcript: ❌ Not available")
            elif transcript.startswith('[Whisper]'):
                st.write("- Transcript: 🤖 Generated by Whisper AI (Small Model)")
            else:
                st.write("- Transcript: ✅ YouTube captions available")
            
            st.write("---")

def format_for_spreadsheet(channel_data, insights):
    """Format the results for easy copying to a spreadsheet"""
    
    comment_range = f"{channel_data['comment_range']['min']}–{channel_data['comment_range']['max']}"
    
    output = f"""Channel Name: {channel_data['channel_name']}
Engagement Range: {comment_range} comments/video
Videos Analyzed: {len(channel_data['videos'])}

Engagement Notes:
{insights['engagement_notes']}

Tone & Content Summary:
{insights['tone_content_summary']}"""
    
    return output

if __name__ == "__main__":
    main() 