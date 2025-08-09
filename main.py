import os
import requests
import telebot
from telebot import types
from flask import Flask, request
import yt_dlp
import re
from urllib.parse import urlparse
import uuid
import subprocess
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = '8331845686:AAEyAbX8uVzsV8P87JwEpF9eBlclb-w7sBQ'
WEBHOOK_URL = f'https://probable-sybilla-wwmahe-52df4f73.koyeb.app/{BOT_TOKEN}'
bot = telebot.TeleBot(BOT_TOKEN)

SUPPORTED_DOMAINS = [
    'youtube.com', 'youtu.be', 'instagram.com', 'instagr.am', 'tiktok.com',
    'twitter.com', 'x.com', 'facebook.com', 'fb.watch', 'reddit.com',
    'pinterest.com', 'pin.it', 'likee.video', 'snapchat.com', 'threads.net'
]

QUALITY_OPTIONS = {
    'youtube': ['best', '1080p', '720p', '480p', '360p'],
    'x': ['best', '720p', '480p'],
    'facebook': ['best', '720p', '480p']
}

def is_supported_url(url):
    try:
        domain = urlparse(url).netloc.lower()
        return any(supported in domain for supported in SUPPORTED_DOMAINS)
    except Exception as e:
        logging.error(f"Error checking URL: {str(e)}")
        return False

def get_platform(url):
    domain = urlparse(url).netloc.lower()
    if 'youtube.com' in domain or 'youtu.be' in domain:
        return 'youtube'
    elif 'x.com' in domain or 'twitter.com' in domain:
        return 'x'
    elif 'facebook.com' in domain or 'fb.watch' in domain:
        return 'facebook'
    return None

def expand_short_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        logging.error(f"Error expanding URL: {str(e)}")
        return url

def extract_video_info(url):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'format': 'best', 'listformats': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            return ydl.extract_info(url, download=False)
        except Exception as e:
            logging.error(f"Error extracting info: {str(e)}")
            return None

def get_available_formats(url):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'listformats': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            return [(f.get('format_id'), f.get('resolution', 'unknown')) for f in formats if f.get('vcodec') != 'none']
        except Exception as e:
            logging.error(f"Error getting formats: {str(e)}")
            return []

def download_and_process_video(url, quality='best', platform='youtube'):
    unique_id = str(uuid.uuid4())
    output_file = f'downloads/{unique_id}.%(ext)s'
    processed_file = f'downloads/{unique_id}_processed.mp4'
    format_string = 'best' if quality == 'best' else f'bestvideo[height<={quality[:-1]}]+bestaudio/best'
    
    ydl_opts = {
        'format': format_string,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_file,
        'merge_output_format': 'mp4',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        subprocess.run([
            'ffmpeg', '-i', filename, '-c:v', 'libx264', 
            '-preset', 'fast', '-c:a', 'aac', '-b:a', '192k',
            '-y', processed_file
        ], check=True, capture_output=True)
        
        if os.path.exists(processed_file):
            if os.path.exists(filename) and filename != processed_file:
                os.remove(filename)
            return processed_file, info
        return filename, info
        
    except Exception as e:
        logging.error(f"Error downloading: {str(e)}")
        return None, None

def clean_filename(filename):
    return re.sub(r'[^\w\-_. ]', '', filename)

def create_downloads_folder():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
🌟 *Video Downloader Bot* 🌟

📥 *Supported Platforms*:
🎥 YouTube (Videos & Shorts)
📸 Instagram (Posts, Reels, Stories)
🎶 TikTok
🐦 Twitter/X
📘 Facebook
📌 Reddit, Pinterest, Likee, Snapchat, Threads

🎨 *Features*:
- Choose video quality for YouTube, X, and Facebook
- Fast and reliable downloads
- Supports short links

📢 *How to Use*:
1️⃣ Send a video link
2️⃣ Select quality (if applicable)
3️⃣ Receive your video!

⚠️ *Note*: Private or restricted videos may not work.
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📚 Support", url="https://t.me/your_support_channel"))
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    text = expand_short_url(message.text)
    
    if not is_supported_url(text):
        bot.reply_to(message, "❌ *Invalid Link!* Please send a valid video URL from a supported platform.", parse_mode='Markdown')
        return

    processing_msg = bot.reply_to(message, "🔄 *Processing...* Please wait a moment.", parse_mode='Markdown')
    
    try:
        video_info = extract_video_info(text)
        if not video_info:
            bot.edit_message_text(
                "❌ *Oops!* Couldn’t fetch video details. The link might be invalid or restricted.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode='Markdown'
            )
            return

        platform = get_platform(text)
        if platform in ['youtube', 'x', 'facebook']:
            markup = types.InlineKeyboardMarkup(row_width=2)
            buttons = [
                types.InlineKeyboardButton(f"📽️ {quality}", callback_data=f"quality_{quality}_{text}")
                for quality in QUALITY_OPTIONS.get(platform, ['best'])
            ]
            markup.add(*buttons)
            
            bot.edit_message_text(
                f"🎬 *{video_info.get('title', 'Untitled Video')}*\n\n📏 *Select Quality*:",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        else:
            handle_download(message, text, 'best', platform, processing_msg)

    except Exception as e:
        logging.error(f"Error processing: {str(e)}")
        bot.edit_message_text(
            f"❌ *Error*: {str(e)}\nTry again or contact support.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('quality_'))
def handle_quality_selection(call):
    try:
        _, quality, url = call.data.split('_', 2)
        platform = get_platform(url)
        
        bot.edit_message_text(
            "⬇️ *Downloading...* This may take a moment.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
        
        handle_download(call.message, url, quality, platform, call.message)
        
    except Exception as e:
        logging.error(f"Error in quality selection: {str(e)}")
        bot.edit_message_text(
            f"❌ *Error*: {str(e)}\nPlease try again.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )

def handle_download(message, url, quality, platform, processing_msg):
    try:
        create_downloads_folder()
        video_path, video_info = download_and_process_video(url, quality, platform)

        if not video_path or not os.path.exists(video_path):
            bot.edit_message_text(
                "❌ *Failed!* The video might be unavailable or too large.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode='Markdown'
            )
            return

        title = video_info.get('title', 'Untitled Video')
        duration = video_info.get('duration', 0)
        uploader = video_info.get('uploader', 'Unknown')

        with open(video_path, 'rb') as video_file:
            bot.send_video(
                message.chat.id,
                video_file,
                caption=f"🎬 *{title}*\n⏳ Duration: {duration}s\n👤 Uploader: {uploader}\n📏 Quality: {quality}\n\n✅ *Downloaded by @{bot.get_me().username}*",
                parse_mode='Markdown',
                reply_to_message_id=message.message_id
            )

        bot.delete_message(message.chat.id, processing_msg.message_id)

        try:
            os.remove(video_path)
        except Exception as e:
            logging.error(f"Error cleaning file: {str(e)}")

    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        bot.edit_message_text(
            f"❌ *Failed*: {str(e)}\nCheck the link or try again later.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            parse_mode='Markdown'
        )

@app.route('/')
def index():
    return "✅ *Bot is online!*", 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return f"Webhook Error: {str(e)}", 500

if __name__ == "__main__":
    create_downloads_folder()
    try:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        logging.info(f"✅ Webhook set: {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Webhook setup failed: {str(e)}")
    app.run(host="0.0.0.0", port=8080)
