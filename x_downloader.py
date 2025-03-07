import os
import logging
import re
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
from dotenv import load_dotenv
from typing import Optional
import pytz  # Explicitly import pytz

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Get Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env file")

# Ensure downloads directory exists in project folder
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Detect if URL is from X (Twitter)
def detect_x_url(url: str) -> bool:
    return bool(re.search(r"x\.com|twitter\.com", url))

# Download and convert X video to MP4
def download_x_video(url: str) -> Optional[str]:
    output_path = os.path.join(DOWNLOAD_DIR, f"x_video_{os.urandom(4).hex()}.mp4")
    
    # yt-dlp options for X videos
    ydl_opts = {
        "outtmpl": output_path,
        "quiet": True,
        "merge_output_format": "mp4",  # Ensure MP4 output by merging if needed
        "postprocessors": [{  # Force MP4 conversion
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
        "format": "best[filesize<50M]/best",  # Prefer videos under 50MB, fall back to best available
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if not os.path.exists(output_path):
            logger.error(f"Download failed: File not found at {output_path}")
            return None
        
        # Check file size and compress if necessary
        if os.path.getsize(output_path) > 50 * 1024 * 1024:  # 50MB
            logger.warning("X video exceeds 50MB, attempting compression.")
            compressed_path = compress_video(output_path)
            if compressed_path:
                return compressed_path  # Return compressed path, original will be cleaned up
            else:
                if os.path.exists(output_path):
                    os.remove(output_path)
                return None
        return output_path
    
    except Exception as e:
        logger.error(f"Error downloading X video: {e}")
        if "format is not available" in str(e).lower():
            logger.info("Falling back to best available format for X video.")
            ydl_opts["format"] = "best"
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                if not os.path.exists(output_path):
                    logger.error(f"Fallback download failed: File not found at {output_path}")
                    return None
                if os.path.getsize(output_path) > 50 * 1024 * 1024:
                    logger.warning("X video still exceeds 50MB, attempting compression.")
                    compressed_path = compress_video(output_path)
                    if compressed_path:
                        return compressed_path
                    else:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        return None
                return output_path
            except Exception as e2:
                logger.error(f"Fallback download failed: {e2}")
        if os.path.exists(output_path):  # Cleanup on download failure
            os.remove(output_path)
        return None

# Compress video if over 50MB (ensures MP4 output)
def compress_video(input_path: str) -> Optional[str]:
    output_path = input_path.replace(".mp4", "_compressed.mp4")
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path, "-vf", "scale=-2:480",  # Resize to 480p
            "-c:v", "libx264", "-b:v", "1M", "-c:a", "aac", "-b:a", "128k",
            "-f", "mp4",  # Explicitly specify MP4 format
            "-y", output_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(output_path) and os.path.getsize(output_path) <= 50 * 1024 * 1024:
            if os.path.exists(input_path):  # Clean up original after successful compression
                os.remove(input_path)
            return output_path
        else:
            logger.error("Compression failed or file still too large.")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me an X (Twitter) URL containing a video, and I’ll download it for you!"
    )

# URL message handler
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    
    if not detect_x_url(url):
        await update.message.reply_text(
            "Please send a valid X (Twitter) URL containing a video."
        )
        return
    
    await update.message.reply_text("Downloading your X video... Please wait.")
    
    video_path = download_x_video(url)
    if video_path:
        try:
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(video=video_file)  # Removed timeout parameter
            logger.info("Sent X video to user.")
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            if "Timed out" in str(e):
                await update.message.reply_text(
                    "Upload timed out. The video might be too large or the network too slow. Try a smaller video."
                )
            else:
                await update.message.reply_text("Something went wrong while sending the video.")
        finally:
            # Clean up the file only after sending attempt (success or failure)
            if os.path.exists(video_path):
                os.remove(video_path)
    else:
        await update.message.reply_text("Sorry, I couldn’t download that X video. Check the URL and try again.")

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update.message:
        await update.message.reply_text("An error occurred. Please try again later.")

# Main function to run the bot
def main() -> None:
    # Set global timeouts and explicitly specify timezone using pytz
    default_timezone = pytz.timezone('UTC')  # Use UTC or your local timezone, e.g., 'America/Los_Angeles'
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(60).write_timeout(60).build()
    
    # Optionally configure JobQueue with pytz timezone
    application.job_queue.scheduler.configure(timezone=default_timezone)
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_error_handler(error)
    
    # Start the bot
    logger.info("Starting X Video Downloader bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
