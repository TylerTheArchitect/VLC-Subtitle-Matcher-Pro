import os
import json
import re
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load variables from local .env if present
load_dotenv()

# Setup Persistent Logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Supported file extensions
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.flv', '.webm'}
SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.sub', '.vtt'}

CONFIG_FILE = Path("config.json")
BASE_URL = "https://api.opensubtitles.com/api/v1/subtitles"

def save_config(api_key=None, last_folder=None):
    """Saves settings (API key and last folder) to local config.json."""
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except Exception:
            pass
            
    if api_key is not None:
        config["api_key"] = api_key.strip()
    if last_folder is not None:
        config["last_folder"] = str(last_folder)
        
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        logging.info("Configuration saved successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to save config: {e}")
        return False

def load_config():
    """Loads configuration from config.json."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def load_api_key():
    """Loads API key from config.json first, falling back to .env / system environment variables."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                key = config.get("api_key", "").strip()
                if key:
                    return key
        except Exception:
            pass
    return os.getenv("OPEN_SUBTITLES_API_KEY", "").strip()


def natural_sort_key(path):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', path.name)]

def scan_folder(folder_path):
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        logging.warning(f"Invalid folder path scanned: {folder_path}")
        return [], []
        
    videos = sorted([f for f in path.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS], key=natural_sort_key)
    subtitles = sorted([f for f in path.iterdir() if f.is_file() and f.suffix.lower() in SUBTITLE_EXTENSIONS], key=natural_sort_key)
    
    logging.info(f"Scanned folder {path.name}: Found {len(videos)} videos, {len(subtitles)} subtitles.")
    return videos, subtitles

def preview_renames(video_paths, subtitle_paths):
    videos = sorted([Path(v) for v in video_paths], key=natural_sort_key)
    subtitles = sorted([Path(s) for s in subtitle_paths], key=natural_sort_key)
    
    if not videos or not subtitles:
        return ["Error: Video list or subtitle list is empty."]
        
    if len(videos) != len(subtitles):
        return [f"Error: Count mismatch! Found {len(videos)} video(s) and {len(subtitles)} subtitle(s)."]
        
    previews = []
    for video, subtitle in zip(videos, subtitles):
        new_stem = video.stem
        sub_extension = subtitle.suffix
        new_subtitle_path = subtitle.with_name(new_stem + sub_extension)
        previews.append(f"PREVIEW: {subtitle.name} -> {new_subtitle_path.name}")
        
    return previews

def rename_subtitles(video_paths, subtitle_paths):
    videos = sorted([Path(v) for v in video_paths], key=natural_sort_key)
    subtitles = sorted([Path(s) for s in subtitle_paths], key=natural_sort_key)
    
    if not videos or not subtitles:
        return ["Error: Video list or subtitle list is empty."]
        
    if len(videos) != len(subtitles):
        return [f"Error: Count mismatch! Found {len(videos)} video(s) and {len(subtitles)} subtitle(s)."]
        
    results = ["Starting batch rename process..."]
    logging.info("Starting batch rename execution.")
    
    for video, subtitle in zip(videos, subtitles):
        try:
            sub_path = Path(subtitle)
            vid_path = Path(video)
            
            if not sub_path.exists() or not vid_path.exists():
                results.append(f"Skipped: File missing on disk -> {sub_path.name}")
                continue
                
            if sub_path.suffix.lower() not in SUBTITLE_EXTENSIONS or vid_path.suffix.lower() not in VIDEO_EXTENSIONS:
                results.append(f"Skipped: Invalid extension type -> {sub_path.name}")
                continue

            new_stem = vid_path.stem
            new_subtitle_path = sub_path.with_name(new_stem + sub_path.suffix)
            
            if new_subtitle_path.exists() and new_subtitle_path != sub_path:
                results.append(f"Skipped: Target file already exists -> {new_subtitle_path.name}")
                continue
                
            sub_path.rename(new_subtitle_path)
            results.append(f"Success: {sub_path.name} -> {new_subtitle_path.name}")
            logging.info(f"Renamed: {sub_path.name} to {new_subtitle_path.name}")
            
        except PermissionError:
            msg = f"Permission Error: '{Path(subtitle).name}' is open in another app."
            results.append(msg)
            logging.error(msg)
        except Exception as e:
            msg = f"Error on {Path(subtitle).name}: {str(e)}"
            results.append(msg)
            logging.error(msg)
            
    results.append("Batch process finished.")
    return results

import concurrent.futures

def process_single_video(v_path, headers, language):
    video = Path(v_path)
    if not video.exists():
        return f"Skipped: File missing on disk -> {video.name}", False
        
    query_title = video.stem.replace(".", " ").replace("_", " ")
    params = {"query": query_title, "languages": language}

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return f"API Error for {video.name}: Status code {response.status_code}", False

        data = response.json().get("data", [])
        if not data:
            return f"No subtitles found online for: {video.name}", False

        file_id = data[0]["attributes"]["files"][0]["file_id"]
        dl_response = requests.post("https://api.opensubtitles.com/api/v1/download", headers=headers, json={"file_id": file_id}, timeout=10)
        
        if dl_response.status_code == 200:
            dl_data = dl_response.json()
            link = dl_data.get("link")
            file_name = dl_data.get("file_name", video.stem + ".srt")
            
            sub_content = requests.get(link, timeout=10)
            target_sub_path = video.with_name(video.stem + Path(file_name).suffix)
            
            with open(target_sub_path, "wb") as f:
                f.write(sub_content.content)
                
            logging.info(f"Downloaded online subtitle: {target_sub_path.name}")
            return f"Successfully downloaded: {target_sub_path.name}", True
        else:
            return f"Failed to retrieve download link for {video.name}", False

    except Exception as e:
        logging.error(f"Network/API Error for {video.name}: {e}")
        return f"Error for {video.name}: {str(e)}", False

def download_online_subtitles(video_paths, language="en", log_callback=None):
    api_key =load_api_key() 
    
    if not video_paths:
        return ["Error: No video files provided."]
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return ["Error: No API key found. Please save your OpenSubtitles API key in the sidebar."]

    headers = {"Api-Key": api_key, "User-Agent": "VLCSubtitleMatcherPro v1.0"}
    results = ["Starting concurrent online subtitle search..."]
    
    success_count, fail_count = 0, 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_video = {executor.submit(process_single_video, v, headers, language): v for v in video_paths}
        for future in concurrent.futures.as_completed(future_to_video):
            msg, success = future.result()
            results.append(msg)
            if log_callback:
                log_callback(msg)
            if success:
                success_count += 1
            else:
                fail_count += 1

    summary = f"Online search complete. Downloaded: {success_count}, Failed/Skipped: {fail_count}."
    results.append(summary)
    logging.info(summary)
    return results
