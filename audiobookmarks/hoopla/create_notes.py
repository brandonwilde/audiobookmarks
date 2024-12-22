import os
import time

def write_notes(bookmarks, book_info, notes_dir):
    '''
    Write notes to a markdown file.
    '''
    title = book_info['title']
    subtitle = book_info['subtitle']
    authors = [author['name'] for author in book_info['authors']]
    chapters = book_info['chapters']
    synopsis = book_info['synopsis']
    duration = book_info['seconds']

    if ':' in title and not subtitle:
        subtitle = title.split(':')[1].strip()
        title = title.split(':')[0].strip()

    notes_file = os.path.join(notes_dir, f"{title}.md")
    with open(notes_file, "w") as f:
        f.write("---\n")
        authors_clean = [author.translate(str.maketrans('','','.')) for author in authors]
        authors_str = "[[" + "]], [[".join(authors_clean) + "]]"
        f.write(f'''Author: "{authors_str}"\n''')
        f.write("---\n")
        if subtitle:
            f.write(f"# {title}: {subtitle}\n")
        else:
            f.write(f"# {title}\n")
        f.write(f"### Synopsis\n")
        f.write(f"{synopsis}\n\n")
        f.write(f"---\n\n")

        bookmark_num = 0
        if chapters:
            for chapter in chapters:
                f.write(f"## {chapter['title']}\n")
                chapter_start = chapter['start']
                chapter_duration = chapter['duration']
                chapter_bookmarks = [bookmark for bookmark in bookmarks if bookmark['chapter']['title'] == chapter['title']]
                for bookmark in chapter_bookmarks:
                    bookmark_num += 1
                    book_seconds = bookmark['seconds']
                    book_time = time.strftime('%H:%M:%S', time.gmtime(book_seconds))
                    book_percent = round((book_seconds / duration) * 100, 2)
                    chapter_seconds = book_seconds - chapter_start
                    chapter_time = time.strftime('%H:%M:%S', time.gmtime(chapter_seconds))
                    chapter_percent = round((chapter_seconds / chapter_duration) * 100, 2)

                    f.write(f"#### Bookmark {bookmark_num}\n")
                    f.write(f"*({chapter_time} \\[{chapter_percent}%\\] into chapter, {book_time} \\[{book_percent}%\\] into book)*\n")
                    if 'note' in bookmark:
                        f.write(f"{bookmark['note']}\n")
                f.write(f"\n---\n\n")

        else:
            for bookmark in bookmarks:
                bookmark_num += 1
                book_seconds = bookmark['seconds']
                book_time = time.strftime('%H:%M:%S', time.gmtime(book_seconds))
                book_percent = round((book_seconds / duration) * 100, 2)
                f.write(f"#### Bookmark {bookmark_num}\n")
                f.write(f"*({book_time} \\[{book_percent}%\\] into book)*\n")
                if 'note' in bookmark:
                    f.write(f"{bookmark['note']}\n")
    
    print(f"Notes written to {notes_file}")
    return
