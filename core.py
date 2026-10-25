import re
from pathlib import Path
import requests
from dotenv import load_dotenv
import os
import json
import concurrent.futures

# Load variables from the local .env file if present
load_dotenv()

# Supported file extensions for validation
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.flv', '.webm'}
SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.sub', '.vtt'}

# OpenSubtitles API Configuration

CONFIG_FILE = Path("config.json")
BASE_URL = "https://api.opensubtitles.com/api/v1/subtitles"
OPEN_SUBTITLES_API_KEY=os.getenv("OPEN_SUBTITLES_API_KEY", "")
def save_api_key(api_key):
    config = {"api_key":api_key.strip()}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        return True
    
    except Exception as e:
        return False

def load_api_key():
    if CONFIG_FILE.exists():
        try:
            with open (CONFIG_FILE, "r") as f:
                data=json.load(f)
                key=data.get("api_key", "")
                if key:
                    return key
        
        except Exception:
            pass
    
    return os.getenv("OPEN_SUBTITLES_API_KEY", "")

def natural_sort_key(path):
    """
    Splits filename into text and numeric parts so '10' is evaluated 
    numerically after '2' instead of alphabetically after '1'.
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', path.name)]

def scan_folder(folder_path):
    """
    Scans a directory and automatically finds and naturally sorts all 
    valid video and subtitle files.
    """
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        return [], []
        
    videos = sorted([f for f in path.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS], key=natural_sort_key)
    subtitles = sorted([f for f in path.iterdir() if f.is_file() and f.suffix.lower() in SUBTITLE_EXTENSIONS], key=natural_sort_key)
    
    return videos, subtitles

def preview_renames(video_paths, subtitle_paths):
    """
    Generates a dry-run preview list showing how subtitles will be renamed 
    without actually touching the disk.
    """
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
    """
    Executes the actual renaming process with validation, natural sorting,
    and safe collision checks.
    """
    videos = sorted([Path(v) for v in video_paths], key=natural_sort_key)
    subtitles = sorted([Path(s) for s in subtitle_paths], key=natural_sort_key)
    
    if not videos or not subtitles:
        return ["Error: Video list or subtitle list is empty."]
        
    if len(videos) != len(subtitles):
        return [f"Error: Count mismatch! Found {len(videos)} video(s) and {len(subtitles)} subtitle(s)."]
        
    results = ["Starting batch rename process..."]
    
    for video, subtitle in zip(videos, subtitles):
        try:
            sub_path = Path(subtitle)
            vid_path = Path(video)
            
            if not sub_path.exists() or not vid_path.exists():
                results.append(f"Skipped: File missing on disk -> {sub_path.name}")
                continue
                
            # Validate extensions
            if sub_path.suffix.lower() not in SUBTITLE_EXTENSIONS:
                results.append(f"Skipped: Invalid subtitle type -> {sub_path.name}")
                continue
            if vid_path.suffix.lower() not in VIDEO_EXTENSIONS:
                results.append(f"Skipped: Invalid video type -> {vid_path.name}")
                continue

            new_stem = vid_path.stem
            sub_extension = sub_path.suffix
            new_subtitle_path = sub_path.with_name(new_stem + sub_extension)
            
            # Target collision check
            if new_subtitle_path.exists() and new_subtitle_path != sub_path:
                results.append(f"Skipped: Target file already exists -> {new_subtitle_path.name}")
                continue
                
            sub_path.rename(new_subtitle_path)
            results.append(f"Success: {sub_path.name} -> {new_subtitle_path.name}")
            
        except PermissionError:
            results.append(f"Permission Error: '{Path(subtitle).name}' is open in another app (like VLC).")
        except Exception as e:
            results.append(f"Error on {Path(subtitle).name}: {str(e)}")
            
    results.append("Batch process finished.")
    return results

def process_single_video(v_path, headers, language):
    """Worker function to process and download a single video's subtitle."""
    video = Path(v_path)
    if not video.exists():
        return f"Skipped: File missing on disk -> {video.name}", False
        
    query_title = video.stem.replace(".", " ").replace("_", " ")
    params = {
        "query": query_title,
        "languages": language
    }

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        
        if response.status_code == 401:
            return "API Error: Unauthorized. Check your OpenSubtitles API Key.", False
        elif response.status_code != 200:
            return f"API Error for {video.name}: Status code {response.status_code}", False

        data = response.json().get("data", [])
        
        if not data:
            return f"No subtitles found online for: {video.name}", False

        file_id = data[0]["attributes"]["files"][0]["file_id"]
        
        download_endpoint = "https://api.opensubtitles.com/api/v1/download"
        dl_response = requests.post(download_endpoint, headers=headers, json={"file_id": file_id}, timeout=10)
        
        if dl_response.status_code == 200:
            dl_data = dl_response.json()
            link = dl_data.get("link")
            file_name = dl_data.get("file_name", video.stem + ".srt")
            
            sub_content = requests.get(link, timeout=10)
            target_sub_path = video.with_name(video.stem + Path(file_name).suffix)
            
            with open(target_sub_path, "wb") as f:
                f.write(sub_content.content)
                
            return f"Successfully downloaded: {target_sub_path.name}", True
        else:
            return f"Failed to retrieve download link for {video.name}", False

    except requests.exceptions.SSLError:
        return f"SSL Error for '{video.name}': Secure connection dropped.", False
    except requests.exceptions.ConnectionError:
        return f"Connection Error for '{video.name}': Could not reach server.", False
    except requests.exceptions.Timeout:
        return f"Timeout Error for '{video.name}': Request timed out.", False
    except Exception as e:
        return f"Network/API Error for {video.name}: {str(e)}", False

def download_online_subtitles(video_paths, language="en", log_callback=None):
    """
    Downloads subtitles concurrently across multiple worker threads 
    using ThreadPoolExecutor for lightning-fast batch processing.
    """
    if not video_paths:
        return ["Error: No video files provided for online search."]
        
    api_key = load_api_key()
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return ["Error: No API key found. Please enter and save your OpenSubtitles API key in the app sidebar."]

    headers = {
        "Api-Key": api_key,
        "User-Agent": "VLCSubtitleMatcherPro v1.0"
    }

    results = ["Starting concurrent online subtitle search..."]
    if log_callback:
        log_callback("Starting concurrent online subtitle search...")

    success_count = 0
    fail_count = 0

    # Use ThreadPoolExecutor to run up to 5 downloads in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks to the thread pool
        future_to_video = {
            executor.submit(process_single_video, v_path, headers, language): v_path 
            for v_path in video_paths
        }
        
        # As each thread completes, grab its result
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
    return results
