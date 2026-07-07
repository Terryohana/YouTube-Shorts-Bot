import subprocess
import sys
import json

def run_step(step_name, cmd):
    print(f"\n{'='*50}\n  {step_name}\n{'='*50}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during {step_name}: {e}")
        sys.exit(1)

def main():
    print("Daily Automated YouTube Shorts Pipeline")
    print("========================================\n")
    
    # Step 1: Harvest trending topics
    run_step("Step 1: Harvesting Trending Topics", [sys.executable, "data_harvester.py"])
    
    # Step 2: Read top topic
    with open("trending_topics.json", "r", encoding="utf-8") as f:
        topics = json.load(f)
    
    if not topics:
        print("No topics found. Exiting.")
        sys.exit(1)
    
    top = topics[0]
    title = top["title"]
    source = top["source"]
    url = top["url"]
    
    print(f"\n  Selected topic: {title}")
    print(f"  Source: {source}")
    print(f"  URL: {url}\n")
    
    # Step 3: Upload (the agent will handle image generation, script writing, 
    # video rendering, and upload when the cron triggers it)
    print(f"\nTopic ready for the agent to process:")
    print(f"TITLE={title}")
    print(f"SOURCE={source}")  
    print(f"URL={url}")

if __name__ == "__main__":
    main()
