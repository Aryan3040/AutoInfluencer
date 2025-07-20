import logging
from typing import Dict, Optional
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self, groq_api_key: Optional[str], openai_api_key: Optional[str]):
        self.groq_api_key = groq_api_key
        self.openai_api_key = openai_api_key
        
        # Rate limiting for Groq API
        self.groq_delay_seconds = 1.5  # 1.5 second delay between Groq calls
        self.last_groq_call_time = 0
        
        # Initialize clients
        self.groq_client = None
        self.openai_client = None
        
        if groq_api_key:
            try:
                from groq import Groq
                # Initialize Groq client with minimal parameters
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info("Groq client initialized successfully")
            except ImportError:
                logger.error("Groq package not installed")
            except Exception as e:
                logger.error(f"Error initializing Groq client: {str(e)}")
        
        if openai_api_key:
            try:
                from openai import OpenAI
                # Initialize OpenAI client with minimal parameters
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.error("OpenAI package not installed")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {str(e)}")
    
    def generate_insights(self, transcripts: str, comments: str) -> Dict[str, str]:
        """Generate AI insights from transcripts and comments"""
        
        # Generate tone & content summary from transcripts
        tone_content_summary = self._generate_tone_content_summary(transcripts)
        
        # Generate engagement notes from comments
        engagement_notes = self._generate_engagement_notes(comments)
        
        return {
            'tone_content_summary': tone_content_summary,
            'engagement_notes': engagement_notes
        }
    
    def analyze_content(self, prompt: str) -> str:
        """General content analysis method for custom prompts"""
        return self._call_ai_api(prompt, "content analysis")
    
    def _generate_tone_content_summary(self, transcripts: str) -> str:
        """Generate tone and content summary from video transcripts"""
        
        if not transcripts or transcripts.strip() == "":
            return "No transcript data available for analysis."
        
        prompt = f"""
Analyze this YouTube channel's transcripts and write 2 concise sentences capturing the most unique/standout characteristics.

Focus on SPECIFIC patterns you observe:
- What unique content format or approach do they use?
- Any specific topics, advice types, or recurring themes?
- Notable speaking style or delivery method?
- What makes this channel different from generic content?

Be factual and specific. Avoid generic phrases like "motivational content" or "engaging personality."

Channel Transcripts:
{transcripts[:8000]}

Write brief, direct notes highlighting only the most distinctive characteristics of this channel.
"""
        
        return self._call_ai_api(prompt, "tone and content summary")
    
    def _generate_engagement_notes(self, comments: str) -> str:
        """Generate engagement analysis from video comments"""
        
        if not comments or comments.strip() == "":
            return "No comment data available for analysis."
        
        prompt = f"""
Analyze these YouTube comments and write 1 brief sentence about engagement patterns.

Look for specific characteristics:
- Comment volume/engagement level
- What do viewers typically say? (praise, criticism, questions, etc.)
- Do comments relate to content or are they off-topic?
- Any notable patterns in viewer behavior?

Comments:
{comments[:6000]}

Write factual, specific notes about the comment patterns you observe.
"""
        
        return self._call_ai_api(prompt, "engagement notes")
    
    def _call_ai_api(self, prompt: str, analysis_type: str) -> str:
        """Call AI API with fallback logic"""
        
        # Try Groq first
        if self.groq_client:
            try:
                response = self._call_groq(prompt)
                if response:
                    logger.info(f"Generated {analysis_type} using Groq")
                    return response
            except Exception as e:
                logger.warning(f"Groq API failed for {analysis_type}: {str(e)}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self._call_openai(prompt)
                if response:
                    logger.info(f"Generated {analysis_type} using OpenAI")
                    return response
            except Exception as e:
                logger.error(f"OpenAI API failed for {analysis_type}: {str(e)}")
        
        # If both fail
        return f"Unable to generate {analysis_type} - AI services unavailable."
    
    def _call_groq(self, prompt: str) -> Optional[str]:
        """Call Groq API with rate limiting"""
        try:
            # Implement rate limiting to prevent hitting Groq limits
            current_time = time.time()
            time_since_last_call = current_time - self.last_groq_call_time
            
            if time_since_last_call < self.groq_delay_seconds:
                sleep_time = self.groq_delay_seconds - time_since_last_call
                logger.debug(f"🛡️ Groq rate limit: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            self.last_groq_call_time = time.time()
            
            completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert YouTube analytics specialist. Provide concise, professional analysis that would be valuable for influencer marketing assessments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct",  # User's specified model
                temperature=0.3,
                max_tokens=1024
            )
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API"""
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert YouTube analytics specialist. Provide concise, professional analysis that would be valuable for influencer marketing assessments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1024
            )
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    def test_connection(self) -> Dict[str, bool]:
        """Test API connections"""
        results = {"groq": False, "openai": False}
        
        # Test Groq
        if self.groq_client:
            try:
                response = self._call_groq("Say 'test successful' if you can see this message.")
                results["groq"] = response is not None and "test successful" in response.lower()
            except Exception:
                pass
        
        # Test OpenAI
        if self.openai_client:
            try:
                response = self._call_openai("Say 'test successful' if you can see this message.")
                results["openai"] = response is not None and "test successful" in response.lower()
            except Exception:
                pass
        
        return results 
