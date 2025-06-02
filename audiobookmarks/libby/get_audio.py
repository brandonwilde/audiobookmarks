import json
import os
import re
import time
from typing import List
import requests

from playwright.async_api import async_playwright
from playwright.async_api import Page

from audiobookmarks.models import LibbyBookDataTree


BROWSER_DATA_DIRECTORY = os.environ.get("BROWSER_DATA_DIRECTORY", "./user_data")

# If running in debug mode, first run the following command in the terminal:
# google-chrome --remote-debugging-port=9222

# audio files with a low start byte (5 digits) are usually the full chapter (minus the chapter number and title)
# others are bookmarks (plus 2-3 seconds before the bookmark)

async def start_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIRECTORY,  # Specify a directory to store user data
            headless=False,
            args=["--remote-debugging-port=9222"]
        )
        page = await browser.new_page()
        await page.goto("https://www.libbyapp.com/")


def remove_punctuation(text):
    remove_punc = str.maketrans('','',':/=;-.')
    return text.translate(remove_punc)


async def download_audio_file(audio_url, headers, tag='', dir_path=''):
    '''
    Downloads the audio file from the given URL.
    '''

    response = requests.get(audio_url, headers=headers)
    if 200 <= response.status_code < 300:
        file_name = f"audio_file_{tag}.mp3"
        if os.path.exists(file_name):
            file_name = f"audio_file_{tag}_a.mp3"
            if os.path.exists(file_name):
                file_name = f"audio_file_{tag}_b.mp3"
                if os.path.exists(file_name):
                    file_name = f"audio_file_{tag}_extra.mp3"
        with open(os.path.join(dir_path, file_name), "wb") as f:
            f.write(response.content)
        print(file_name, flush=True)
    else:
        print(f"Failed to download audio file. Status code: {response.status_code}", flush=True)


async def get_bookmarks(context, page: Page, book: LibbyBookDataTree):
    '''
    Get bookmarks data for an audiobook.
    '''

    async def intercept_response(response):
        '''
        Intercepts network responses to get the bookmarks JSON.'''
        
        if "libbyjourney" in response.url:
            response_body = response.request.post_data_json
            if response_body and 'value' in response_body:
                with open(book.file, "w") as f:
                    json.dump(response_body['value'], f)

    page.on("response", intercept_response)

    # Open list of borrowed books (tag is an emoji)
    await page.goto("https://libbyapp.com/tags/tag/%F0%9F%A7%BE")

    title_split = book.title.split(' ') # may need to be changed
    regex = re.compile('.*' + '.*'.join(title_split) + '.*', re.IGNORECASE)
    book_mentions = page.get_by_text(regex)

    try:
        await book_mentions.last.click()
    except:
        raise Exception("Book not found. Please make sure you have entered the title exactly as it appears in Libby.")

    if 'open/loan' in page.url:
        title_id = page.url.split('/')[-1]
        await page.goto(f"https://libbyapp.com/tags/similar-{title_id}/page-1/{title_id}")

    # Download bookmarks
    journey = await page.query_selector("button[class=\"title-journey-preview-button shibui-button halo\"]")
    await journey.click()
    actions = page.get_by_role('button', name='Actions', exact=True)
    await actions.click()
    buttons = await page.get_by_role('button').all()
    await buttons[1].click()

    try:
        # needed in order to capture response, but doesn't exit gracefully
        async with context.expect_page():
            await page.get_by_text("JSON").click()
    except:
        pass


async def download_audiobookmarks(page: Page, book: LibbyBookDataTree):
    '''
    Downloads the audio file for each bookmark.
    '''

    with open(book.file, "r") as f:
        bookmarks_data = json.load(f)

    title_data = bookmarks_data['readingJourney']['title']
    title_id = title_data['titleId']
    try:
        bookmarks = bookmarks_data['bookmarks']
    except:
        raise Exception(f"No bookmarks found. Are you sure you placed bookmarks in \"{title_data['text']}\"?")
    bookmark_list = sorted(bookmarks, key=lambda x: x['percent'])

    # Open the target book
    await page.goto(f"https://libbyapp.com/tags/similar-{title_id}/page-1/{title_id}")       

    # Open the audiobook player
    actions = await page.query_selector("ul[class=\"title-details-actions-list\"]")
    open_book = await actions.query_selector("li:nth-child(2)")
    await open_book.click()

    try:
        await page.wait_for_selector("iframe")
        print("Page loaded.", flush=True)
    except:
        raise Exception("Failed to load audiobook player.")

    iframe_element = await page.query_selector("iframe")
    iframe = await iframe_element.content_frame()

    # close synchronization pop-up if it exists
    try:
        print("Checking for pop-up.", flush=True)
        popup = await iframe.query_selector("button[class=\"notifier-close-button halo\"]")
        if not await popup.get_attribute('aria-hidden') == 'true':
            print("Pop-up found.", flush=True)
            await popup.click()
    except:
        print("No pop-up found.", flush=True)
        pass

    async def get_bookmarks():
        return await iframe.query_selector_all("li[class=\"marks-dialog-mark data-mark-type_bookmark data-mark-color_none halos-anchor\"]")

    async def select_bookmark(open_bms, num, bm_info:List[dict]):
        '''
        Retrieves a bookmark's chapter number and position within chapter.
        Also triggers the audio file request.
        '''
        bookmark_popup = await iframe.query_selector("div[class=\"navigation-shades\"]")
        if not await bookmark_popup.text_content():
            await open_bms.click()
        bookmarks = await get_bookmarks()

        bookmark = bookmarks[num-1]
        print(f"Clicked bookmark {num}.", flush=True)
        await bookmark.click()
        time.sleep(5)
        chapter = await iframe.query_selector("div[class=\"chapter-bar-title\"]")
        chapter_num = await chapter.text_content()
        prog_in_chapter = await iframe.query_selector("span[class=\"chapter-bar-prev-text\"]")
        prog_text = await prog_in_chapter.text_content()
        min_remaining = await iframe.query_selector("span[class=\"chapter-bar-next-text\"]")
        min_remaining_text = await min_remaining.text_content()
        
        # Could also get minutes remaining in chapter here, calculate progress percentage

        bookmark_info = {
            "bookmark_num": num,
            "chapter_num": chapter_num,
            "minutes_in": prog_text.lower(),
            "minutes_remaining": min_remaining_text.lower()
        }
        bm_info[num-1].update(bookmark_info)

        print(f"Bookmark {num}: {chapter_num}, {prog_text.lower()} in.", flush=True)
        print(flush=True)

        return bm_info
    
    bookmarks_button = await iframe.query_selector("button[class=\"nav-action-item-button halo\"]")
    await bookmarks_button.click()
    
    bookmarks = await get_bookmarks()
    assert len(bookmarks) == len(bookmark_list), "Number of bookmarks do not match."
    
    # audio_dir = os.path.join(download_dir, "audio")
    if not os.path.exists(book.audio_dir):
        os.makedirs(book.audio_dir)

    bookmark_num = -1 # dummy value

    async def intercept_audio(route, request):
        '''
        Intercepts the audio file requests and downloads them.
        '''
        nonlocal bookmark_num

        audio_url = request.url
        headers = request.headers

        await download_audio_file(audio_url, headers, bookmark_num, dir_path=book.audio_dir)
        await route.continue_()

    # Intercept network requests
    await page.route("**://*audioclips*/**", intercept_audio)
    time.sleep(5)

    for bookmark_num in range(1,len(bookmarks)+1):
        bookmark_list = await select_bookmark(bookmarks_button, bookmark_num, bookmark_list)

    # Get bookmarks missed for whatever reason
    # This often happens because bookmarks are too close together and so a new audio file wasn't fetched.
    bookmark_num = 1
    bookmark_list = await select_bookmark(bookmarks_button, bookmark_num, bookmark_list)
    for bookmark_num in range(len(bookmarks),0,-1):
        if not os.path.exists(os.path.join(book.audio_dir, f"audio_file_{bookmark_num}.mp3")):
            bookmark_list = await select_bookmark(bookmarks_button, bookmark_num, bookmark_list)

    return bookmark_list

async def get_audiobookmarks(book: LibbyBookDataTree, debug: bool = False):
    # Fetches bookmark data from libby
    async with async_playwright() as p:
        browser = None
        if debug:
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                print("Connected to existing browser: ", browser, flush=True)
                context = browser.contexts[0]
            except Exception as e:
                print("No open debug browser detected. Will run with visible browser, but if you would like the browser to persist between runs, start the debug browser with `google-chrome --remote-debugging-port=9222`")
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=BROWSER_DATA_DIRECTORY,
                    headless=False,
                )
        else:
            print(f"Launching browser with user data directory: {BROWSER_DATA_DIRECTORY}")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_DIRECTORY,  # Specify a directory to store user data
                headless=True,
            )
        context.set_default_timeout(7000)
        page = context.pages[0]

        await page.goto("https://libbyapp.com/", wait_until="networkidle")

        # Will redirect to libbyapp.com/shelf if logged in. Wait for redirect.
        print("URL: ", page.url, flush=True)
        if "shelf" not in page.url:
            logged_in = input("It looks like you are not logged in. Please log in and hit enter once you are in.")

        await get_bookmarks(context, page, book)

        bookmark_list = await download_audiobookmarks(page, book)

        # Close the browser or context properly
        if browser:
            await browser.close()
        else:
            await context.close()

    with open(book.file, "r") as f:
        bookmarks_data = json.load(f)

    bookmarks_data['bookmarks'] = bookmark_list
    with open(book.updated_file, "w") as f:
        json.dump(bookmarks_data, f, indent=4)

    return bookmark_list


# # Util for debugging
# def get_structure(element):
#     structure = element.evaluate('''() => {
#         const getElementInfo = (element) => {
#             return {
#                 tagName: element.tagName,
#                 className: element.className,
#                 id: element.id,
#                 innerText: element.innerText,
#                 children: Array.from(element.children).map(getElementInfo)
#             };
#         };
#         return getElementInfo(document.body);
#     }''')
#     return structure