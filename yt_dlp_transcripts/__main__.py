#!/usr/bin/env python3
"""
Allow package to be run as a module: python -m yt_dlp_transcripts
"""

from .core import main

if __name__ == "__main__":
    main()