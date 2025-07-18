import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys

STATUS_FILE = Path(__file__).parent / 'status.json'
COOKIES_DIR = Path(__file__).parent.parent / 'cookies'

PLATFORMS = {
    'youtube': {
        'url': 'https://www.youtube.com/',
        'cookie_file': COOKIES_DIR / 'youtube_cookies.txt',
        'login_selector': 'a[href*="/signin"]',
        'domain': '.youtube.com',
    },
    'facebook': {
        'url': 'https://www.facebook.com/',
        'cookie_file': COOKIES_DIR / 'facebook_cookies.txt',
        'login_selector': 'a[data-testid="open-registration-form-button"], input[name="email"]',
        'domain': '.facebook.com',
    },
    'instagram': {
        'url': 'https://www.instagram.com/',
        'cookie_file': COOKIES_DIR / 'instagram_cookies.txt',
        'login_selector': 'input[name="username"], a[href*="/accounts/login"]',
        'domain': '.instagram.com',
    },
}

def update_status(platform, login_required, cookie_expiry=None):
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)
        else:
            status = {}
    except Exception:
        status = {}
    status[platform] = {
        'login_required': login_required,
        'cookie_expiry': cookie_expiry or None
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def export_cookies(context, cookie_file, domain):
    cookies = context.cookies()
    with open(cookie_file, 'w', encoding='utf-8') as f:
        for cookie in cookies:
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            expires = int(cookie.get('expires', 0)) if cookie.get('expires') else 0
            secure = str(cookie.get('secure', 'FALSE')).upper()
            f.write(f"{domain}\tTRUE\t/\t{secure}\t{expires}\t{name}\t{value}\n")
    expiry = min([c.get('expires', 0) for c in cookies if c.get('expires')], default=None)
    return expiry

def check_platform(platform, headless=True):
    info = PLATFORMS[platform]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(info['url'])
        time.sleep(3)
        login_btn = page.query_selector(info['login_selector'])
        if login_btn:
            update_status(platform, True)
            print(f"Login required for {platform.title()}.")
        else:
            expiry = export_cookies(context, info['cookie_file'], info['domain'])
            update_status(platform, False, expiry)
            print(f"{platform.title()} cookies refreshed.")
        browser.close()

def main():
    headless = True
    if '--no-headless' in sys.argv:
        headless = False
    # Check all platforms
    for platform in PLATFORMS:
        check_platform(platform, headless=headless)
    # User tracking and scheduling can be added later

if __name__ == '__main__':
    main() 