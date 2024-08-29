from aitools.media_tools.text_tools import prompt_llm

prompt_template = """
Below is a transcribed segment of an audiobook. The segment is expected to contain content related to the following jotted note:

<note>
{note}
<\note>

<book_segment>
{transcript}
<\book_segment>

Please trim the transcript to only include content relevant to the topic or idea mentioned in the note, but trim sparingly. Use ellipses (...) to indicate where content has been removed. Book formatting has been lost in the transcription, so please add formatting back in as needed to make the text more readable.

Notice: If the provided note is not relevant to the transcribed segment, please simply respond with "N/A" to indicate that no trimming is necessary.

In any case, only respond with the trimmed transcript or "N/A"; do not include any additional comments or disclaimers.
"""

prompt_wo_note_template = """
Below is a transcribed segment of an audiobook. 

<book_segment>
{transcript}
<\book_segment>

Book formatting has been lost in the transcription, so please add formatting back in as appropriate to make the text more readable. If there are errors or incomplete sentences, use ellipses (...) to indicate where content has been removed.
"""

def clean_transcripts(data):
    '''
    Trim and format the transcripts to focus on the bookmarked content.
    '''
    bookmarks = data['bookmarks']
    for bookmark in bookmarks:
        transcript = bookmark['5m_transcript']
        if 'note' in bookmark:
            note = bookmark['note']
            prompt = prompt_template.format(note=note, transcript=transcript)
            cleaned_transcript = prompt_llm(prompt, max_tokens=2000)
        else:
            prompt_wo_note = prompt_wo_note_template.format(transcript=transcript)
            cleaned_transcript = prompt_llm(prompt_wo_note, max_tokens=2000)
        bookmark['quote'] = cleaned_transcript
    return bookmarks