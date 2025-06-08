import os
import re
from ..note_utils import format_author_header

def split_authors(author_string, and_words=['and', 'und', 'y', 'e', 'et']):
    '''
    Split an author string into a list of authors.
    '''
    patterns = []
    for word in and_words:
        patterns.extend([
            fr'\b{word}\b',
            fr',\s*\b{word}\b'
        ])
    patterns.append(',')

    regex_pattern = '|'.join(patterns)
    authors = re.split(regex_pattern, author_string)
    return [author.strip() for author in authors]


def write_notes(bookmarks_data, notes_dir):
    '''
    Write notes to a markdown file.
    '''
    title = bookmarks_data['readingJourney']['title']['text']
    author = bookmarks_data['readingJourney']['author']
    bookmarks = bookmarks_data['bookmarks']

    notes_file = os.path.join(notes_dir, f"{title}.md")
    with open(notes_file, "w") as f:
        authors = split_authors(author)
        f.write(format_author_header(authors))
        # We assume the bookmarks are in order
        current_chapter = ''
        for bookmark in bookmarks:
            if bookmark['chapter_num'] != current_chapter:
                current_chapter = bookmark['chapter_num']
                f.write(f"\n---\n\n")
                f.write(f"## {current_chapter}\n")

            minutes_in = int(bookmark['minutes_in'].strip('m'))
            minutes_remaining = int(bookmark['minutes_remaining'].strip('m'))
            chapter_length = minutes_in + minutes_remaining
            chapter_percent = round((minutes_in / chapter_length) * 100)
            book_percent = round((bookmark['percent'] * 100))
            f.write(f"#### Bookmark {bookmark['bookmark_num']}\n")
            f.write(f"*({bookmark['minutes_in']} \\[{chapter_percent}%\\] into chapter, \\[{book_percent}%\\] into book)*\n")
            if 'note' in bookmark:
                f.write(f"**{bookmark['note']}**\n")
            f.write(f"{bookmark['quote']}\n")
            
    
    print(f"Notes written to {notes_file}")
    return