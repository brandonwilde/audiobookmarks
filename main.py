import asyncio
import json
import os
import time
import requests

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from tabulate import tabulate


# First run the following command in the terminal:
# google-chrome --remote-debugging-port=9222

# audio files with a low start byte (5 digits) are usually the full chapter (minus the chapter number and title)
# others are bookmarks (plus 2-3 seconds before the bookmark)

async def start_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="/home/brandon/Projects/audiobookmarks/user_data",  # Specify a directory to store user data
            headless=False,
            args=["--remote-debugging-port=9222"]
        )
        page = await browser.new_page()
        await page.goto("https://www.libbyapp.com/")


def remove_punctuation(text):
    remove_punc = str.maketrans('','',':/=;-.')
    return text.translate(remove_punc)


async def download_audio_file(audio_url, headers, tag=''):
    response = requests.get(audio_url, headers=headers)
    # tag = remove_punctuation(audio_url)[-10:]
    if 200 <= response.status_code < 300:
        file_name = f"audio_file_{tag}.mp3"
        if os.path.exists(file_name):
            file_name = f"audio_file_{tag}_a.mp3"
            if os.path.exists(file_name):
                file_name = f"audio_file_{tag}_b.mp3"
                if os.path.exists(file_name):
                    file_name = f"audio_file_{tag}_c.mp3"
                    if os.path.exists(file_name):
                        file_name = f"audio_file_{tag}_extra.mp3"
        with open(file_name, "wb") as f:
            f.write(response.content)
              
        # Requested content range
        q_content_range = headers['range']
        q_byte_range = q_content_range.split('=')[1]
        q_start_byte, q_end_byte = q_byte_range.split('-')
        q_start_byte, q_end_byte = int(q_start_byte) if q_start_byte else '', int(q_end_byte) if q_end_byte else ''

        # Received content range
        content_range = response.headers['content-range']
        range_info, total_size = content_range.split('/')
        byte_range = range_info.split(' ')[1]
        start_byte, end_byte = map(int, byte_range.split('-'))
        total_size = int(total_size)
        byte_data = [
            ["Req/Rec", "Start", "End", "Total"],
            ["Requested", q_start_byte, q_end_byte, ''],
            ["Received", start_byte, end_byte, total_size]
        ]
        print(file_name, flush=True)
        # print(tabulate(byte_data), flush=True)
        pass
    else:
        print(f"Failed to download audio file. Status code: {response.status_code}", flush=True)


async def get_audiobookmarks(title_id='', bookmark_list=[]):
    # First run the following command in the terminal:
    # google-chrome --remote-debugging-port=9222
     async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]  # Get the first context
        context.set_default_timeout(7000)
        page = context.pages[0]  # Get the first page

        bookmark_num = -1

        async def handle_request(route, request):
            nonlocal bookmark_num

            audio_url = request.url
            headers = request.headers

            await download_audio_file(audio_url, headers, bookmark_num)
            await route.continue_()

        await page.goto("https://www.libbyapp.com/")

        # Open tags
        await page.click("button[class=\"app-footer-nav-bar-button-tags halo\"]")
        
        # Open smart-list of "titles I've borrowed"
        await page.click("text=🧾")

        # Open the target book
        await page.goto(f"https://libbyapp.com/tags/similar-{title_id}/page-1/{title_id}")       

        # Open the audiobook player
        actions = await page.query_selector("ul[class=\"title-details-actions-list\"]")
        open_book = await actions.query_selector("li:nth-child(2)")
        await open_book.click()

        # page.wait_for_load_state("networkidle") # very slow
        # page.wait_for_load_state("domcontentloaded")
        await page.wait_for_selector("iframe")
        print("Page loaded.", flush=True)

        iframe_element = await page.query_selector("iframe")
        iframe = await iframe_element.content_frame()

        # close pop-up to synchronise audiobook if it exists
        try:
            print("Checking for pop-up.", flush=True)
            popup = await iframe.query_selector("button[class=\"notifier-close-button halo\"]")
            if not await popup.get_attribute('aria-hidden') == 'true':
                print("Pop-up found.", flush=True)
                await popup.click()
        except:
            print("No pop-up found.", flush=True)
            pass

        time.sleep(3)
        bookmarks_button = await iframe.query_selector("button[class=\"nav-action-item-button halo\"]")
        await bookmarks_button.click()

        async def get_bookmarks():
            return await iframe.query_selector_all("li[class=\"marks-dialog-mark data-mark-type_bookmark data-mark-color_none halos-anchor\"]")
        
        bookmarks = await get_bookmarks()
        assert len(bookmarks) == len(bookmark_list), "Number of bookmarks do not match."

        # Intercept network requests
        await page.route("**://*mediaclips*/**", handle_request)
        time.sleep(5)

        # for bookmark_num in range(1,len(bookmarks)+1):
        for bookmark_num in range(len(bookmarks),0,-1):
            if 2 < bookmark_num < 25:
                print(f"Skipping bookmark {bookmark_num}.", flush=True)
                continue

            bookmark_popup = await iframe.query_selector("div[class=\"navigation-shades\"]")
            if not await bookmark_popup.text_content():
                await bookmarks_button.click()
                bookmarks = await get_bookmarks()
            # if not iframe.query_selector("div[class=\"shibui-shade marks-shade shibui-shade-n is-visible\"]"):
            #     bookmarks_button.click()

            bookmark = bookmarks[bookmark_num-1]
            print(f"Clicked bookmark {bookmark_num}.", flush=True)
            await bookmark.click()
            time.sleep(5)
            chapter = await iframe.query_selector("div[class=\"chapter-bar-title\"]")
            chapter_num = await chapter.text_content()
            prog_in_chapter = await iframe.query_selector("span[class=\"chapter-bar-prev-text\"]")
            prog_text = await prog_in_chapter.text_content()
            print(f"Bookmark {bookmark_num}: {chapter_num}, {prog_text.lower()} in.", flush=True)
            print(flush=True)
            # page.expect_response("**://*mediaclips*/**")
            # page.expect_request_finished("**://*mediaclips*/**")

        # Get bookmarks missed for whatever reason
        for bookmark_num in range(1,len(bookmarks)+1):
            if not os.path.exists(f"audio_file_{bookmark_num}.mp3"):
                bookmark_popup = await iframe.query_selector("div[class=\"navigation-shades\"]")
                if not await bookmark_popup.text_content():
                    await bookmarks_button.click()
                    bookmarks = await get_bookmarks()

                bookmark = bookmarks[bookmark_num-1]
                print(f"Downloading bookmark {bookmark_num}.", flush=True)
                await bookmark.click()
                time.sleep(5)
                chapter = await iframe.query_selector("div[class=\"chapter-bar-title\"]")
                chapter_num = await chapter.text_content()
                prog_in_chapter = await iframe.query_selector("span[class=\"chapter-bar-prev-text\"]")
                prog_text = await prog_in_chapter.text_content()
                print(f"Bookmark {bookmark_num}: {chapter_num}, {prog_text.lower()} in.", flush=True)
                print(flush=True)

        # Close the browser
        browser.close()


bookmarks_file = "world_upside_down.json"
with open(bookmarks_file, "r") as f:
    bookmarks_data = json.load(f)

title_data = bookmarks_data['readingJourney']['title']
title = title_data['text']
title_url = title_data['url']
title_id = title_data['titleId']
bookmarks = bookmarks_data['bookmarks']
ordered = sorted(bookmarks, key=lambda x: x['percent'])

def get_structure(element):
    structure = element.evaluate('''() => {
        const getElementInfo = (element) => {
            return {
                tagName: element.tagName,
                className: element.className,
                id: element.id,
                innerText: element.innerText,
                children: Array.from(element.children).map(getElementInfo)
            };
        };
        return getElementInfo(document.body);
    }''')
    return structure

# asyncio.run(start_browser())
asyncio.run(get_audiobookmarks(bookmark_list=ordered, title_id=title_id))
# get_audiobookmarks(bookmark_list=ordered, title_id=title_id)

# page_structure = page.evaluate('''() => {
#     const getElementInfo = (element) => {
#         return {
#             tagName: element.tagName,
#             className: element.className,
#             id: element.id,
#             innerText: element.innerText,
#             children: Array.from(element.children).map(getElementInfo)
#         };
#     };
#     return getElementInfo(document.body);
# }''')



# get bookmark data
        # # Open the target book
        # page.goto(f"https://libbyapp.com/tags/similar-{title_id}/page-1/{title_id}")

        # # Get bookmark JSON data
        # reading_journey = page.query_selector("button[class=\"title-journey-preview-button shibui-button halo\"]")
        # reading_journey.click()
        # action_button = page.query_selector("button[class=\"shelf-actions\"]")
        # action_button.click()
        # # export_button = page.query_selector("a[class=\"halo\" role=\"button\"]")
        # # export_button.click()
        # popover = page.query_selector("div[class=\"popover-choices popover-scroller popover-content halos-anchor\"]")
        # export = popover.query_selector("a:nth-child(2)")
        # export.click()
        # popover = page.query_selector("div[class=\"popover-choices popover-scroller popover-content halos-anchor\"]")
        # export_json = popover.query_selector("a:nth-child(3)")
        # export_json.click()






# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options

# # First run the following command in the terminal:
# # google-chrome --remote-debugging-port=9222

# # Set up Chrome options to connect to the remote debugging port
# chrome_options = Options()
# chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# # Connect to the running Chrome instance
# driver = webdriver.Chrome(options=chrome_options)

# # Navigate to the Libby app website
# driver.get("https://www.libbyapp.com/")


# # Perform actions on the website
# pass

# # Close the browser
# # driver.quit()