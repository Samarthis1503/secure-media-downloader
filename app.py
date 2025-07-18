from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import yt_dlp
import instaloader
import os
import logging
import json
from datetime import datetime
import tempfile

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

def datetimeformat(value):
    if not value:
        return "Unknown"
    try:
        return datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(value)

app.jinja_env.filters['datetimeformat'] = datetimeformat

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

@app.route('/get-formats', methods=['POST'])
def get_formats():
    data = request.json if request.is_json else {}
    url = data.get('url') if isinstance(data, dict) else None
    platform = data.get('platform') if isinstance(data, dict) else None
    if not url or not platform:
        return jsonify({'error': 'Missing url or platform'}), 400
    try:
        if platform in ['youtube', 'facebook']:
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'forcejson': True,
                'extract_flat': False,
            }
            cookie_path = COOKIE_PATHS.get(platform, '')
            if cookie_path and os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path  # type: ignore
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get('formats', []) if isinstance(info, dict) and isinstance(info.get('formats', []), list) else []:
                if not isinstance(f, dict) or not f.get('url'):
                    continue
                # Ensure all fields are correct type
                formats.append({
                    'format_id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'resolution': f.get('resolution') or f.get('height'),
                    'acodec': f.get('acodec'),
                    'vcodec': f.get('vcodec'),
                    'filesize': f.get('filesize') or f.get('filesize_approx'),
                    'format_note': f.get('format_note') if isinstance(f.get('format_note'), str) else '',
                })
            return jsonify({
                'title': info.get('title') if isinstance(info, dict) else None,
                'thumbnail': info.get('thumbnail') if isinstance(info, dict) else None,
                'formats': formats,
                'duration': info.get('duration') if isinstance(info, dict) else None,
                'uploader': info.get('uploader') if isinstance(info, dict) else None,
                'webpage_url': info.get('webpage_url') if isinstance(info, dict) else None,
            })
        elif platform == 'instagram':
            shortcode = url.strip('/').split('/')[-1]
            L = instaloader.Instaloader(dirname_pattern='downloads', save_metadata=False)
            session_file = 'cookies/instagram_cookies.txt'
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r') as f:
                        for line in f:
                            if 'ds_user_id' in line:
                                username = line.strip().split('\t')[-1]
                                break
                        else:
                            username = None
                    if username:
                        L.load_session_from_file(username, session_file)
                except Exception:
                    pass
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            video_url = getattr(post, 'video_url', None)
            video_height = getattr(post, 'video_height', None)
            video_duration = getattr(post, 'video_duration', None)
            return jsonify({
                'title': getattr(post, 'title', None) or 'Instagram Reel',
                'thumbnail': getattr(post, 'url', None),
                'formats': [{
                    'format_id': 'default',
                    'ext': 'mp4',
                    'resolution': f'{video_height}p' if video_height else '-',
                    'acodec': 'unknown',
                    'vcodec': 'unknown',
                    'filesize': getattr(post, 'video_view_count', None),
                    'format_note': 'Instagram default',
                }],
                'duration': video_duration,
                'uploader': getattr(post, 'owner_username', None),
                'webpage_url': url,
                'video_url': video_url,
            })
        else:
            return jsonify({'error': 'Unsupported platform'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json if request.is_json else {}
    url = data.get('url') if isinstance(data, dict) else None
    platform = data.get('platform') if isinstance(data, dict) else None
    format_id = data.get('format') if isinstance(data, dict) else None
    if not url or not platform or not format_id:
        return 'Missing parameters', 400
    try:
        if platform in ['youtube', 'facebook']:
            ydl_opts = {
                'format': 'bestaudio/best' if format_id == 'mp3' else format_id,
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'quiet': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            }
            cookie_path = COOKIE_PATHS.get(platform, '')
            if cookie_path and os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path
            if format_id == 'mp3':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ext = 'mp3' if format_id == 'mp3' else (info['ext'] if isinstance(info, dict) and 'ext' in info else 'mp4')
                file_id = info['id'] if isinstance(info, dict) and 'id' in info else 'video'
                output_path = f'downloads/{file_id}.{ext}'
            def generate():
                with open(output_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
                os.remove(output_path)
            return Response(generate(), mimetype='application/octet-stream', headers={
                'Content-Disposition': f'attachment; filename="{file_id}.{ext}"'
            })
        elif platform == 'instagram':
            shortcode = url.strip('/').split('/')[-1]
            L = instaloader.Instaloader(dirname_pattern='downloads', save_metadata=False)
            session_file = 'cookies/instagram_cookies.txt'
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r') as f:
                        for line in f:
                            if 'ds_user_id' in line:
                                username = line.strip().split('\t')[-1]
                                break
                        else:
                            username = None
                    if username:
                        L.load_session_from_file(username, session_file)
                except Exception:
                    pass
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            video_url = getattr(post, 'video_url', None)
            if not video_url:
                return 'Video URL not found', 404
            import requests
            r = requests.get(video_url, stream=True)
            ext = 'mp4'
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        tmp.write(chunk)
                tmp_path = tmp.name
            if format_id == 'mp3':
                import subprocess
                mp3_path = tmp_path.replace('.mp4', '.mp3')
                subprocess.run(['ffmpeg', '-i', tmp_path, '-vn', '-ab', '128k', '-ar', '44100', '-y', mp3_path])
                os.remove(tmp_path)
                def generate():
                    with open(mp3_path, 'rb') as f:
                        while True:
                            chunk = f.read(8192)
                            if not chunk:
                                break
                            yield chunk
                    os.remove(mp3_path)
                return Response(generate(), mimetype='audio/mpeg', headers={
                    'Content-Disposition': f'attachment; filename="{shortcode}.mp3"'
                })
            else:
                def generate():
                    with open(tmp_path, 'rb') as f:
                        while True:
                            chunk = f.read(8192)
                            if not chunk:
                                break
                            yield chunk
                    os.remove(tmp_path)
                return Response(generate(), mimetype='video/mp4', headers={
                    'Content-Disposition': f'attachment; filename="{shortcode}.mp4"'
                })
        else:
            return 'Unsupported platform', 400
    except Exception as e:
        return f'Error: {str(e)}', 500

@app.route('/admin')
def admin_dashboard():
    try:
        with open('automation/status.json', 'r') as f:
            status = json.load(f)
    except Exception:
        status = {}
    return render_template('admin_dashboard.html', status=status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
