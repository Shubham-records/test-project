import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import List, Dict, Any, Union, Optional
import time
import api_keys  # Import the api_keys module
import json

class GoogleSheetsClient:
    def __init__(self):
        self._client = None
        self._credentials = None
        self._spreadsheet = None
    
    @property
    def client(self):
        """Initialize and return the Google Sheets client using service account credentials"""
        if self._client is None:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Use credentials directly from api_keys.py
            self._credentials = Credentials.from_service_account_info(
                api_keys.GOOGLE_SHEET_CREDENTIALS, 
                scopes=scopes
            )
            self._client = gspread.authorize(self._credentials)
        return self._client
    
    @property
    def spreadsheet(self):
        """Get or open the spreadsheet"""
        if self._spreadsheet is None:
            try:
                # Try to open by name first
                self._spreadsheet = self.client.open(api_keys.GOOGLE_SPREADSHEET_ID)
            except gspread.exceptions.SpreadsheetNotFound:
                # If not found by name, try as an ID
                try:
                    self._spreadsheet = self.client.open_by_key(api_keys.GOOGLE_SPREADSHEET_ID)
                except Exception as e:
                    print(f"Error opening spreadsheet: {e}")
                    raise
        return self._spreadsheet
    
    def get_worksheet(self, sheet_name):
        """Get a specific worksheet by name, creating it if it doesn't exist"""
        try:
            # Try to get the worksheet by name
            worksheet = self.spreadsheet.worksheet(sheet_name)
            
            # Check if headers exist
            all_values = worksheet.get_all_values()
            if not all_values:
                # Sheet exists but is empty, add headers
                if sheet_name == api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]:
                    headers = ["Title", "Author", "CreatedUTC", "Body", "LinkFlairText"]
                    worksheet.append_row(headers)
                elif sheet_name == api_keys.GOOGLE_SHEET_NAMES["DONE_ARTICLE"]:
                    headers = ["Title", "Author", "CreatedUTC", "ArticleContent", "Status"]
                    worksheet.append_row(headers)
            else:
                # Check if first row contains proper headers
                first_row = all_values[0]
                if sheet_name == api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"] and "Title" not in first_row:
                    # Clear the sheet and add headers
                    worksheet.clear()
                    headers = ["Title", "Author", "CreatedUTC", "Body", "LinkFlairText"]
                    worksheet.append_row(headers)
                    
                    # Re-add the data (if any)
                    if len(all_values) > 0:
                        for row in all_values:
                            worksheet.append_row(row)
                            
                elif sheet_name == api_keys.GOOGLE_SHEET_NAMES["DONE_ARTICLE"] and "Title" not in first_row:
                    # Clear the sheet and add headers
                    worksheet.clear()
                    headers = ["Title", "Author", "CreatedUTC", "ArticleContent", "Status"]
                    worksheet.append_row(headers)
                    
                    # Re-add the data (if any)
                    if len(all_values) > 0:
                        for row in all_values:
                            worksheet.append_row(row)
                            
        except gspread.exceptions.WorksheetNotFound:
            # If not found, create a new worksheet
            print(f"Worksheet '{sheet_name}' not found, creating it...")
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            
            # Add headers for RedditData sheet
            if sheet_name == api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]:
                headers = ["Title", "Author", "CreatedUTC", "Body", "LinkFlairText"]
                worksheet.append_row(headers)
            
            # Add headers for done_article sheet
            elif sheet_name == api_keys.GOOGLE_SHEET_NAMES["DONE_ARTICLE"]:
                headers = ["Title", "Author", "CreatedUTC", "ArticleContent", "Status"]
                worksheet.append_row(headers)
        
        return worksheet
    
    def get_row_count(self, sheet_name=None):
        """
        Get the number of rows in a worksheet
        
        Args:
            sheet_name (str): The name of the sheet to count rows from
            
        Returns:
            int: Number of rows (excluding header row), or 0 if error
        """
        if sheet_name is None:
            sheet_name = api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]
        
        try:
            worksheet = self.get_worksheet(sheet_name)
            # Get all values and subtract 1 for the header row
            row_count = len(worksheet.get_all_values()) - 1
            if row_count < 0:
                row_count = 0
            return row_count
        except Exception as e:
            print(f"Error getting row count from Google Sheets: {e}")
            return 0
    
    def is_duplicate_post(self, title, author, sheet_name=None):
        """
        Check if a post with the same title and author already exists in the sheet
        
        Args:
            title (str): The post title to check
            author (str): The post author to check
            sheet_name (str): The name of the sheet to check
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        if sheet_name is None:
            sheet_name = api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]
        
        try:
            # Get the worksheet directly
            worksheet = self.get_worksheet(sheet_name)
            
            # Get all values as a list of lists
            all_values = worksheet.get_all_values()
            if len(all_values) <= 1:  # Only header or empty
                return False
                
            # The first row should be headers, but let's check the actual data
            # If the first row doesn't contain "Title" and "Author", we need to fix the sheet
            headers = all_values[0]
            if "Title" not in headers or "Author" not in headers:
                print(f"Warning: Sheet headers are not properly set. Current headers: {headers}")
                print("Attempting to check for duplicates using column positions instead...")
                
                # Assume standard column order: Title is first column, Author is second column
                title_idx = 0
                author_idx = 1
            else:
                # Get header row to find title and author column indices
                try:
                    title_idx = headers.index("Title")
                    author_idx = headers.index("Author")
                except ValueError:
                    print(f"Could not find Title or Author columns in the sheet. Headers: {headers}")
                    return False
            
            # Normalize the input values
            title_normalized = title.strip().lower() if title else ""
            author_normalized = author.strip().lower() if author else ""
            
            # Debug output
            print(f"Checking for duplicate: '{title_normalized}' by {author_normalized}")
            
            # Check each row (skip header)
            for i, row in enumerate(all_values[1:], 1):
                if len(row) > max(title_idx, author_idx):  # Make sure row has enough columns
                    row_title = row[title_idx].strip().lower() if row[title_idx] else ""
                    row_author = row[author_idx].strip().lower() if row[author_idx] else ""
                    
                    if row_title == title_normalized and row_author == author_normalized:
                        print(f"Duplicate found at row {i+1}: '{row_title}' by {row_author}")
                        return True
            
            print(f"No duplicates found for '{title_normalized}' by {author_normalized}")
            return False
        except Exception as e:
            print(f"Error checking for duplicate posts: {e}")
            import traceback
            traceback.print_exc()
            return False

    def add_to_sheet(self, post_data, sheet_name=None, skip_duplicate_check=False):
        """
        Add data to Google Sheets using the official API
        
        Args:
            post_data (dict): The post data to add to the sheet
            sheet_name (str): The name of the sheet to add data to
            skip_duplicate_check (bool): Whether to skip duplicate checking
            
        Returns:
            bool: True if successful, False otherwise
        """
        if sheet_name is None:
            sheet_name = api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]
        
        try:
            # Check for duplicates if it's the Reddit data sheet and we're not skipping the check
            if sheet_name == api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"] and not skip_duplicate_check:
                if self.is_duplicate_post(post_data.get("title", ""), post_data.get("author", "")):
                    print(f"Skipping duplicate post: '{post_data.get('title', '')}'")
                    return False
                
            worksheet = self.get_worksheet(sheet_name)
            
            # Prepare row data based on sheet type
            if sheet_name == api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]:
                row_data = [
                    post_data.get("title", ""),
                    post_data.get("author", ""),
                    post_data.get("created_utc", ""),
                    post_data.get("body", ""),
                    post_data.get("link_flair_text", "")
                ]
            elif sheet_name == api_keys.GOOGLE_SHEET_NAMES["DONE_ARTICLE"]:
                row_data = [
                    post_data.get("title", ""),
                    post_data.get("author", ""),
                    post_data.get("created_utc", ""),
                    post_data.get("article_content", ""),
                    post_data.get("status", "Completed")
                ]
            else:
                # Generic fallback
                row_data = list(post_data.values())
            
            # Append the row to the worksheet
            worksheet.append_row(row_data)
            
            print(f"Added post '{post_data.get('title', '')}' to Google Sheets")
            return True
                
        except Exception as e:
            print(f"Error adding data to Google Sheets: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def read_from_sheet(self, sheet_name=None):
        """
        Read data from Google Sheets using the official API
        
        Args:
            sheet_name (str): The name of the sheet to read from
            
        Returns:
            list: List of dictionaries containing the sheet data, or None if error
        """
        if sheet_name is None:
            sheet_name = api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]
        
        try:
            worksheet = self.get_worksheet(sheet_name)
            
            # Get all records as dictionaries
            records = worksheet.get_all_records()
            
            print(f"Successfully read {len(records)} records from Google Sheets")
            return records
                
        except Exception as e:
            print(f"Error reading data from Google Sheets: {e}")
            return None
    
    def batch_add_to_sheets(self, post_data_list, sheet_name=None, delay=1):
        """
        Add multiple posts to Google Sheets with a delay between requests to avoid rate limiting.
        
        Args:
            post_data_list (list): List of post data dictionaries to add to the sheet
            sheet_name (str): The name of the sheet to add data to
            delay (int): Delay in seconds between requests
            
        Returns:
            int: Number of successfully added posts
        """
        if sheet_name is None:
            sheet_name = api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"]
        
        successful_posts = 0
        
        for post_data in post_data_list:
            if self.add_to_sheet(post_data, sheet_name):
                successful_posts += 1
            
            # Add delay to avoid rate limiting
            if delay > 0 and post_data != post_data_list[-1]:  # No delay after the last item
                time.sleep(delay)
        
        return successful_posts
    
    def mark_as_done(self, post_data, article_content, status="Completed"):
        """
        Mark a post as done by adding it to the done_article sheet
        
        Args:
            post_data (dict): The original post data
            article_content (str): The generated article content
            status (str): The status of the article
            
        Returns:
            bool: True if successful, False otherwise
        """
        done_data = {
            "title": post_data.get("title", ""),
            "author": post_data.get("author", ""),
            "created_utc": post_data.get("created_utc", ""),
            "article_content": article_content,
            "status": status
        }
        
        return self.add_to_sheet(done_data, api_keys.GOOGLE_SHEET_NAMES["DONE_ARTICLE"])
    
    async def process_post(self, post, miner_instance):
        """
        Process a single Reddit post and prepare it for adding to Google Sheets
        
        Args:
            post (dict): The post data from Reddit
            miner_instance: The YARS miner instance
            
        Returns:
            dict: Processed post data ready for Google Sheets, or None if processing failed
        """
        try:
            permalink = post["permalink"]
            post_details = miner_instance.scrape_post_details(permalink)
            
            if post_details:
                post_data = {
                    "title": post.get("title", ""),
                    "author": post.get("author", ""),
                    "created_utc": post.get("date", ""),
                    "body": post_details.get("body", ""),
                    "link_flair_text": post.get("link_flair_text", ""),
                }
                
                # Return the post data to be added to Google Sheets
                return post_data
            else:
                print(f"Failed to scrape details for post: {post.get('title', 'Unknown')}")
                return None
        except Exception as e:
            print(f"Error processing post: {e}")
            return None

    def get_first_unprocessed_post(self, sheet_name):
        """
        Get the first unprocessed post from the specified sheet
        
        Args:
            sheet_name (str): Name of the sheet to get the post from
        
        Returns:
            dict: Post data or None if no unprocessed posts found
        """
        try:
            # Get the sheet - use the correct sheet_id from api_keys
            sheet = self.client.open_by_key(api_keys.GOOGLE_SHEET_ID_REDDIT_DATA).worksheet(sheet_name)
            
            # Get all values
            values = sheet.get_all_values()
            
            if len(values) <= 1:  # Only header row or empty
                return None
            
            # Get the header row
            headers = values[0]
            
            # Find the index of the "Status" column
            status_index = -1
            for i, header in enumerate(headers):
                if header.lower() == "status":
                    status_index = i
                    break
            
            # If no Status column found, assume the first row is unprocessed
            if status_index == -1:
                first_row = values[1]  # First row after header
            else:
                # Find the first row with empty status or status not "Completed"
                first_row = None
                for row in values[1:]:  # Skip header row
                    if status_index >= len(row) or not row[status_index] or row[status_index].lower() != "completed":
                        first_row = row
                        break
            
            if not first_row:
                return None
                
            # Convert to dictionary
            post_data = {}
            for i, header in enumerate(headers):
                if i < len(first_row):
                    post_data[header] = first_row[i]
                else:
                    post_data[header] = ""
                    
            return post_data
            
        except Exception as e:
            print(f"Error getting first unprocessed post: {e}")
            return None

    def mark_post_as_done(self, post_title, article_content, status="Completed"):
        """
        Mark a post as done in the sheet and save the generated article
        
        Args:
            post_title (str): Title of the post to mark as done
            article_content (str): Generated article content
            status (str): Status to set for the post
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the sheet - use the correct sheet_id from api_keys
            sheet = self.client.open_by_key(api_keys.GOOGLE_SHEET_ID_REDDIT_DATA).worksheet(api_keys.GOOGLE_SHEET_NAMES["REDDIT_DATA"])
            
            # Get all values
            values = sheet.get_all_values()
            
            if len(values) <= 1:  # Only header row or empty
                return False
            
            # Get the header row
            headers = values[0]
            
            # Find the indices of the relevant columns
            title_index = -1
            status_index = -1
            article_index = -1
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if header_lower == "title":
                    title_index = i
                elif header_lower == "status":
                    status_index = i
                elif header_lower == "article" or header_lower == "content" or header_lower == "article_content":
                    article_index = i
            
            if title_index == -1:
                print("Title column not found in sheet")
                return False
                
            # Find the row with the matching title
            row_index = -1
            for i, row in enumerate(values[1:], 2):  # Start from 2 to account for header row and 1-indexing
                if title_index < len(row) and row[title_index] == post_title:
                    row_index = i
                    break
                    
            if row_index == -1:
                print(f"Post with title '{post_title}' not found in sheet")
                return False
                
            # Update the status if status column exists
            if status_index != -1:
                sheet.update_cell(row_index, status_index + 1, status)  # +1 because sheets are 1-indexed
                
            # Update the article content if article column exists
            if article_index != -1:
                sheet.update_cell(row_index, article_index + 1, article_content)
            else:
                # If no article column exists, add one
                sheet.update_cell(1, len(headers) + 1, "Article_Content")
                sheet.update_cell(row_index, len(headers) + 1, article_content)
                
            print(f"Successfully marked post '{post_title}' as done and saved article content")
            return True
                
        except Exception as e:
            print(f"Error marking post as done: {e}")
            import traceback
            traceback.print_exc()
            return False











