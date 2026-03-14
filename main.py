import os
import time
from datetime import datetime
from curl_cffi import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK')
HLTV_EVENTS_URL = 'https://www.hltv.org/events?prizeMin=300000&prizeMax=2000000'

def fetch_top_events(limit_per_category=5):
    """Fetches top upcoming and ongoing Tier 1 events from HLTV."""
    response = requests.get(HLTV_EVENTS_URL, impersonate='chrome110')
    
    if response.status_code != 200:
        print(f"Failed to fetch HLTV events. Status Code {response.status_code}")
        return [], []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Grab all links that point to an event
    all_links = soup.find_all('a', href=lambda h: h and '/events/' in h)
    
    week_events = []
    month_events = []
    seen_hrefs = set()
    
    current_time_ms = time.time() * 1000
    seven_days_ms = 7 * 24 * 60 * 60 * 1000
    thirty_days_ms = 30 * 24 * 60 * 60 * 1000
    
    for e in all_links:
        # Stop parsing if we've filled both buckets
        if len(week_events) >= limit_per_category and len(month_events) >= limit_per_category:
            break
            
        href = e.get('href')
        if not href or href in seen_hrefs:
            continue
            
        # Check if it has unix timestamps (meaning it's an actual event block)
        unix_spans = e.find_all('span', attrs={'data-unix': True})
        if not unix_spans:
            continue
            
        seen_hrefs.add(href)
            
        # Try to extract the event name across different HLTV formats
        name_div = e.find('div', class_=['text-ellipsis', 'big-event-name', 'standard-event-name', 'small-event-name'])
        name = name_div.text.strip() if name_div else 'Unknown Event'
        
        start_unix = int(unix_spans[0].get('data-unix'))
        end_unix = int(unix_spans[-1].get('data-unix')) if len(unix_spans) > 1 else start_unix
        
        is_ongoing = start_unix <= current_time_ms <= end_unix
        
        # Determine buckets
        is_this_week = is_ongoing or (current_time_ms < start_unix <= current_time_ms + seven_days_ms)
        is_this_month = not is_this_week and (current_time_ms < start_unix <= current_time_ms + thirty_days_ms)
        
        # Skip if outside of 30 days entirely
        if not (is_this_week or is_this_month):
            continue
            
        start_dt = datetime.fromtimestamp(start_unix / 1000)
        end_dt = datetime.fromtimestamp(end_unix / 1000)
        
        if start_dt.date() == end_dt.date():
            date_str = start_dt.strftime('%b %d')
        else:
            date_str = f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}"
        
        # Try to extract the prize pool
        prize = 'TBA'
        prize_td = e.find('td', class_='prizePoolCol')
        if prize_td:
            prize = prize_td.text.strip()
        else:
            # Fallback for future events (look for a td with a title starting with $)
            val_td = e.find('td', class_='col-value', title=lambda t: t and t.startswith('$'))
            if val_td:
                prize = val_td.text.strip()
        
        link = f"https://www.hltv.org{href}"
        formatted = f"🏆 **{name}**\n📅 {date_str} | 💰 {prize}\n🔗 {link}"
        
        if is_this_week and len(week_events) < limit_per_category:
            week_events.append(formatted)
        elif is_this_month and len(month_events) < limit_per_category:
            month_events.append(formatted)
            
    return week_events, month_events

def send_webhook(matches, title):
    """Pushes the formatted schedule to Discord."""
    if not WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK environment variable not set.")
        return

    if not matches:
        content = f"🎯 **{title}:**\n\n*No events found matching your filter in this timeframe!* 🛌"
    else:
        content = f"🎯 **{title}:**\n\n" + "\n\n".join(matches)
    
    payload = {
        "username": "HLTV Event Bot",
        "avatar_url": "https://www.hltv.org/img/static/favicon/favicon-32x32.png",
        "content": content
    }
    
    response = requests.post(WEBHOOK_URL, json=payload, impersonate='chrome110')
    
    if response.status_code in [200, 204]:
        print(f"Successfully sent '{title}' to Discord.")
    else:
        print(f"Failed to send '{title}'. Error code: {response.status_code}\nResponse: {response.text}")

if __name__ == '__main__':
    week_evs, month_evs = fetch_top_events()
    send_webhook(week_evs, "Upcoming Tier 1 CS2 Events (Next 7 Days)")
    send_webhook(month_evs, "Upcoming Tier 1 CS2 Events (Next 30 Days)")
