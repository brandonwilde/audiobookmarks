# AudioBookmarks

A personal Python tool for managing my audiobook bookmarks from various platforms. This is a personal project created for my own use and learning purposes.

**Note on Accuracy:** This tool uses heuristic methods to identify and transcribe audio snippets from bookmarks. While it works well in most cases (approximately 95% accuracy), it may occasionally fail to find the correct section or transcribe an incorrect portion of the audio. Review the resulting notes carefully for accuracy.
Re-running the tool may yield different results.

## Disclaimer

This tool is intended for personal use only. It was created as a learning exercise and to solve a personal need. Please be aware that automated interactions with audiobook platforms may be against their terms of service. Use at your own risk.

## Overview

This tool automates the process of extracting and processing audiobook bookmarks from Libby and Hoopla:

1. **Browser Automation**: Uses Playwright to navigate to your bookmarks in each platform
2. **Audio Extraction**: Captures the audio around each bookmark timestamp
3. **Transcription**: Converts the audio to text using OpenAI's Whisper API
4. **Quote Selection**: Processes the transcribed text to extract the most relevant quote

Note: This tool uses OpenAI's APIs for transcription and text processing, which will incur costs based on their pricing.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/audiobookmarks.git
cd audiobookmarks
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
BOOKS_DATA_DIRECTORY=/path/to/store/book/data
BROWSER_DATA_DIRECTORY=/path/to/store/browser/data # To store browser session data (and skip login)
NOTES_DIRECTORY=/path/to/store/notes
OPENAI_API_KEY=your_api_key_here  # Required for audio transcription
OPENAI_ORGANIZATION=your_organization_key_here
HOOPLA_USERNAME=your_hoopla_username
HOOPLA_PASSWORD=your_hoopla_password
```

## Usage

### First-Time Setup

The first time you use this tool, you'll need to:

1. Run the script with the `--debug` flag:
```bash
python main.py <platform> <book_name> --debug
```

2. When prompted, log in to your audiobook platform (Libby or Hoopla) in the browser window that opens.
   - For Libby: You'll need to complete the login process manually
   - For Hoopla: If you've set the environment variables, login will be automated

3. Hit enter in your terminal to continue. The tool will save your session data to the `BROWSER_DATA_DIRECTORY` specified in your `.env` file.

### Subsequent Usage

After your first successful login:

1. Run the script:
```bash
python main.py <platform> <book_name>
```

The tool will use your saved session data, so you won't need to log in again unless your session expires.

### Command Arguments

- `platform`: The audiobook platform (`libby` or `hoopla`)
- `book_name`: The name of the audiobook (use quotes for multi-word titles)
- `--debug`: Run in debug mode with visible browser (always required for now)

Example:
```bash
python main.py libby "Project Hail Mary" --debug
```

## Output Format

The tool creates a markdown file in your specified `NOTES_DIRECTORY` with the following structure:

- **File Name**: `<Book Title>.md`
- **Metadata**: Author information in YAML frontmatter
- **Content Structure**:
  - Organized by chapters
  - Each bookmark includes:
    - Bookmark number
    - Timestamp information
    - Any notes you added in the platform (for both Libby and Hoopla)
    - Transcribed quote from the audio
  - Additional details:
    - Libby shows time into chapter
    - Hoopla shows both chapter-specific and book-wide progress percentages

Example output:
```markdown
---
Author: "[[Author Name]]"
---

## Chapter 1
#### Bookmark 1 *(5:30 in)*
**Your note from the platform (if any)**
Transcribed quote from the audiobook...

---

## Chapter 2
#### Bookmark 2 *(2:15 in)*
Transcribed quote from the audiobook...

---

## Troubleshooting

### Common Issues

1. **Session Expired**: If your saved session has expired, the tool will prompt you to log in again.

2. **Book Not Found**: Ensure the book title matches exactly as it appears in your Libby or Hoopla library.

3. **Audio Extraction Issues**: If the tool fails to extract audio properly:
   - Try running the tool again
   - Ensure your browser is properly displaying the audiobook player
   - Check that the bookmark timestamps are correctly set in the platform

4. **Transcription Errors**: If transcriptions are inaccurate:
   - Check your OpenAI API key is valid
   - Try running the tool again (results may vary)

### Browser Data

The tool stores browser session data in the directory specified by `BROWSER_DATA_DIRECTORY`. If you're experiencing persistent login issues, you can delete this directory to start fresh:

```bash
rm -rf /path/to/your/browser/data/directory
```

Then run the tool again with the `--debug` flag to complete a new login.
