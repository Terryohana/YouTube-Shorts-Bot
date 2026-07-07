import requests
import json
import feedparser
from datetime import datetime

def fetch_rss(feed_url, source_name):
    print(f"Fetching RSS from {source_name}...")
    try:
        feed = feedparser.parse(feed_url)
        items = []
        # Fallback ranking: we'll just use the most recent ones and assign a fake velocity score 
        # or calculate one based on time since published.
        for entry in feed.entries[:5]:
            items.append({
                "source": source_name,
                "title": entry.title,
                "score": 100, # Mock score for demo
                "url": entry.link
            })
        return items
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
        return []

def main():
    print("Harvesting dynamic data...")
    topics = []
    
    topics.extend(fetch_rss("https://www.androidpolice.com/feed/", "Android Police"))
    topics.extend(fetch_rss("https://www.xda-developers.com/feed/", "XDA Developers"))
    
    # Sort by score descending (they are all 100 in this demo, so we'll just take the top 5)
    topics.sort(key=lambda x: x["score"], reverse=True)
    
    # Save the top 5
    top_5 = topics[:5]
    
    with open("trending_topics.json", "w", encoding="utf-8") as f:
        json.dump(top_5, f, indent=4)
        
    print(f"Successfully harvested {len(topics)} topics. Top 5 saved to trending_topics.json")

if __name__ == "__main__":
    main()
