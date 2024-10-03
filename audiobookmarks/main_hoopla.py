import json
import os
import re
import time

from hoopla.get_bookmarks import get_bookmarks
from hoopla.create_notes import write_notes

NOTES_DIRECTORY = os.environ.get("NOTES_DIRECTORY", "")

# If running in debug mode, first run the following command in the terminal:
# google-chrome --remote-debugging-port=9222

data_directory = "data"
book_name = "what_iranians_want"
book_dir = os.path.join(data_directory, book_name)
bookmarks_json = os.path.join(book_dir, f"{book_name}_bookmarks.json")
title_json = os.path.join(book_dir, f"{book_name}_title.json")

if not os.path.exists(book_dir):
    os.makedirs(book_dir)


get_bookmarks(
    title='what_iranians_want',
    download_dir=book_dir
)

with open(bookmarks_json, "r") as f:
    bookmarks_data = json.load(f)['data']['bookmarks']

with open(title_json, "r") as f:
    book_info = json.load(f)['data']['title']
    
write_notes(bookmarks_data, book_info, NOTES_DIRECTORY)