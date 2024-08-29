import os
import time
from typing import List
import requests

from playwright.async_api import async_playwright

BROWSER_DATA_DIRECTORY = os.environ.get("BROWSER_DATA_DIRECTORY", "./user_data")

# First run the following command in the terminal:
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


async def get_audiobookmarks(title_id='', bookmark_list=[], download_dir=''):
    # First run the following command in the terminal:
    # google-chrome --remote-debugging-port=9222
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        context.set_default_timeout(7000)
        page = context.pages[0]

        bookmark_num = -1 # dummy value
        async def intercept_audio(route, request):
            '''
            Intercepts the audio file requests and downloads them.
            '''
            nonlocal bookmark_num

            audio_url = request.url
            headers = request.headers

            await download_audio_file(audio_url, headers, bookmark_num, dir_path=download_dir)
            await route.continue_()

        # Open the target book
        await page.goto(f"https://libbyapp.com/tags/similar-{title_id}/page-1/{title_id}")       

        # Open the audiobook player
        actions = await page.query_selector("ul[class=\"title-details-actions-list\"]")
        open_book = await actions.query_selector("li:nth-child(2)")
        await open_book.click()

        await page.wait_for_selector("iframe")
        print("Page loaded.", flush=True)

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

            bookmark_info = {
                "bookmark_num": num,
                "chapter_num": chapter_num,
                "minutes_in": prog_text.lower(),
            }
            bm_info[num-1].update(bookmark_info)

            print(f"Bookmark {num}: {chapter_num}, {prog_text.lower()} in.", flush=True)
            print(flush=True)

            return bm_info
        
        bookmarks_button = await iframe.query_selector("button[class=\"nav-action-item-button halo\"]")
        await bookmarks_button.click()
        
        bookmarks = await get_bookmarks()
        assert len(bookmarks) == len(bookmark_list), "Number of bookmarks do not match."

        # Intercept network requests
        await page.route("**://*mediaclips*/**", intercept_audio)
        time.sleep(5)

        for bookmark_num in range(1,len(bookmarks)+1):
            bookmark_list = await select_bookmark(bookmarks_button, bookmark_num, bookmark_list)

        # Get bookmarks missed for whatever reason
        for bookmark_num in range(len(bookmarks),0,-1):
            if not os.path.exists(os.path.join(download_dir, f"audio_file_{bookmark_num}.mp3")):
                bookmark_list = await select_bookmark(bookmarks_button, bookmark_num, bookmark_list)

        # Close the browser
        await browser.close()

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