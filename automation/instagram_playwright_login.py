import asyncio
from playwright.sync_api import sync_playwright
import json
import os

INSTAGRAM_USERNAME = input('Enter your Instagram username: ')
INSTAGRAM_PASSWORD = input('Enter your Instagram password: ')
SESSION_FILE = os.path.join(os.path.dirname(__file__), '../cookies/instagram_playwright_session.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://www.instagram.com/accounts/login/')
    page.wait_for_selector('input[name="username"]', timeout=20000)
    page.fill('input[name="username"]', INSTAGRAM_USERNAME)
    page.fill('input[name="password"]', INSTAGRAM_PASSWORD)
    page.press('input[name="password"]', 'Enter')
    # Wait for the home icon or profile icon to appear (indicates successful login)
    try:
        page.wait_for_selector('svg[aria-label="Home"], svg[aria-label="Profile"]', timeout=30000)
        # Save session as soon as login is successful
        context.storage_state(path=SESSION_FILE)
        print(f'Instagram session saved to {SESSION_FILE}')
    except Exception as e:
        print('Login may have failed or took too long:', e)
    browser.close() 