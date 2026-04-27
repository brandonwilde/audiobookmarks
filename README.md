# AudioBookmarks [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/brandonwilde/audiobookmarks)

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

You can use the tool with either Libby or Hoopla. The basic usage is the same for both platforms, but the login process differs slightly.

The general usage is:
```bash
python main.py <platform> <book_name>
```

### Hoopla

If you have set the `HOOPLA_USERNAME` and `HOOPLA_PASSWORD` environment variables, login is automated. You can always run the tool with:
```bash
python main.py hoopla "<book_name>"
```

The tool will use your saved session data (stored in `BROWSER_DATA_DIRECTORY`), so you won't need to log in again unless your session expires.

### Libby

Libby requires real Google Chrome (for Widevine DRM support). The script connects to a running Chrome instance via the Chrome DevTools Protocol (CDP).

**Step 1: Start Chrome with the debug port**

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/path/to/audiobookmarks/debug_user_data &
```

> **Important:** You must pass `--user-data-dir` pointing to a dedicated directory (e.g. `debug_user_data/` inside this repo). Chrome will silently ignore `--remote-debugging-port` without this flag. Do **not** reuse the `BROWSER_DATA_DIRECTORY` path — that directory is used by Playwright and will conflict.

The first time, log into Libby in the browser window that opens. If you have books checked out from multiple library cards, make sure all cards are connected — the tool can only see books visible on your shelf. Your session is saved in `debug_user_data/`, so you won't need to log in again on future runs.

**Step 2: Run the tool**

```bash
python main.py libby "<book_name>" --debug
```

### Command Arguments

- `platform`: The audiobook platform (`libby` or `hoopla`)
- `book_name`: The name of the audiobook (use quotes for multi-word titles)
- `--debug`: Run in debug mode with visible browser

Example run command:
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

2. **Book Not Found**: Ensure the book title matches exactly as it appears in your Libby or Hoopla library. If you have multiple library cards connected in Libby, make sure all cards are linked in the `debug_user_data` Chrome session — books from secondary library cards won't appear otherwise.

3. **Audio Extraction Issues**: If the tool fails to extract audio properly:
   - Try running the tool again
   - Ensure your browser is properly displaying the audiobook player
   - Check that the bookmark timestamps are correctly set in the platform

4. **Transcription Errors**: If transcriptions are inaccurate:
   - Check your OpenAI API key is valid
   - Try running the tool again (results may vary)

### Browser Data

The tool stores browser session data in different directories depending on platform:

- Libby debug mode uses the Chrome profile directory passed to `--user-data-dir` (for example, `debug_user_data/`).
- Hoopla and non-debug Playwright runs use `BROWSER_DATA_DIRECTORY`.

If you're experiencing persistent login issues, delete the relevant directory to start fresh:

```bash
rm -rf /path/to/your/profile/directory
```

Then run the tool again with the `--debug` flag to complete a new login.
