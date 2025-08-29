"""
yt-dlp-transcripts: Extract video information and transcripts from YouTube
"""

__version__ = "0.1.1"
__author__ = "Shawn Anderson"
__email__ = "shawn@longtailfinancial.com"

from .core import (
    main,
    get_video_info,
    process_single_video,
    process_playlist,
    process_channel,
    detect_url_type,
    extract_video_id
)

__all__ = [
    'main',
    'get_video_info',
    'process_single_video', 
    'process_playlist',
    'process_channel',
    'detect_url_type',
    'extract_video_id'
]