from pathlib import Path

def rename_subtitles(video_paths, subtitle_paths):
    """
    Takes a list of video file paths and subtitle file paths,
    sorts them, and safely renames each subtitle file with comprehensive error handling.
    """
    results = []
    
    # Convert string paths to Path objects
    videos = sorted([Path(v) for v in video_paths])
    subtitles = sorted([Path(s) for s in subtitle_paths])
    
    # --- Exception Check 1: Empty lists ---
    if not videos or not subtitles:
        return ["Error: Video list or subtitle list is empty."]
    
    # --- Exception Check 2: Count Mismatch ---
    if len(videos) != len(subtitles):
        return [
            f"Error: Count mismatch! You selected {len(videos)} video(s) "
            f"and {len(subtitles)} subtitle(s). Counts must match for 1:1 pairing."
        ]
    
    results.append("Starting batch rename process...")
    
    # Pair and rename safely
    for video, subtitle in zip(videos, subtitles):
        try:
            # --- Exception Check 3: Source file exists ---
            if not subtitle.exists():
                results.append(f"Skipped: Subtitle file not found on disk -> {subtitle.name}")
                continue
                
            if not video.exists():
                results.append(f"Skipped: Video file not found on disk -> {video.name}")
                continue

            # Extract naming components
            new_stem = video.stem
            sub_extension = subtitle.suffix
            new_subtitle_path = subtitle.with_name(new_stem + sub_extension)
            
            # --- Exception Check 4: Target collision avoidance ---
            if new_subtitle_path.exists() and new_subtitle_path != subtitle:
                results.append(f"Skipped: Target file already exists -> {new_subtitle_path.name}")
                continue
                
            # Perform the rename operation
            subtitle.rename(new_subtitle_path)
            results.append(f"Success: {subtitle.name} -> {new_subtitle_path.name}")
            
        except PermissionError:
            results.append(
                f"Permission Error: Could not rename '{subtitle.name}'. "
                f"Is the file currently open in VLC or another program?"
            )
        except OSError as e:
            results.append(f"OS Error on {subtitle.name}: {str(e)}")
        except Exception as e:
            results.append(f"Unexpected Error on {subtitle.name}: {str(e)}")
            
    results.append("Batch process finished.")
    return results
