import json
import os
import re
import time

from hoopla.get_bookmarks import get_bookmarks
from audiobookmarks.hoopla.create_notes import write_notes

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


get_bookmarks(
    title='what_iranians_want',
    download_dir=book_dir
)

bookmarks_file = os.path.join(book_dir, "what_iranians_want_bookmarks.json")
book_info_file = os.path.join(book_dir, "what_iranians_want_title.json")

with open(bookmarks_file, "r") as f:
    bookmarks_data = json.load(f)['data']['bookmarks']

with open(book_info_file, "r") as f:
    book_info = json.load(f)['data']['title']
    
write_notes(bookmarks_data, book_info, NOTES_DIRECTORY)