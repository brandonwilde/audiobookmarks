import json
import os
import re
import subprocess

from aitools.media_tools.audio_tools import convert_to_mp3, transcribe
from aitools.media_tools.text_tools import prompt_llm

# If there are multiple audio files for a bookmark,
# assume the shortest one starts at the bookmark,
# and the longest one is the entire chapter.


def get_duration(filepath):
    """
    Get the duration of an audio file in seconds using ffprobe.
    """
    duration = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True
    ).stdout
    return round(float(duration))


def clip_audio_file(start_time, end_time, file_path):
    """
    Clip audio file from start_time to end_time using ffmpeg.
    """
    clip_path = file_path.replace(".mp3", f"_clip{start_time}-{end_time}.mp3")
    if os.path.exists(clip_path):
        return clip_path # Skip
        
    subprocess.run(
        ["ffmpeg", "-y", "-i", file_path, "-ss", str(start_time), "-to", str(end_time), clip_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
    return clip_path


def transcribe_audio_file(bookmark_number, data_dir):
    # Find the audio file for the bookmark
    file_pattern = rf"audio_file_{bookmark_number}(_.*)?.mp3"
    audio_files = [f for f in os.listdir(data_dir) if re.match(file_pattern, f)]
    
    # Assume shortest file is the one that starts at the bookmark
    shortest_file = min(audio_files, key=lambda f: get_duration(os.path.join(data_dir, f)))
    
    # Clip 5 minutes from the start of the file
    clip_audio_file(0, 300, os.path.join(data_dir, shortest_file))

    # Transcribe the clipped audio file
    clipped_file = os.path.join(data_dir, shortest_file.replace(".mp3", "_clip0-300.mp3"))
    response = transcribe(clipped_file)
    return response.text

