import json
import os

from audiobookmarks.models import HooplaBookDataTree
from audiobookmarks.hoopla.get_bookmarks import get_bookmarks
from audiobookmarks.hoopla.create_notes import write_notes

BOOKS_DATA_DIRECTORY = os.environ.get("BOOKS_DATA_DIRECTORY", "")
NOTES_DIRECTORY = os.environ.get("NOTES_DIRECTORY", "")

def main(book_name):
    book = HooplaBookDataTree(BOOKS_DATA_DIRECTORY, book_name)
    if not os.path.exists(book.dir):
        os.makedirs(book.dir)

    get_bookmarks(book)

    with open(book.bookmarks_file, "r") as f:
        bookmarks_data = json.load(f)['data']['bookmarks']

    with open(book.title_file, "r") as f:
        book_info = json.load(f)['data']['title']
        
    write_notes(bookmarks_data, book_info, NOTES_DIRECTORY)