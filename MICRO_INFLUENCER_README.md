# Micro Influencer Finder for Dating/Social Skills Niche

Automatically discovers YouTube micro influencers (10k-100k subscribers) in the dating advice, social skills, and psychology niche.

## Features

- **Automated Search**: Uses 20+ targeted keywords to find relevant channels
- **AI Verification**: Analyzes 5 random videos per channel to confirm niche fit
- **Subscriber Filtering**: Only finds channels with 10k-100k subscribers
- **Auto Data Collection**: Calculates engagement metrics, formats subscriber counts
- **CSV Export**: Matches your spreadsheet format exactly
- **Continuous Discovery**: Runs in background with configurable cycles
- **Duplicate Prevention**: Tracks discovered channels to avoid repeats

## Quick Start

### 1. Test Run (Recommended First)
```bash
python test_micro_finder.py
```
This will test 3 keywords and process ~15 channels total to verify everything works.

### 2. Continuous Discovery
```bash
python micro_influencer_finder.py
```
Runs continuously, processing ~25 channels per cycle, 30-minute breaks between cycles.

## Output Format

CSV file with columns matching your spreadsheet:
- **Name**: Channel name
- **Sex**: (Empty - for manual review)
- **Handle**: @username format
- **Platform**: "YT"
- **Follower Count**: "47.2K YT" format
- **Contact**: (Empty - for manual research)
- **Engagement**: "142 avg comments, 1.34% engagement rate"
- **Niche**: AI-determined category (Dating Advice, Social Skills, etc.)
- **Notes**: "Auto-discovered: [AI explanation]"
- **Status**: "Found"

## Search Keywords

Current keywords include:
- how to flirt, dating advice, social skills
- looksmaxxing, redpill, black pill
- confidence tips, masculinity tips
- how to attract women, pickup lines
- conversation skills, body language
- self improvement, charisma tips
- And 10+ more targeted terms

## Configuration

Edit `micro_influencer_finder.py` to adjust:
- `self.min_subscribers` / `self.max_subscribers`: Subscriber range
- `self.search_keywords`: Add/remove search terms
- `cycle_delay_minutes`: Time between discovery cycles
- `max_channels_per_cycle`: Channels processed per cycle

## Files Created

- `micro_influencers_YYYYMMDD_HHMMSS.csv`: Main results
- `micro_influencer_finder.log`: Detailed logs
- `test_micro_influencers.csv`: Test run results

## API Usage

Uses same APIs as main analyzer:
- YouTube Data API (for search/channel data)
- Groq API (for AI niche verification)

## Tips

- Start with test run to verify system works
- Monitor logs for any API errors
- Check CSV periodically to see discovered influencers
- Use Ctrl+C to stop continuous discovery
- Results are automatically deduplicated across runs 