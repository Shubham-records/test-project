import json
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
sys.path.append(src_path)

from yars.yars import YARS
# Initialize the YARS Reddit miner
miner = YARS()
filename = "subreddit_data3.json"

# Function to scrape subreddit post details and comments and save to JSON
def scrape_subreddit_data(subreddit_name, category, limit=5, filename=filename, filter=None):
    try:
        subreddit_posts = miner.fetch_subreddit_posts(subreddit_name, category, limit=limit, time_filter="all", filter=filter)

        # Load existing data from the JSON file, if available
        try:
            with open(filename, "r") as json_file:
                existing_data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        # Scrape details and comments for each post
        for i, post in enumerate(subreddit_posts, 1):
            permalink = post["permalink"]
            post_details = miner.scrape_post_details(permalink)
            print(f"Processing post {i}")

            if post_details:
                post_data = {
                    "title": post.get("title", ""),
                    "author": post.get("author", ""),
                    "created_utc": post.get("date", ""),  # Using date field from fetch_subreddit_posts
                    "body": post_details.get("body", ""),
                    "link_flair_text": post.get("link_flair_text", ""),  # Add link_flair_text
                }

                # Append new post data to existing data
                existing_data.append(post_data)

                # Save the data incrementally to the JSON file
                save_to_json(existing_data, filename)
            else:
                print(f"Failed to scrape details for post: {post['title']}")

    except Exception as e:
        print(f"Error occurred while scraping subreddit: {e}")


# Function to save post data to a JSON file
def save_to_json(data, filename=filename):
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON file: {e}")


# Main execution
if __name__ == "__main__":
    # Remove the trailing slash
    subreddit_name = "https://www.reddit.com/r/smallbusiness"
    # Example of using filter - uncomment to use
    filter_flairs = ["Question", "Help"]
    scrape_subreddit_data(subreddit_name=subreddit_name, category="new", limit=50, filename="reddit-test5", filter=filter_flairs)
    # Without filter - shows all posts
    # scrape_subreddit_data(subreddit_name=subreddit_name, category="new", limit=50, filename="reddit-test5")