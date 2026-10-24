# VLC Subtitle Matcher Pro

A Python desktop application for pairing and renaming subtitle files, previewing changes, and downloading subtitles through the OpenSubtitles API.

## Features

- **Batch subtitle renaming:** Match video and subtitle files and rename subtitles to match their corresponding videos.
- **Natural sorting:** Process filenames numerically, so `Episode 2` appears before `Episode 10`.
- **Folder scanning:** Find and sort supported video and subtitle files in a selected directory.
- **Dry-run previews:** Review proposed filename changes before applying them.
- **Extension validation:** Restrict processing to supported media and subtitle formats.
- **Online subtitle downloads:** Search OpenSubtitles and download subtitles to your video directory.
- **Theme options and execution log:** Use the CustomTkinter interface with dark, light, or system appearance and a running log.

## Download

A packaged Windows executable is available in [Releases](../../releases). Download the latest `.exe` to run the application without installing Python.

## Run from source

### Requirements

- Python 3.9 or later
- An OpenSubtitles API key for online subtitle downloads

### Setup

1. Clone the repository and open its directory:

    ```powershell
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create and activate a virtual environment:

    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

3. Install dependencies:

    ```powershell
    pip install customtkinter requests python-dotenv certifi urllib3
    ```

4. Configure your API key using either the application's API key field or a local `.env` file:

    ```text
    OPEN_SUBTITLES_API_KEY=your_api_key_here
    ```

5. Start the application:

    ```powershell
    python app.py
    ```

## Security

- Treat your OpenSubtitles API key as a password. Do not put real keys in source files, screenshots, issues, or commits.
- The application stores a key entered in the GUI as plaintext in `config.json`; protect access to your computer and do not share this file.
- Keep `.env` and `config.json` out of version control. They are listed in `.gitignore`, but ignore rules do not remove files that have already been committed.
- Before committing, review `git status` and `git diff` and verify that no secrets or personal files are included.
- If a key is exposed or committed, revoke it with OpenSubtitles, create a replacement, and remove the exposed value from repository history as needed. Deleting the file in a later commit does not erase earlier copies.
- Install dependencies from trusted sources and review changes to dependency lists before installing or building the application.

## Git workflow

- Create a branch for each feature or fix, and keep commits focused on one change.
- Review staged changes with `git diff --cached` before committing.
- Use clear commit messages that describe the change, such as `Fix subtitle filename matching`.
- Do not commit virtual environments, build output, API keys, or local configuration. The repository's `.gitignore` excludes common local files and build artifacts.

## Project structure

```text
.
├── .env.example
├── .gitignore
├── README.md
├── app.py       # CustomTkinter interface and event handlers
└── core.py      # Sorting, validation, file operations, and API integration
```


