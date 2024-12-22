from aitools.media_tools.text_tools import prompt_llm

prompt_template = """
A note was taken while listening to an audiobook. A segment of the audiobook was then transcribed, starting before and ending after the note's timestamp. Your task is to read the note and then review the transcribed segment to find the relevant content. Extract this content as a quote that can be attached to the note.

Please ensure that the quote is faithful to the original text and includes any content that could possibly be relevant or necessary to make sense of the quote. Do not change ANY of the original wording. Punctuation and formatting should be added as appropriate to make up for their loss in the transcription. The only other change you are allowed to make is to add ellipses (...) to indicate where irrelevant content has been removed, although this should be done sparingly.

Below are the note and the transcribed book segment:

<note>
{note}
<\\note>

<book_segment>
{transcript}
<\\book_segment>

Please return the quote that sufficiently captures the context of the note. Do not include any additional comments, disclaimers, or conversation in your response. If you cannot respond with a quote for any reason, please respond with "N/A".
"""

prompt_wo_note_template = """
Below is a transcribed segment of an audiobook. Your task is to use your best judgment to restore the text's original punctuation and formatting. If there appear to be errors or incomplete sentences, use ellipses (...) to indicate where content is missing.

<book_segment>
{transcript}
<\\book_segment>

Please return the formatted book segment. Do not include any additional comments, disclaimers, or conversation in your response. If you cannot complete the task for any reason, please respond with "N/A".
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
            cleaned_transcript = prompt_llm([prompt], max_tokens=2000)
        else:
            prompt_wo_note = prompt_wo_note_template.format(transcript=transcript)
            cleaned_transcript = prompt_llm([prompt_wo_note], max_tokens=2000)
        bookmark['quote'] = cleaned_transcript
    return data