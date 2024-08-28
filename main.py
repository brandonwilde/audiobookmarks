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


def download_audio_file(audio_url, headers, tag=''):
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
        print(f'\nAudio file "{file_name}" downloaded successfully.',flush=True)
        print(tabulate(byte_data), flush=True)
        pass
    else:
        print(f"Failed to download audio file. Status code: {response.status_code}", flush=True)


def get_audiobookmarks(title_id='', bookmark_list=[]):
    # First run the following command in the terminal:
    # google-chrome --remote-debugging-port=9222
     with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]  # Get the first context
        context.set_default_timeout(7000)
        page = context.pages[0]  # Get the first page

        bookmark_num = -1

        def handle_request(route, request):
            nonlocal bookmark_num
            if "mediaclips" in request.url:
                headers = request.headers
                audio_url = request.url
                # print(f"!!!!!Audio URL intercepted: {audio_url}", flush=True)
                download_audio_file(audio_url, headers, bookmark_num)
            # else:
            #     print(f"Request URL: {request.url}", flush=True)
            route.continue_()

        # def start_interception():
        #     page.route("**/*", handle_request)

        page.goto("https://www.libbyapp.com/")

        # # For establishing connection
        # buttons = page.query_selector("ul[class=\"interview-answers\"]")
        # first_button = buttons.query_selector("li")
        # first_button.click()

        # Open tags
        page.click("button[class=\"app-footer-nav-bar-button-tags halo\"]")
        
        # Open smart-list of "titles I've borrowed"
        page.click("text=🧾")

        # Open the target book
        page.goto(f"https://libbyapp.com/tags/similar-{title_id}/page-1/{title_id}")       

        # Open the audiobook player
        actions = page.query_selector("ul[class=\"title-details-actions-list\"]")
        open_book = actions.query_selector("li:nth-child(2)")
        open_book.click()

        # page.wait_for_load_state("networkidle") # very slow
        # page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("iframe")
        print("Page loaded.", flush=True)
        # page.expect_response(lambda response: 'audio/mpeg' in response.headers.get('content-type', ''))

        iframe_element = page.query_selector("iframe")
        # iframe_source = await iframe_element.get_attribute("src")
        # await page.goto(iframe_source)

        iframe = iframe_element.content_frame()
        # iframe_struct = get_structure(iframe)

        # iframe.wait_for_selector("button[class=\"nav-action-item-button halo\"]")
        
        # close pop-up to synchronise audiobook if it exists
        try:
            print("Checking for pop-up.", flush=True)
            popup = iframe.query_selector("button[class=\"notifier-close-button halo\"]")
            if not popup.get_attribute('aria-hidden') == 'true':
                print("Pop-up found.", flush=True)
                popup.click()
        except:
            print("No pop-up found.", flush=True)
            pass
        bookmarks_button = iframe.query_selector("button[class=\"nav-action-item-button halo\"]")
        bookmarks_button.click()

        def get_bookmarks():
            return iframe.query_selector_all("li[class=\"marks-dialog-mark data-mark-type_bookmark data-mark-color_none halos-anchor\"]")
        
        bookmarks = get_bookmarks()
        assert len(bookmarks) == len(bookmark_list), "Number of bookmarks do not match."

        # Intercept network requests
        page.route("**://*mediaclips*/**", handle_request)

        # for bookmark_num in range(1,len(bookmarks)+1):
        for bookmark_num in range(len(bookmarks),0,-1):
            bookmark_popup = iframe.query_selector("div[class=\"navigation-shades\"]")
            if not bookmark_popup.text_content():
                bookmarks_button.click()
                bookmarks = get_bookmarks()
            # if not iframe.query_selector("div[class=\"shibui-shade marks-shade shibui-shade-n is-visible\"]"):
            #     bookmarks_button.click()

            bookmark = bookmarks[bookmark_num-1]
            print(f"Clicked bookmark {bookmark_num}.", flush=True)
            bookmark.click()
            time.sleep(1)
            # page.expect_response("**://*mediaclips*/**")
            # page.expect_request_finished("**://*mediaclips*/**")

        

        # for bookmark_num,bookmark in enumerate(bookmarks):
        #     # start_interception()
        #     time.sleep(1)
        #     try:
        #         bookmark.click()
        #     except:
        #         bookmarks_button.click()
        #         bookmark.click()

            # with page.expect_response(lambda response: 'audio/mpeg' in response.headers.get('content-type', '')) as response_info:
            #     bookmark.click()
            #     print(f"Bookmark {bookmark_num+1} clicked.", flush=True)
            # response = response_info.value

            # with page.expect_response(lambda response: "odrmediaclips" in response.url) as response_info:
            #     bookmark.click()
            #     print(f"Bookmark {bookmark_num+1} clicked.", flush=True)
            # response = response_info.value         

            # # Get the response and download the file
            # content = response.body()
            # tag = remove_punctuation(audio_url)[-10:]
            # file_name = f"audio_file_{tag}.mp3"
            # with open(file_name, 'wb') as f:
            #     f.write(content)
            # print(f"Downloaded: {file_name}")

            # with page.expect_request(lambda req: 'mediaclips' in req.url) as request_info:
            #     bookmark.click()
            #     print(f"Bookmark {bookmark_num+1} clicked.", flush=True)
            # req = request_info.value
            # download_audio_file(req.url, req.headers)
            # time.sleep(1)


            # # Wait for the network request to complete
            # while True:
            #     request = await page.wait_for_event("requestfinished")
            #     print(f"Request for {request.url} finished.", flush=True)
            #     if "mediaclips" in request.url:
            #         # Get request URL and headers here
            #         audio_url = request.url
            #         headers = request.headers
            #         print(f"***Request for {audio_url} finished.", flush=True)
            #         await download_audio_file(audio_url, headers, bookmark_num+1)
            #         break  # Exit the loop once the correct request is found


        # page.text_content

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
# asyncio.run(reconnect_browser())
get_audiobookmarks(bookmark_list=ordered, title_id=title_id)

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