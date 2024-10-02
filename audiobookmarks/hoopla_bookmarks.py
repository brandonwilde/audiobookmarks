import json
import os
import re

from playwright.sync_api import sync_playwright

BROWSER_DATA_DIRECTORY = os.environ.get("BROWSER_DATA_DIRECTORY", "./user_data")
DEBUG_MODE = False if os.environ.get("DEBUG_MODE",'false').lower() not in ['true','t','yes','y'] else True
NOTES_DIRECTORY = os.environ.get("NOTES_DIRECTORY", "")

# If running in debug mode, first run the following command in the terminal:
# google-chrome --remote-debugging-port=9222

data_directory = "data"
book_name = "what_iranians_want"
book_dir = os.path.join(data_directory, book_name)
book_audio_dir = os.path.join(book_dir, "audio")
book_file_name = book_name + ".json"
book_file = os.path.join(book_dir, book_file_name)
updated_file = book_file.replace(".json", "_updated.json")

if not os.path.exists(book_dir):
    os.makedirs(book_dir)


def get_bookmarks(title='', download_dir=''):
    '''
    Get bookmarks data for an audiobook.
    '''
    with sync_playwright() as p:
        if DEBUG_MODE:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
        else:
            context = p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_DIRECTORY,  # Specify a directory to store user data
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
                with open(os.path.join(download_dir, f"{title}_{data_type}.json"), "w") as f:
                    json.dump(response_body, f)
                
                if data_type == "bookmarks":
                    print("Found 'em!")

        page.on("response", intercept_response)

        page.goto("https://www.hoopladigital.com/my/borrowed", timeout=10000)
        page.wait_for_selector("text=TERMS AND CONDITIONS OF USE")
        page.click("text=ACCEPT")

        page.wait_for_selector(f'text=Currently Borrowed')

        # Get audiobook links
        book_name_split = title.split('_')
        regex = re.compile('.*' + '.*'.join(book_name_split) + '.*', re.IGNORECASE)
        book_tile = page.get_by_text(regex)
        book_tile.click()

        play_button = page.get_by_text(re.compile('play|resume', re.IGNORECASE))
        play_button.click()

        page.get_by_role('button', name='Expand').click()

        page.get_by_role('button', name='Bookmarks Menu').click()



get_bookmarks(
    title='what_iranians_want',
    download_dir=book_dir
)