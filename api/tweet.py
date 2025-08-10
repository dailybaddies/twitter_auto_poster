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
        image_urls = random_item["image_url"] 
        caption = random_item["caption"]    

        if not image_urls or not caption:
            return jsonify({"error": "Selected row is missing 'image_url' or 'caption'."}), 500

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
        
       # Split the comma-separated URLs and process each one
        image_urls = [url.strip() for url in image_urls.split(',')]
        media_ids = []

        for url in image_urls:
            try:
                image_response = requests.get(url)
                temp_file_path = f"/tmp/temp_image_{os.path.basename(url)}.jpg"
                
                with open(temp_file_path, "wb") as f:
                    f.write(image_response.content)

                media = api_v1.media_upload(filename=temp_file_path)
                media_ids.append(media.media_id)
            except Exception as e:
                # Log a warning and continue to the next image if one fails
                print(f"Warning: Failed to process image from URL: {url}. Details: {str(e)}")
        
        if not media_ids:
            return jsonify({"error": "No valid images were found to post."}), 500

        # Post the tweet with the caption and all media IDs
        client.create_tweet(text=caption, media_ids=media_ids)
        
        print(f"Successfully posted image from URL: image(s) with caption: {caption}")
        return jsonify({"message": "Tweet with image posted successfully!"}), 200
            
    except tweepy.TwitterServerError as e:
        print(f"Tweepy Error: {e}")
        return jsonify({"error": f"Error posting tweet: {str(e)}"}), 500
    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# New endpoint to add a post to the Google Sheet using an external API
@app.route("/api/add-to-sheet", methods=["GET"])
def add_to_sheet_handler():
    try:
        # Load request data from URL parameters
        post_id = request.args.get("url").split("/")[-1]
        custom_caption = request.args.get("caption")

        if not post_id:
            return jsonify({"error": "Missing 'id' in request parameters."}), 400

        # Call the external API to get tweet data
        external_api_url = f"https://api.brandbird.app/twitter/public/tweets/{post_id}"
        response = requests.get(external_api_url)
        response.raise_for_status()
        api_data = response.json()

        if not api_data["success"]:
            return jsonify({"error": "External API call failed."}), 500

        # Extract data from the API response
        tweet_data = api_data["tweet"]
        caption_to_use = custom_caption if custom_caption else tweet_data["text"]
        image_urls = ", ".join(tweet_data["images"])

        # Load Google Sheets credentials and append new data
        google_creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
        creds = json.loads(google_creds_json)
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open(os.environ.get("GOOGLE_SHEET_NAME"))
        worksheet = spreadsheet.sheet1
        
        # Append the new row to the spreadsheet
        worksheet.append_row([image_urls, caption_to_use])
        
        return jsonify({"message": f"Successfully added post to Google Sheet. Caption: {caption_to_use}, Image URLs: {image_urls}"}), 200

    except requests.exceptions.RequestException as e:
        print(f"External API Request Error: {e}")
        return jsonify({"error": f"Error calling external API: {str(e)}"}), 500
    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500