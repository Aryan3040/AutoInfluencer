# ChannelScrape - YouTube Micro-Influencer Discovery & Analysis

A comprehensive YouTube analytics platform for discovering and analyzing micro-influencers (10k-100k subscribers) with AI-powered insights and automated discovery tools.

## Features

- **Micro-Influencer Discovery**: Automatically find channels with 10k-100k subscribers
- **AI-Powered Analysis**: Content analysis using Groq/OpenAI APIs
- **Engagement Metrics**: Detailed analytics and insights
- **Transcript Analysis**: Whisper-powered video content analysis
- **Multi-API Rotation**: Automatic YouTube API key rotation for high-volume usage
- **Streamlit Interface**: Beautiful web interface for manual analysis
- **Whisper API Server**: Dedicated transcription service for concurrent processing

## Quick Start

### Prerequisites

- Python 3.8+
- YouTube Data API v3 key(s)
- Groq API key (recommended) or OpenAI API key
- CUDA-capable GPU (for Whisper transcription)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd channelscrape
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the Whisper API server:**
   ```bash
   python whisper_api_server.py
   ```

5. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

## Documentation

### [Ready to Use Guide](READY_TO_USE.md)
Complete setup and usage instructions with examples.

### [Optimization Summary](OPTIMIZATION_SUMMARY.md)
Technical details about performance optimizations and API management.

### [Micro Influencer Guide](MICRO_INFLUENCER_README.md)
Focused guide for micro-influencer discovery.

### [Whisper API Setup](WHISPER_API_SETUP.md)
Detailed instructions for setting up the transcription service.

### [API Usage Analysis](API_USAGE_ANALYSIS.md)
Analysis of API usage patterns and optimization strategies.

### [Streamlit Demo Guide](STREAMLIT_OPTIMIZATION_DEMO.md)
Guide for the Streamlit web interface.

## Usage Examples

### Manual Channel Analysis
```bash
# Start the web interface
streamlit run app.py
# Visit http://localhost:8501
```

### Automated Discovery
```bash
# Find 10 micro-influencers
python optimized_multi_api_finder.py 10

# Find unlimited influencers
python optimized_multi_api_finder.py
```

### Whisper API Usage
```bash
# Start API server
python whisper_api_server.py

# Test transcription
python test_whisper_api.py
```

## Project Structure

```
channelscrape/
├── app.py                           # Main Streamlit application
├── optimized_multi_api_finder.py    # Automated discovery script
├── streamlit_optimized_analyzer.py  # Streamlit analyzer class
├── ai_analyzer.py                   # AI analysis utilities
├── whisper_api_server.py           # Transcription API server
├── whisper_client.py               # Whisper API client
├── setup_multiple_apis.py          # API key setup utility
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
├── READY_TO_USE.md                 # Complete usage guide
├── OPTIMIZATION_SUMMARY.md         # Technical optimizations
├── MICRO_INFLUENCER_README.md      # Micro-influencer guide
├── WHISPER_API_SETUP.md            # Whisper setup guide
├── API_USAGE_ANALYSIS.md           # API usage analysis
└── STREAMLIT_OPTIMIZATION_DEMO.md  # Streamlit demo guide
```

## Configuration

### Environment Variables

Create a `.env` file with your API keys:

```bash
# YouTube Data API Keys (multiple keys for rotation)
YOUTUBE_API_KEY=your_primary_key
YOUTUBE_API_KEY_2=your_secondary_key
YOUTUBE_API_KEY_3=your_tertiary_key

# AI Analysis APIs
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
```

### API Key Setup

Use the setup utility to configure multiple YouTube API keys:

```bash
python setup_multiple_apis.py
```

## Target Use Cases

- **Marketing Agencies**: Find micro-influencers for campaigns
- **Brand Managers**: Discover authentic content creators
- **Researchers**: Analyze YouTube content trends
- **Content Creators**: Find collaboration opportunities
- **Social Media Managers**: Identify trending channels

## Search Keywords

The system targets channels in these niches:
- Dating advice and social skills
- Self-improvement and confidence
- Masculinity and personal development
- Conversation skills and charisma
- And 20+ more targeted terms

## Performance Features

- **Multi-API Rotation**: Automatic key switching to avoid quota limits
- **Concurrent Processing**: Whisper API server for parallel transcription
- **Smart Caching**: Efficient data storage and retrieval
- **Error Recovery**: Robust error handling and retry logic
- **Progress Tracking**: Real-time progress monitoring

## Privacy & Ethics

- Respects YouTube's Terms of Service
- Uses only publicly available data
- Implements rate limiting to avoid API abuse
- No personal data collection or storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [YouTube Data API v3](https://developers.google.com/youtube/v3) for channel data
- [OpenAI Whisper](https://github.com/openai/whisper) for transcription
- [Streamlit](https://streamlit.io/) for the web interface
- [Groq](https://groq.com/) for fast AI inference

## Future Enhancements

- [ ] Real-time channel monitoring
- [ ] Advanced content analysis
- [ ] Engagement prediction models
- [ ] Automated outreach tools
- [ ] Multi-platform support (TikTok, Instagram)
- [ ] Sentiment analysis
- [ ] Trend prediction algorithms 