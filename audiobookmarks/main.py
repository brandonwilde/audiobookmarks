import asyncio
import json
import os

from libby.clean_transcripts import clean_transcripts
from libby.create_notes import write_notes
from libby.get_audio import get_audiobookmarks
from libby.transcribe import transcribe_audio_file

NOTES_DIRECTORY = os.environ.get("NOTES_DIRECTORY", "")


data_directory = "data"
book_name = "world_upside_down_2"
book_dir = os.path.join(data_directory, book_name)
book_audio_dir = os.path.join(book_dir, "audio")
book_file_name = book_name + ".json"
book_file = os.path.join(book_dir, book_file_name)
updated_file = book_file.replace(".json", "_updated.json")

if not os.path.exists(book_dir):
    os.makedirs(book_dir)
if not os.path.exists(book_audio_dir):
    os.makedirs(book_audio_dir)
# start with book_file in the book directory

with open(book_file, "r") as f:
    bookmarks_data = json.load(f)

title_data = bookmarks_data['readingJourney']['title']
title_id = title_data['titleId']
bookmarks = bookmarks_data['bookmarks']
ordered = sorted(bookmarks, key=lambda x: x['percent'])


# Get audio files and bookmark position info
updated_bookmarks = asyncio.run(
    get_audiobookmarks(bookmark_list=ordered, title_id=title_id, download_dir=book_audio_dir)
)
bookmarks_data['bookmarks'] = updated_bookmarks
with open(updated_file, "w") as f:
    json.dump(bookmarks_data, f, indent=4)


# Transcribe bookmarks
with open(updated_file, 'r') as f:
    data = json.load(f)

bookmarks = data['bookmarks']
for bookmark in bookmarks:
    bookmark['5m_transcript'] = transcribe_audio_file(bookmark['bookmark_num'], book_audio_dir)
    # Save transcripts as they are generated
    with open(updated_file, 'w') as f:
        json.dump(data, f, indent=4)


# Clean up transcripts
with open(updated_file, 'r') as f:
    data = json.load(f)
cleaned_data = clean_transcripts(data)
with open(updated_file, 'w') as f:
    json.dump(cleaned_data, f, indent=4)


# Save notes to Obsidian
with open(updated_file, 'r') as f:
    data = json.load(f)
write_notes(data, NOTES_DIRECTORY)
