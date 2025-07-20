from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import yt_dlp
import instaloader
import os
import logging
import json
from datetime import datetime
import tempfile
from pytube import YouTube
from playwright.sync_api import sync_playwright

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

INSTAGRAM_PLAYWRIGHT_SESSION = 'cookies/instagram_playwright_session.json'

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

INSTALOADER_SESSION_USER = 'damnnnsammy'
INSTALOADER_SESSION_FILE = 'cookies/instagram_session'

@app.route('/get-formats', methods=['POST'])
def get_formats():
    data = request.json if request.is_json else {}
    url = data.get('url') if isinstance(data, dict) else None
    platform = data.get('platform') if isinstance(data, dict) else None
    if not url or not platform:
        return jsonify({'error': 'Missing url or platform'}), 400
    try:
        if platform == 'youtube':
            yt = YouTube(url)
            formats = []
            for stream in yt.streams.filter(progressive=True):
                formats.append({
                    'format_id': stream.itag,
                    'ext': stream.subtype,
                    'resolution': stream.resolution,
                    'acodec': 'yes' if stream.includes_audio_track else 'no',
                    'vcodec': 'yes' if stream.includes_video_track else 'no',
                    'filesize': stream.filesize,
                    'format_note': 'progressive',
                })
            for stream in yt.streams.filter(only_audio=True):
                formats.append({
                    'format_id': stream.itag,
                    'ext': stream.subtype,
                    'resolution': '-',
                    'acodec': 'yes',
                    'vcodec': 'no',
                    'filesize': stream.filesize,
                    'format_note': 'audio only',
                })
            return jsonify({
                'title': yt.title,
                'thumbnail': yt.thumbnail_url,
                'formats': formats,
                'duration': yt.length,
                'uploader': yt.author,
                'webpage_url': url,
            })
        elif platform == 'facebook':
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
            available_format_ids = set()
            for f in info.get('formats', []) if isinstance(info, dict) and isinstance(info.get('formats', []), list) else []:
                if not isinstance(f, dict) or not f.get('url'):
                    continue
                format_id = f.get('format_id')
                available_format_ids.add(format_id)
                formats.append({
                    'format_id': format_id,
                    'ext': f.get('ext'),
                    'resolution': f.get('resolution') or f.get('height'),
                    'acodec': f.get('acodec'),
                    'vcodec': f.get('vcodec'),
                    'filesize': f.get('filesize') or f.get('filesize_approx'),
                    'format_note': f.get('format_note') if isinstance(f.get('format_note'), str) else '',
                })
            session['available_formats'] = list(available_format_ids)
            return jsonify({
                'title': info.get('title') if isinstance(info, dict) else None,
                'thumbnail': info.get('thumbnail') if isinstance(info, dict) else None,
                'formats': formats,
                'duration': info.get('duration') if isinstance(info, dict) else None,
                'uploader': info.get('uploader') if isinstance(info, dict) else None,
                'webpage_url': info.get('webpage_url') if isinstance(info, dict) else None,
            })
        elif platform == 'instagram':
            import instaloader
            shortcode = url.strip('/').split('/')[-1]
            L = instaloader.Instaloader(dirname_pattern='downloads', save_metadata=False)
            try:
                L.load_session_from_file(INSTALOADER_SESSION_USER, INSTALOADER_SESSION_FILE)
            except Exception as e:
                return jsonify({'error': f'Failed to load Instagram session: {str(e)}'}), 400

            try:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
            except Exception as e:
                return jsonify({'error': f'Failed to fetch Instagram post: {str(e)}'}), 500

            video_url = getattr(post, 'video_url', None)
            title = getattr(post, 'title', None) or 'Instagram Reel'
            thumbnail_url = getattr(post, 'url', None)
            return jsonify({
                'title': title,
                'thumbnail': thumbnail_url,
                'formats': [{
                    'format_id': 'default',
                    'ext': 'mp4',
                    'resolution': '-',
                    'acodec': 'unknown',
                    'vcodec': 'unknown',
                    'filesize': None,
                    'format_note': 'Instagram default',
                }],
                'duration': None,
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
        if platform == 'youtube':
            yt = YouTube(url)
            stream = yt.streams.get_by_itag(int(format_id))
            if not stream:
                return f'Error: Requested format {format_id} is not available for this video.', 400
            file_path = stream.download(output_path='downloads')
            file_name = os.path.basename(file_path)
            def generate():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
                os.remove(file_path)
            return Response(generate(), mimetype='application/octet-stream', headers={
                'Content-Disposition': f'attachment; filename="{file_name}"'
            })
        elif platform == 'facebook':
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
            import instaloader
            shortcode = url.strip('/').split('/')[-1]
            L = instaloader.Instaloader(dirname_pattern='downloads', save_metadata=False)
            try:
                L.load_session_from_file(INSTALOADER_SESSION_USER, INSTALOADER_SESSION_FILE)
            except Exception as e:
                return f'Failed to load Instagram session: {str(e)}', 400

            try:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
            except Exception as e:
                return f'Failed to fetch Instagram post: {str(e)}', 500

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
                    'Content-Disposition': f'attachment; filename="instagram_reel.mp3"'
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
                    'Content-Disposition': f'attachment; filename="instagram_reel.mp4"'
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
