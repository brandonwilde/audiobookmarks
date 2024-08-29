import asyncio
import json
import os

from get_audio import get_audiobookmarks
from transcribe import transcribe_audio_file


bookmarks_file = "world_upside_down.json"
with open(bookmarks_file, "r") as f:
    bookmarks_data = json.load(f)

title_data = bookmarks_data['readingJourney']['title']
title = title_data['text']
title_url = title_data['url']
title_id = title_data['titleId']
bookmarks = bookmarks_data['bookmarks']
ordered = sorted(bookmarks, key=lambda x: x['percent'])

# Get audio files and bookmark position info
updated_bookmarks = asyncio.run(get_audiobookmarks(bookmark_list=ordered, title_id=title_id))

bookmarks_data['bookmarks'] = updated_bookmarks
updated_file = bookmarks_file.replace(".json", "_updated.json")

with open(updated_file, "w") as f:
    json.dump(bookmarks_data, f, indent=4)


# Transcribe bookmarks
data_directory = "data"
book = "world_upside_down"
book_data = book + "_updated.json"

book_dir = os.path.join(data_directory, book)
data_file = os.path.join(data_directory, book, book_data)

with open(data_file, 'r') as f:
    data = json.load(f)

bookmarks = data['bookmarks']
for bookmark in bookmarks:
    bookmark['5m_transcript'] = transcribe_audio_file(bookmark['bookmark_num'], book_dir)
    # Save transcripts as they are generated
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)

