import asyncio
import json
import os

from libby.clean_transcripts import clean_transcripts
from libby.create_notes import write_notes
from libby.get_audio import get_audiobookmarks
from libby.transcribe import transcribe_audio_file

NOTES_DIRECTORY = os.environ.get("NOTES_DIRECTORY", "")


data_directory = "data"
book_name = "The Experience Machine"
book_file_name = book_name.replace(' ', '_').lower()
book_dir = os.path.join(data_directory, book_file_name)
book_audio_dir = os.path.join(book_dir, "audio")
book_file = os.path.join(book_dir, book_file_name + '.json')
updated_file = book_file.replace(".json", "_updated.json")

if not os.path.exists(book_dir):
    os.makedirs(book_dir)

# Get audio files and bookmark position info
asyncio.run(get_audiobookmarks(title=book_name, download_dir=book_dir))

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
