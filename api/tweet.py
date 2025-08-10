import os
import random
import json
import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def handler(request, response):
    try:
        # Load Twitter API keys
        consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
        consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
        access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            return "Error: Missing Twitter API credentials."

        # Load Google Sheets credentials from an environment variable
        google_creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
        if not google_creds_json:
            return "Error: Missing Google Sheets credentials."

        # Authenticate with Google Sheets
        creds = json.loads(google_creds_json)
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open("TwitterBotContent") # Use your sheet's name
        worksheet = spreadsheet.sheet1
        data = worksheet.get_all_records()

        if not data:
            return "Error: The Google Sheet is empty."

        # Select a random row from the spreadsheet
        random_item = random.choice(data)
        image_url = random_item["image_url"] 
        caption = random_item["caption"]    

        # Authenticate with Twitter
        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        auth_v1 = tweepy.OAuth1UserHandler(
            consumer_key, consumer_secret, access_token, access_token_secret
        )
        api_v1 = tweepy.API(auth_v1)
        
        # Download image from URL (requires the 'requests' library)
        import requests
        image_response = requests.get(image_url)
        temp_file_path = "/tmp/temp_image.jpg"
        with open(temp_file_path, "wb") as f:
            f.write(image_response.content)

        # Upload media (using the temporary file)
        media = api_v1.media_upload(filename=temp_file_path)
        
        # Post the tweet with the media and caption
        client.create_tweet(text=caption, media_ids=[media.media_id])
        
        print(f"Successfully posted image from URL: {image_url} with caption: {caption}")
        return f"Tweet with image posted successfully!"
            
    except tweepy.TweepError as e:
        print(f"Tweepy Error: {e}")
        return f"Error posting tweet: {e}"
    except Exception as e:
        print(f"General Error: {e}")
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    handler(None, None)