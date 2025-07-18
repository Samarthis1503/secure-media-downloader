from flask import Flask, render_template, request, redirect, url_for, session, send_file
import yt_dlp
import instaloader
import os
import uuid
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
PASSWORD = 'samarth123'

# Ensure required folders exist
os.makedirs("downloads", exist_ok=True)

# Cookie paths
COOKIE_PATHS = {
    'youtube': 'cookies/youtube_cookies.txt',
    'facebook': 'cookies/facebook_cookies.txt',
}

logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Wrong password')
    return render_template('login.html')

@app.route('/home')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/youtube-mp3', methods=['POST'])
def youtube_mp3():
    url = request.form['url']
    file_id = str(uuid.uuid4())
    output_path = f"downloads/{file_id}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'downloads/{file_id}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    if os.path.exists(COOKIE_PATHS['youtube']):
        ydl_opts['cookiefile'] = COOKIE_PATHS['youtube']

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if not os.path.exists(output_path):
            logging.error(f"File not found after download: {output_path}")
            return render_template('error.html', error="Download failed: file not found.")
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        logging.exception("Error downloading YouTube MP3")
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route('/youtube-video', methods=['POST'])
def youtube_video():
    url = request.form['url']
    file_id = str(uuid.uuid4())
    output_path = f"downloads/{file_id}.mp4"

    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    if os.path.exists(COOKIE_PATHS['youtube']):
        ydl_opts['cookiefile'] = COOKIE_PATHS['youtube']

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if not os.path.exists(output_path):
            logging.error(f"File not found after download: {output_path}")
            return render_template('error.html', error="Download failed: file not found.")
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        logging.exception("Error downloading YouTube Video")
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route('/instagram-reel', methods=['POST'])
def instagram_reel():
    url = request.form['url']
    shortcode = url.strip('/').split("/")[-1]
    L = instaloader.Instaloader(dirname_pattern='downloads', save_metadata=False)
    session_file = 'cookies/instagram_cookies.txt'
    try:
        # Try to load session if available
        if os.path.exists(session_file):
            try:
                # Try to extract username from cookies file (Netscape format)
                with open(session_file, 'r') as f:
                    for line in f:
                        if 'ds_user_id' in line:
                            username = line.strip().split('\t')[-1]
                            break
                    else:
                        username = None
                if username:
                    L.load_session_from_file(username, session_file)
                    logging.info(f"Loaded Instagram session for {username}")
            except Exception as e:
                logging.warning(f"Could not load Instagram session: {e}")
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target='reel')
        for file in os.listdir("downloads/reel"):
            if file.endswith(".mp4"):
                return send_file(f"downloads/reel/{file}", as_attachment=True)
        logging.error("Video not found after download.")
        return render_template('error.html', error="Video not found.")
    except Exception as e:
        logging.exception("Error downloading Instagram Reel")
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route('/facebook-video', methods=['POST'])
def facebook_video():
    url = request.form['url']
    file_id = str(uuid.uuid4())
    output_path = f"downloads/{file_id}.mp4"

    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    if os.path.exists(COOKIE_PATHS['facebook']):
        ydl_opts['cookiefile'] = COOKIE_PATHS['facebook']

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if not os.path.exists(output_path):
            logging.error(f"File not found after download: {output_path}")
            return render_template('error.html', error="Download failed: file not found.")
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        logging.exception("Error downloading Facebook Video")
        return render_template('error.html', error=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
