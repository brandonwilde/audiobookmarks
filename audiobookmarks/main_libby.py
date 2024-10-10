import asyncio
import json
import os

from models import LibbyBookDataTree
from libby.clean_transcripts import clean_transcripts
from libby.create_notes import write_notes
from libby.get_audio import get_audiobookmarks
from libby.transcribe import transcribe_audio_file

BOOKS_DATA_DIRECTORY = os.environ.get("BOOKS_DATA_DIRECTORY", "")
NOTES_DIRECTORY = os.environ.get("NOTES_DIRECTORY", "")


book_name = "Dark Territory"

book = LibbyBookDataTree(BOOKS_DATA_DIRECTORY, book_name)
    
if not os.path.exists(book.dir):
    os.makedirs(book.dir)

# Get audio files and bookmark position info
asyncio.run(get_audiobookmarks(book))

# Transcribe bookmarks
with open(book.updated_file, 'r') as f:
    data = json.load(f)

bookmarks = data['bookmarks']
for bookmark in bookmarks:
    bookmark['5m_transcript'] = transcribe_audio_file(bookmark['bookmark_num'], book.audio_dir)
    # Save transcripts as they are generated
    with open(book.updated_file, 'w') as f:
        json.dump(data, f, indent=4)


# Clean up transcripts
with open(book.updated_file, 'r') as f:
    data = json.load(f)
cleaned_data = clean_transcripts(data)
with open(book.updated_file, 'w') as f:
    json.dump(cleaned_data, f, indent=4)


# Save notes to Obsidian
with open(book.updated_file, 'r') as f:
    data = json.load(f)
write_notes(data, NOTES_DIRECTORY)
