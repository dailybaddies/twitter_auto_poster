import os
import random
import json
import tweepy
import gspread
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

# Load environment variables
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# This is the main function that will be executed
# It is now a Flask route instead of a generic handler
@app.route("/api/tweet", methods=["GET"])
def tweet_handler():
    try:
        # Load Twitter API keys
        consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
        consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
        access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            return jsonify({"error": "Missing Twitter API credentials."}), 500

        # Load Google Sheets credentials from an environment variable
        google_creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
        if not google_creds_json:
            return jsonify({"error": "Missing Google Sheets credentials."}), 500

        # Authenticate with Google Sheets
        creds = json.loads(google_creds_json)
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open(os.environ.get("GOOGLE_SHEET_NAME"))  # Use your sheet's name
        worksheet = spreadsheet.sheet1
        data = worksheet.get_all_records()

        if not data:
            return jsonify({"error": "The Google Sheet is empty."}), 500

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
        
        # Download image from URL
        image_response = requests.get(image_url)
        temp_file_path = "/tmp/temp_image.jpg"
        with open(temp_file_path, "wb") as f:
            f.write(image_response.content)

        # Upload media (using the temporary file)
        media = api_v1.media_upload(filename=temp_file_path)
        
        # Post the tweet with the media and caption
        client.create_tweet(text=caption, media_ids=[media.media_id])
        
        print(f"Successfully posted image from URL: {image_url} with caption: {caption}")
        return jsonify({"message": "Tweet with image posted successfully!"}), 200
            
    except tweepy.TwitterServerError as e:
        print(f"Tweepy Error: {e}")
        return jsonify({"error": f"Error posting tweet: {str(e)}"}), 500
    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
