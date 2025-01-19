import json
import os
import re
import time

from playwright.sync_api import sync_playwright

from audiobookmarks.models import HooplaBookDataTree

BROWSER_DATA_DIRECTORY = os.environ.get("BROWSER_DATA_DIRECTORY", "./user_data")
HOOPLA_USERNAME = os.environ.get("HOOPLA_USERNAME")
HOOPLA_PASSWORD = os.environ.get("HOOPLA_PASSWORD")


def get_bookmarks(book: HooplaBookDataTree, debug: bool = False):
    '''
    Get bookmarks data for an audiobook.
    '''
    with sync_playwright() as p:
        if debug:
            try:
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                context = browser.contexts[0]
            except Exception as e:
                print("No open debug browser detected. Will run with visible browser, but if you would like the browser to persist between runs, first start the debug browser in another terminal with `google-chrome --remote-debugging-port=9222`")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=BROWSER_DATA_DIRECTORY,
                    headless=False,
                )
        else:
            context = p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_DIRECTORY,
                headless=True,
            )
        context.set_default_timeout(7000)
        page = context.pages[0]

        def intercept_response(response):
            '''
            Intercepts network responses to get the audio file.'''
            
            if "graphql" in response.url:
                response_body = response.json()
                data_type = list(response_body['data'].keys())[0]
                if data_type == 'bookmarks':
                    file_path = book.bookmarks_file
                elif data_type == 'title':
                    file_path = book.title_file
                else:
                    return
                with open(file_path, "w") as f:
                    json.dump(response_body, f)

        def handle_page_load(response):
            nonlocal app_start_time, on_login_page
            if response.url == "https://analytics.hoopladigital.com/patron/event":
                try:
                    body = response.request.post_data_json
                    if body.get('interactionType') == 'APP_START':
                        app_start_time = time.time()
                    elif body.get('interactionType') == 'PAGE_LOAD':
                        on_login_page = 'login' in body.get('url')
                except Exception:
                    pass

        def navigate_and_login():
            print("Navigating to Hoopla...", flush=True)
            page.goto("https://www.hoopladigital.com/my/borrowed")
            page_load_timeout = 5.0
            while app_start_time is None or (time.time() - app_start_time < page_load_timeout and not on_login_page):
                page.wait_for_timeout(100)
            if on_login_page:
                print("Logging in...", flush=True)
                page.fill('input[name="email"]', HOOPLA_USERNAME)
                page.fill('input[name="password"]', HOOPLA_PASSWORD)
                page.click('button[type="submit"]')
                print("Navigating to books...", flush=True)
                page.wait_for_url("**/my/borrowed", wait_until="domcontentloaded")

        app_start_time = None
        on_login_page = False
        page.on("response", intercept_response)
        page.on("response", handle_page_load)
        navigate_and_login()

        try:
            page.wait_for_selector("text=TERMS AND CONDITIONS OF USE")
            page.click("text=ACCEPT")
        except:
            pass

        page.wait_for_selector(f'text=Currently Borrowed')

        # Get audiobook links
        book_name_split = book.title.split(' ')
        regex = re.compile('.*' + '.*'.join(book_name_split) + '.*', re.IGNORECASE)
        book_tile = page.get_by_text(regex)
        print("Getting book details...", flush=True)
        book_tile.click()

        play_button = page.get_by_text(re.compile('^play$|^resume$', re.IGNORECASE))
        play_button.click()

        page.get_by_role('button', name='Expand').click()

        print("Getting bookmarks...", flush=True)
        page.get_by_role('button', name='Bookmarks Menu').click()
