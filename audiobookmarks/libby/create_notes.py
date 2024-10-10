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
        f.write("---\n")
        f.write(f'''Author: "[[{author.translate(str.maketrans('','','.'))}]]"\n''')
        f.write("---\n")
        # We assume the bookmarks are in order
        current_chapter = ''
        for bookmark in bookmarks:
            if bookmark['chapter_num'] != current_chapter:
                current_chapter = bookmark['chapter_num']
                f.write(f"\n---\n\n")
                f.write(f"## {current_chapter}\n")
            f.write(f"#### Bookmark {bookmark['bookmark_num']} *({bookmark['minutes_in']} in)*\n")
            if 'note' in bookmark:
                f.write(f"**{bookmark['note']}**\n")
            f.write(f"{bookmark['quote']}\n")
            
    
    print(f"Notes written to {notes_file}")
    return