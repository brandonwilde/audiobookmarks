import os

def write_notes(bookmarks_data, notes_dir):
    '''
    Write notes to a markdown file.
    '''
    title = bookmarks_data['readingJourney']['title']['text']
    author = bookmarks_data['readingJourney']['author']
    bookmarks = bookmarks_data['bookmarks']

    notes_file = os.path.join(notes_dir, f"{title}.md")
    with open(notes_file, "w") as f:
        f.write(f"## Author: {author}\n\n")
        for bookmark in bookmarks:
            f.write(f"### Bookmark {bookmark['bookmark_num']}\n")
            if 'note' in bookmark:
                f.write(f"#### {bookmark['note']}\n")
            f.write(f"{bookmark['5m_transcript']}\n\n")
            f.write(f"---\n\n")

    print(f"Notes written to {notes_file}")
    return