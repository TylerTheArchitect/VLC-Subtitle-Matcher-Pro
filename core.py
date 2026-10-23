import re
from pathlib import Path

# Supported file extensions for validation
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.flv', '.webm'}
SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.sub', '.vtt'}

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
            if not subtitle.exists() or not video.exists():
                results.append(f"Skipped: File missing on disk -> {subtitle.name}")
                continue
                
            # Validate extensions
            if subtitle.suffix.lower() not in SUBTITLE_EXTENSIONS:
                results.append(f"Skipped: Invalid subtitle type -> {subtitle.name}")
                continue
            if video.suffix.lower() not in VIDEO_EXTENSIONS:
                results.append(f"Skipped: Invalid video type -> {video.name}")
                continue

            new_stem = video.stem
            sub_extension = subtitle.suffix
            new_subtitle_path = subtitle.with_name(new_stem + sub_extension)
            
            # Target collision check
            if new_subtitle_path.exists() and new_subtitle_path != subtitle:
                results.append(f"Skipped: Target file already exists -> {new_subtitle_path.name}")
                continue
                
            subtitle.rename(new_subtitle_path)
            results.append(f"Success: {subtitle.name} -> {new_subtitle_path.name}")
            
        except PermissionError:
            results.append(f"Permission Error: '{subtitle.name}' is open in another app (like VLC).")
        except Exception as e:
            results.append(f"Error on {subtitle.name}: {str(e)}")
            
    results.append("Batch process finished.")
    return results
