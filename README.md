# HLTV Events Discord Bot

A Python script that scrapes HLTV.org for Tier 1 CS2 events and pushes formatted updates to a Discord channel via Webhooks.

## Features
- **Smart Scaping**: Uses `curl_cffi` to bypass Cloudflare protection and `BeautifulSoup4` for robust HTML parsing.
- **Dual Category Reporting**: Sends two separate messages for better organization:
  - **Weekly Update**: Events currently ongoing or starting within the next 7 days.
  - **Monthly Update**: Events starting between 7 and 30 days from now.
- **Automated Filtering**: Specifically targets Tier 1 events based on prize pool filters (e.g., $300k - $2M).
- **GitHub Actions Integration**: Designed to run automatically every day.

## Setup

### Local Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Discord Webhook URL as an environment variable:
   ```powershell
   $env:DISCORD_WEBHOOK="your_webhook_url_here"
   ```
4. Run the script:
   ```bash
   python main.py
   ```

### GitHub Actions Deployment
1. Push this repository to GitHub.
2. Go to **Settings > Secrets and variables > Actions**.
3. Create a **New repository secret**:
   - **Name**: `DISCORD_WEBHOOK`
   - **Value**: Your Discord Webhook URL.
4. The bot is scheduled to run daily at 15:00 UTC (configurable in `.github/workflows/schedule.yml`).

## Technical Details
- **Scraper**: Pulls data directly from `https://www.hltv.org/events`.
- **Deduplication**: Ensures the same event isn't reported multiple times across different categories.
- **Rate Limit Safe**: Gracefully handles Discord's webhook execution.
