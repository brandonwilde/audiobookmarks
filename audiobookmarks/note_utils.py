def format_author_header(authors):
    '''
    Format the author header for a markdown file.
    '''
    author_header = "---\n"
    authors_clean = [author.translate(str.maketrans('','','.')) for author in authors]
    author_header += f'''Author: "[[{authors_clean[0]}]]"\n'''
    if len(authors_clean) > 1:
        for i, author in enumerate(authors_clean[1:], start=2):
            author_header += f'''Author{i}: "[[{author}]]"\n'''
    author_header += "---\n"
    return author_header