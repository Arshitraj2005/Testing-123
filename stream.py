# stream.py
import shlex
import os

def build_ffmpeg_command(stream_key, video_url, title="", loop=False):
    """
    Returns either a list (recommended) or a shell string command that will run ffmpeg/yt-dlp.
    Note: server must have ffmpeg (and yt-dlp for youtube links) installed.
    """
    rtmp = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    # If youtube link -> use yt-dlp piping to ffmpeg (shell required)
    if "youtube.com" in video_url or "youtu.be" in video_url:
        # This uses shell piping => returned value is a shell string
        cmd = f'yt-dlp -f best -o - "{video_url}" | ffmpeg -re -i - -c:v libx264 -preset veryfast -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 -c:a aac -b:a 160k -f flv "{rtmp}"'
        return cmd

    # Otherwise direct url/file -> use ffmpeg directly (list form)
    cmd = [
        "ffmpeg",
        "-re",
        # loop for local files (if needed)
        *(["-stream_loop", "-1"] if loop and not video_url.startswith("http") else []),
        "-i", video_url,
        "-c:v", "libx264", "-preset", "veryfast", "-maxrate", "3000k", "-bufsize", "6000k",
        "-pix_fmt", "yuv420p", "-g", "50",
        "-c:a", "aac", "-b:a", "160k",
        "-f", "flv", rtmp
    ]
    return cmd
