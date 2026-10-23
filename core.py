from pathlib import Path

def rename_subtitles(video_paths, subtitle_paths):
    results = []

    videos = sorted(([Path(v) for v in video_paths]))
    subtitles = sorted(([Path(s) for s in subtitle_paths]))

    if len(videos) != len(subtitles):
        return [f"Warning: Number of videos ({len(videos)}) does not match subtitles ({len(subtitles)})"]
    
    for video, subtitle in zip(videos, subtitles):
        try:
            new_stem = video.stem
            sub_extension = subtitle.suffix

            new_subtitle_path = subtitle.with_name(new_stem + sub_extension)
            subtitle.rename(new_subtitle_path)
            results.append(f"Successfully renamed: {subtitle.name} -> {new_subtitle_path.name}")

        except Exception as e:
            results.append(f"Error renaming {subtitle.name}: {str(e)}")
    
    return results

video_paths = ["Your_Lie_in_April_480P_S01_EP01.mp4", "Your_Lie_in_April_480P_S01_EP02.mp4"]
subtitle_paths = ["Your lie in April (Sub) - 01.enUS.ass", "Your lie in April (Sub) - 02.enUS.ass" ]

print(rename_subtitles(video_paths, subtitle_paths))