import os
import random
import json
import tweepy
import gspread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Vercel handler function
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
        spreadsheet = gc.open("twitter_auto_poster_sheet")
        worksheet = spreadsheet.sheet1
        data = worksheet.get_all_records()

        if not data:
            return "Error: The Google Sheet is empty."

        # Select a random row from the spreadsheet
        random_item = random.choice(data)
        image_url = random_item["image_url"] # Assuming a column named 'image_url'
        caption = random_item["caption"]    # Assuming a column named 'caption'

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
        
        # Download image from URL
        # You'll need to add logic here to download the image from image_url
        # and save it to a temporary file for upload.
        # This part requires an additional library like requests.

        # Example (you need to implement this part):
        import requests
        r = requests.get(image_url, stream=True)
        image_file = 'temp_image.jpg'
        with open(image_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        # Upload media (using the temporary file)
        media = api_v1.media_upload(filename=image_file)

        # Post the tweet
        client.create_tweet(text=caption, media_ids=[media.media_id])

        print(f"Successfully posted: {caption} with image {image_url}")
        return f"Tweet posted successfully! {caption}"

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    print(handler(None, None))