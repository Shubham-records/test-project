from __future__ import annotations
from .sessions import RandomUserAgentSession
import time
import random
import logging
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from datetime import datetime

logger = logging.basicConfig(
    filename="YARS.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class YARS:
    __slots__ = ("headers", "session", "proxy", "timeout")

    def __init__(self, proxy=None, timeout=10, random_user_agent=True):
        self.session = RandomUserAgentSession() if random_user_agent else requests.Session()
        self.proxy = proxy
        self.timeout = timeout

        retries = Retry(
            total=5,
            backoff_factor=2,  # Exponential backoff
            status_forcelist=[429, 500, 502, 503, 504],
        )

        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        if proxy:
            self.session.proxies.update({"http": proxy, "https": proxy})
    def handle_search(self,url, params, after=None, before=None):
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            logging.info("Search request successful")
        except Exception as e:
            if response.status_code != 200:
                logging.info("Search request unsuccessful due to: %s", e)
                print(f"Failed to fetch search results: {response.status_code}")
                return []

        data = response.json()
        results = []
        for post in data["data"]["children"]:
            post_data = post["data"]
            results.append(
                {
                    "title": post_data["title"],
                    "link": f"https://www.reddit.com{post_data['permalink']}",
                    "description": post_data.get("selftext", "")[:269],
                }
            )
        logging.info("Search Results Retrned %d Results", len(results))
        return results
    def search_reddit(self, query, limit=10, after=None, before=None):
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": limit, "sort": "relevance", "type": "link"}
        return self.handle_search(url, params, after, before)
    def search_subreddit(self, subreddit, query, limit=10, after=None, before=None, sort="relevance"):
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "limit": limit, "sort": "relevance", "type": "link","restrict_sr":"on"}
        return self.handle_search(url, params, after, before)

    def scrape_post_details(self, permalink):
        url = f"https://www.reddit.com{permalink}.json"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            logging.info("Post details request successful : %s", url)
        except Exception as e:
            logging.info("Post details request unsccessful: %e", e)
            if response.status_code != 200:
                print(f"Failed to fetch post data: {response.status_code}")
                return None

        post_data = response.json()
        if not isinstance(post_data, list) or len(post_data) < 2:
            logging.info("Unexpected post data structre")
            print("Unexpected post data structure")
            return None

        main_post = post_data[0]["data"]["children"][0]["data"]
        title = main_post["title"]
        body = main_post.get("selftext", "")

        comments = self._extract_comments(post_data[1]["data"]["children"])
        logging.info("Successfully scraped post: %s", title)
        return {"title": title, "body": body, "comments": comments}

    def _extract_comments(self, comments):
        logging.info("Extracting comments")
        extracted_comments = []
        for comment in comments:
            if isinstance(comment, dict) and comment.get("kind") == "t1":
                comment_data = comment.get("data", {})
                extracted_comment = {
                    "author": comment_data.get("author", ""),
                    "body": comment_data.get("body", ""),
                    "score": comment_data.get("score",""),
                    "replies": [],
                }

                replies = comment_data.get("replies", "")
                if isinstance(replies, dict):
                    extracted_comment["replies"] = self._extract_comments(
                        replies.get("data", {}).get("children", [])
                    )
                extracted_comments.append(extracted_comment)
        logging.info("Successfully extracted comments")
        return extracted_comments

    def _convert_timestamp(self, unix_timestamp):
        """Convert Unix timestamp to human-readable date and time format."""
        if not unix_timestamp:
            return ""
        return datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    def scrape_user_data(self, username, limit=10):
        logging.info("Scraping user data for %s, limit: %d", username, limit)
        base_url = f"https://www.reddit.com/user/{username}/.json"
        params = {"limit": limit, "after": None}
        all_items = []
        count = 0

        while count < limit:
            try:
                response = self.session.get(
                    base_url, params=params, timeout=self.timeout
                )
                response.raise_for_status()
                logging.info("User data request successful")
            except Exception as e:
                logging.info("User data request unsuccessful: %s", e)
                if response.status_code != 200:
                    print(
                        f"Failed to fetch data for user {username}: {response.status_code}"
                    )
                    break
            try:
                data = response.json()
            except ValueError:
                print(f"Failed to parse JSON response for user {username}.")
                break

            if "data" not in data or "children" not in data["data"]:
                print(
                    f"No 'data' or 'children' field found in response for user {username}."
                )
                logging.info("No 'data' or 'children' field found in response")
                break

            items = data["data"]["children"]
            if not items:
                print(f"No more items found for user {username}.")
                logging.info("No more items found for user")
                break

            for item in items:
                kind = item["kind"]
                item_data = item["data"]
                if kind == "t3":
                    post_url = f"https://www.reddit.com{item_data.get('permalink', '')}"
                    created_utc = item_data.get("created_utc", "")
                    all_items.append(
                        {
                            "type": "post",
                            "title": item_data.get("title", ""),
                            "subreddit": item_data.get("subreddit", ""),
                            "url": post_url,
                            "created_utc": created_utc,
                            "created_date": self._convert_timestamp(created_utc),
                        }
                    )
                elif kind == "t1":
                    comment_url = (
                        f"https://www.reddit.com{item_data.get('permalink', '')}"
                    )
                    created_utc = item_data.get("created_utc", "")
                    all_items.append(
                        {
                            "type": "comment",
                            "subreddit": item_data.get("subreddit", ""),
                            "body": item_data.get("body", ""),
                            "created_utc": created_utc,
                            "created_date": self._convert_timestamp(created_utc),
                            "url": comment_url,
                            "link_flair_text": item_data.get("link_flair_text", ""),  # Add link_flair_text
                        }
                    )
                count += 1
                if count >= limit:
                    break

            params["after"] = data["data"].get("after")
            if not params["after"]:
                break

            time.sleep(random.uniform(1, 2))
            logging.info("Sleeping for random time")

        logging.info("Successfully scraped user data for %s", username)
        return all_items

    def fetch_subreddit_posts(
        self, subreddit, category, limit=10, time_filter="all", filter=None
    ):
        logging.info(
            "Fetching subreddit/user posts for %s, limit: %d, category: %s, time_filter: %s, filter: %s",
            subreddit,
            limit,
            category,
            time_filter,
            filter,
        )
        if category not in ["hot", "top", "new", "userhot", "usertop", "usernew"]:
            raise ValueError("Category for Subredit must be either 'hot', 'top', or 'new' or for User must be 'userhot', 'usertop', or 'usernew'")

        batch_size = min(100, limit)
        total_fetched = 0
        after = None
        all_posts = []

        while total_fetched < limit:
            if category == "hot":
                url = f"{subreddit}/hot.json"
            elif category == "top":
                url = f"{subreddit}/top.json"
            elif category == "new":
                url = f"{subreddit}/new.json"
            elif category == "userhot":
                url = f"{subreddit}/submitted/hot.json"
            elif category == "usertop":
                url = f"{subreddit}/submitted/top.json"
            else:
                url = f"{subreddit}/submitted/new.json"

            params = {
                "limit": batch_size,
                "after": after,
                "raw_json": 1,
                "t": time_filter,
            }
            response = None
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                logging.info("Subreddit/user posts request successful")
            except Exception as e:
                logging.info("Subreddit/user posts request unsuccessful: %s", e)
                if response and hasattr(response, 'status_code') and response.status_code != 200:
                    print(
                        f"Failed to fetch posts for subreddit/user {subreddit}: {response.status_code}"
                    )
                else:
                    print(f"Failed to fetch posts for subreddit/user {subreddit}: {str(e)}")
                    break

            data = response.json()
            posts = data["data"]["children"]
            if not posts:
                break

            for post in posts:
                post_data = post["data"]
                
                # Apply filter if provided
                if filter and isinstance(filter, list) and "link_flair_text" in post_data:
                    flair_text = post_data.get("link_flair_text")
                    if flair_text not in filter:
                        continue  # Skip this post if it doesn't match the filter
                
                created_utc = post_data["created_utc"]
                
                post_info = {
                    "title": post_data["title"],
                    "author": post_data["author"],
                    "permalink": post_data["permalink"],
                    "date": self._convert_timestamp(created_utc),  # Use formatted date instead of raw timestamp
                    "body": post_data.get("selftext", ""),  # Adding body content directly
                    "link_flair_text": post_data.get("link_flair_text", ""),  # Add link_flair_text
                }
                
                # Remove these lines that add the unwanted fields
                # "score": post_data["score"],
                # "num_comments": post_data["num_comments"],
                # "date": self._convert_timestamp(created_utc),
                
                # Also remove or comment out these conditional blocks that add image_url and thumbnail_url
                # if post_data.get("post_hint") == "image" and "url" in post_data:
                #     post_info["image_url"] = post_data["url"]
                # elif "preview" in post_data and "images" in post_data["preview"]:
                #     post_info["image_url"] = post_data["preview"]["images"][0][
                #         "source"
                #     ]["url"]
                # if "thumbnail" in post_data and post_data["thumbnail"] != "self":
                #     post_info["thumbnail_url"] = post_data["thumbnail"]

                all_posts.append(post_info)
                total_fetched += 1
                if total_fetched >= limit:
                    break

            after = data["data"].get("after")
            if not after:
                break

            time.sleep(random.uniform(1, 2))
            logging.info("Sleeping for random time")

        logging.info("Successfully fetched subreddit posts for %s", subreddit)
        return all_posts
