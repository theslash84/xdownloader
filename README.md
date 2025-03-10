
# X (Twitter) Video Downloader Bot

This is a **Telegram bot** that allows users to **download videos from X (formerly Twitter)** by sending a video URL. The bot processes the video and sends it back to the user while ensuring it remains under 50MB.

## Features

✅ Detects and processes **X (Twitter) video URLs**  
✅ Downloads videos using `yt-dlp`  
✅ Compresses videos larger than **50MB** using `FFmpeg`  
✅ Sends videos directly to the user on Telegram  
✅ Handles errors and logs issues  

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/iraqitechs/xdownloader.git
   cd x-video-downloader-bot
   ```

2. **Create a `.env` file** with your Telegram bot token:  
   ```plaintext
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   LOG_LEVEL=INFO
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure `FFmpeg` is installed**  
   - On Ubuntu/Debian: `sudo apt install ffmpeg`
   - On Mac (Homebrew): `brew install ffmpeg`
   - On Windows: [Download FFmpeg](https://ffmpeg.org/download.html)

## Usage

1. **Run the bot**  
   ```bash
   python bot.py
   ```

2. **Send a Twitter (X) video URL to the bot on Telegram.**  
   The bot will download and send back the video.

## How It Works

1. The bot **detects** if a URL is from X (Twitter).
2. If valid, it **downloads** the video using `yt-dlp`.
3. If the file is **larger than 50MB**, it gets **compressed** to 480p.
4. The bot then **sends the video** to the user.
5. Temporary files are **cleaned up** after processing.

## Error Handling

- If the bot **fails to download**, it informs the user.
- If the video **exceeds Telegram's size limit**, it gets compressed.
- Logs are saved for debugging.

## Contributing

Feel free to open issues or contribute improvements!

## License

This project is licensed under the MIT License.
```
