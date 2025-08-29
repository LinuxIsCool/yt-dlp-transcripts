#!/usr/bin/env python3
"""
Unified YouTube content downloader
Supports: individual videos, playlists, channel videos, and channel playlists
"""

import yt_dlp
import csv
import os
import sys
from youtube_transcript_api import YouTubeTranscriptApi
import click
from urllib.parse import urlparse, parse_qs
import re
import requests
import json
import xml.etree.ElementTree as ET

# Handle large CSV fields
maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt // 10)


def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    # Handle youtu.be format
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]
    
    # Handle youtube.com format
    parsed = urlparse(url)
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            query = parse_qs(parsed.query)
            return query.get('v', [None])[0]
        elif parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        elif parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]
    
    # Fallback to regex
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_video_info(video_url, source_type=None, source_name=None, source_url=None):
    """Get detailed information about a video including transcript."""
    ydl_opts = {
        'writesubtitles': True,
        'allsubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'vtt',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            video_id = info.get('id')
            
            # Get transcript - try multiple methods
            transcript_text = ""
            
            # Method 1: Try youtube-transcript-api first (usually better formatting)
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = ' '.join([entry['text'] for entry in transcript])
                print(f"  ✓ Transcript obtained via API")
            except Exception as e:
                # Method 2: Fallback to yt-dlp's subtitle extraction
                try:
                    if 'subtitles' in info:
                        # Try to get English subtitles
                        for lang in ['en', 'en-US', 'en-GB', 'a.en']:
                            if lang in info['subtitles']:
                                # Get the subtitle URL and download it
                                subtitle_info = info['subtitles'][lang]
                                if subtitle_info and len(subtitle_info) > 0:
                                    # yt-dlp provides subtitle data in various formats
                                    # Prefer json3, srv1, or vtt formats (skip hls manifests)
                                    preferred_formats = ['json3', 'srv1', 'srv2', 'srv3', 'vtt']
                                    
                                    # Sort subtitle_info to prioritize preferred formats
                                    sorted_subs = sorted(subtitle_info, 
                                                       key=lambda x: preferred_formats.index(x.get('ext', 'other')) 
                                                       if x.get('ext') in preferred_formats else 999)
                                    
                                    for sub in sorted_subs:
                                        if 'url' in sub and sub.get('ext') != 'vtt':  # Skip HLS manifests
                                            try:
                                                resp = requests.get(sub['url'], timeout=10)
                                                if resp.status_code == 200:
                                                    content = resp.text
                                                    
                                                    # Handle JSON format (json3)
                                                    if sub.get('ext') == 'json3':
                                                        data = json.loads(content)
                                                        if 'events' in data:
                                                            text_parts = []
                                                            for event in data['events']:
                                                                if 'segs' in event:
                                                                    for seg in event['segs']:
                                                                        if 'utf8' in seg:
                                                                            text_parts.append(seg['utf8'])
                                                            transcript_text = ' '.join(text_parts)
                                                    
                                                    # Handle SRV format (srv1, srv2, srv3)
                                                    elif sub.get('ext') in ['srv1', 'srv2', 'srv3']:
                                                        root = ET.fromstring(content)
                                                        text_parts = []
                                                        for text_elem in root.findall('.//text'):
                                                            if text_elem.text:
                                                                text_parts.append(text_elem.text)
                                                        transcript_text = ' '.join(text_parts)
                                                    
                                                    if transcript_text:
                                                        print(f"  ✓ Transcript obtained via yt-dlp subtitles ({lang}, {sub.get('ext')})")
                                                        break
                                            except Exception as e:
                                                continue
                                    if transcript_text:
                                        break
                    
                    # Method 3: Try automatic captions if no manual subtitles
                    if not transcript_text and 'automatic_captions' in info:
                        for lang in ['en', 'en-US', 'en-GB', 'a.en']:
                            if lang in info['automatic_captions']:
                                caption_info = info['automatic_captions'][lang]
                                if caption_info and len(caption_info) > 0:
                                    # Use same logic as subtitles
                                    preferred_formats = ['json3', 'srv1', 'srv2', 'srv3', 'vtt']
                                    sorted_caps = sorted(caption_info, 
                                                       key=lambda x: preferred_formats.index(x.get('ext', 'other')) 
                                                       if x.get('ext') in preferred_formats else 999)
                                    
                                    for cap in sorted_caps:
                                        if 'url' in cap and cap.get('ext') != 'vtt':
                                            try:
                                                resp = requests.get(cap['url'], timeout=10)
                                                if resp.status_code == 200:
                                                    content = resp.text
                                                    
                                                    # Handle JSON format (json3)
                                                    if cap.get('ext') == 'json3':
                                                        data = json.loads(content)
                                                        if 'events' in data:
                                                            text_parts = []
                                                            for event in data['events']:
                                                                if 'segs' in event:
                                                                    for seg in event['segs']:
                                                                        if 'utf8' in seg:
                                                                            text_parts.append(seg['utf8'])
                                                            transcript_text = ' '.join(text_parts)
                                                    
                                                    # Handle SRV format (srv1, srv2, srv3)
                                                    elif cap.get('ext') in ['srv1', 'srv2', 'srv3']:
                                                        root = ET.fromstring(content)
                                                        text_parts = []
                                                        for text_elem in root.findall('.//text'):
                                                            if text_elem.text:
                                                                text_parts.append(text_elem.text)
                                                        transcript_text = ' '.join(text_parts)
                                                    
                                                    if transcript_text:
                                                        print(f"  ✓ Transcript obtained via auto-captions ({lang}, {cap.get('ext')})")
                                                        break
                                            except Exception as e:
                                                continue
                                    if transcript_text:
                                        break
                    
                    if not transcript_text:
                        print(f"  Note: No transcript available for {video_id}")
                        
                except Exception as fallback_error:
                    print(f"  Note: Could not extract transcript for {video_id}")
            
            result = {
                'video_id': video_id,
                'title': info.get('title', ''),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'description': info.get('description', ''),
                'transcript': transcript_text,
                'upload_date': info.get('upload_date', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'channel': info.get('channel', ''),
                'channel_id': info.get('channel_id', ''),
            }
            
            # Add source information based on type
            if source_type == 'playlist':
                result['playlist_name'] = source_name
                result['playlist_url'] = source_url
            elif source_type == 'channel':
                result['channel_source_url'] = source_url
            
            return result
            
        except Exception as e:
            print(f"Error processing video {video_url}: {str(e)}")
            return None


def process_single_video(video_url, output_file):
    """Process a single video."""
    video_id = extract_video_id(video_url)
    if not video_id:
        print(f"Error: Could not extract video ID from {video_url}")
        return
    
    # Check if already processed
    processed_videos = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            processed_videos = set(row.get('video_id', '') for row in reader)
    
    if video_id in processed_videos:
        print(f"Video already processed: {video_id}")
        return
    
    print(f"Processing video: {video_url}")
    video_info = get_video_info(video_url)
    
    if video_info:
        # Write to CSV
        file_exists = os.path.exists(output_file)
        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = list(video_info.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists or f.tell() == 0:
                writer.writeheader()
            
            writer.writerow(video_info)
            print(f"✓ Successfully processed: {video_info['title']}")


def process_playlist(playlist_url, output_file):
    """Process all videos in a playlist."""
    print(f"Processing playlist: {playlist_url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'ignoreerrors': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            if not playlist_info.get('entries'):
                print(f"No videos found in playlist: {playlist_url}")
                return
            
            playlist_title = playlist_info.get('title', 'Unknown Playlist')
            videos = playlist_info['entries']
            print(f"Found {len(videos)} videos in playlist: {playlist_title}")
            
        except Exception as e:
            print(f"Error extracting playlist info: {str(e)}")
            return
    
    # Check for already processed videos
    processed_videos = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            processed_videos = set(row.get('video_id', '') for row in reader)
    
    # Process each video
    file_exists = os.path.exists(output_file)
    first_write = not file_exists
    
    for i, video in enumerate(videos, 1):
        if not video:
            continue
        
        video_id = video.get('id')
        if video_id in processed_videos:
            print(f"[{i}/{len(videos)}] Skipping already processed: {video_id}")
            continue
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[{i}/{len(videos)}] Processing: {video.get('title', video_id)}")
        
        video_info = get_video_info(
            video_url,
            source_type='playlist',
            source_name=playlist_title,
            source_url=playlist_url
        )
        
        if video_info:
            with open(output_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(video_info.keys()))
                
                if first_write:
                    writer.writeheader()
                    first_write = False
                
                writer.writerow(video_info)
                f.flush()
                processed_videos.add(video_id)
                print(f"  ✓ Successfully saved")


def process_channel(channel_url, output_file, mode='videos'):
    """Process all videos or all playlists from a channel."""
    if mode == 'videos':
        # Ensure we're on the videos tab
        if '/videos' not in channel_url:
            channel_url = channel_url.rstrip('/') + '/videos'
        print(f"Processing channel videos: {channel_url}")
    else:
        # Ensure we're on the playlists tab
        if '/playlists' not in channel_url:
            channel_url = channel_url.rstrip('/') + '/playlists'
        print(f"Processing channel playlists: {channel_url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'ignoreerrors': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            channel_info = ydl.extract_info(channel_url, download=False)
            if 'entries' not in channel_info:
                print(f"Error: Could not find content at {channel_url}")
                return
            
            entries = [e for e in channel_info['entries'] if e]
            
            if mode == 'videos':
                print(f"Found {len(entries)} videos")
                process_channel_videos(entries, channel_url, output_file)
            else:
                print(f"Found {len(entries)} playlists")
                for i, playlist in enumerate(entries, 1):
                    playlist_url = playlist.get('url')
                    playlist_title = playlist.get('title', 'Unknown Playlist')
                    print(f"\n[{i}/{len(entries)}] Processing playlist: {playlist_title}")
                    process_playlist(playlist_url, output_file)
                    
        except Exception as e:
            print(f"Error processing channel: {str(e)}")


def process_channel_videos(videos, channel_url, output_file):
    """Process a list of video entries from a channel."""
    # Check for already processed videos
    processed_videos = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            processed_videos = set(row.get('video_id', '') for row in reader)
    
    file_exists = os.path.exists(output_file)
    first_write = not file_exists
    
    for i, video in enumerate(videos, 1):
        video_id = video.get('id')
        if video_id in processed_videos:
            print(f"[{i}/{len(videos)}] Skipping already processed: {video_id}")
            continue
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[{i}/{len(videos)}] Processing: {video.get('title', video_id)}")
        
        video_info = get_video_info(
            video_url,
            source_type='channel',
            source_url=channel_url
        )
        
        if video_info:
            with open(output_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(video_info.keys()))
                
                if first_write:
                    writer.writeheader()
                    first_write = False
                
                writer.writerow(video_info)
                f.flush()
                processed_videos.add(video_id)
                print(f"  ✓ Successfully saved")


def detect_url_type(url):
    """Detect the type of YouTube URL."""
    # First check if it's actually a YouTube URL
    if not any(domain in url for domain in ['youtube.com', 'youtu.be', 'youtube-nocookie.com']):
        return 'unknown'
    
    # Check for channel first (before checking for 'playlist' keyword)
    if '@' in url or '/channel/' in url or '/c/' in url or '/user/' in url:
        if '/playlists' in url:
            return 'channel_playlists'
        elif '/videos' in url:
            return 'channel_videos'
        else:
            # Default to videos for channel URLs without specific tab
            return 'channel_videos'
    
    # Check for video ID patterns
    if extract_video_id(url) and 'playlist' not in url:
        return 'video'
    
    # Check for playlist
    if 'playlist' in url or 'list=' in url:
        return 'playlist'
    
    return 'unknown'


@click.command()
@click.option('--url', '-u', required=True, help='YouTube URL (auto-detects type: video, playlist, channel, or channel playlists)')
@click.option('--output', '-o', default='video_info.csv', help='Output CSV file (default: video_info.csv)')
def main(url, output):
    """
    Download YouTube content information and transcripts.
    
    Automatically detects and processes:
    - Individual videos
    - Playlists
    - Channel videos (/videos or channel main page)
    - Channel playlists (/playlists)
    
    Examples:
    
        yt-dlp-transcripts -u "https://www.youtube.com/watch?v=VIDEO_ID" -o video.csv
        yt-dlp-transcripts -u "https://www.youtube.com/playlist?list=PLAYLIST_ID" -o playlist.csv
        yt-dlp-transcripts -u "https://www.youtube.com/@channelname/videos" -o channel.csv
        yt-dlp-transcripts -u "https://www.youtube.com/@channelname/playlists" -o playlists.csv
    """
    
    url_type = detect_url_type(url)
    print(f"Detected URL type: {url_type}")
    
    if url_type == 'video':
        process_single_video(url, output)
    elif url_type == 'playlist':
        process_playlist(url, output)
    elif url_type == 'channel_videos':
        process_channel(url, output, mode='videos')
    elif url_type == 'channel_playlists':
        process_channel(url, output, mode='playlists')
    else:
        print(f"Error: Could not determine URL type for: {url}")
        print("Supported URL formats:")
        print("  - Video: https://www.youtube.com/watch?v=VIDEO_ID")
        print("  - Playlist: https://www.youtube.com/playlist?list=PLAYLIST_ID")
        print("  - Channel videos: https://www.youtube.com/@channel/videos")
        print("  - Channel playlists: https://www.youtube.com/@channel/playlists")
        return
    
    print(f"\nOutput saved to: {output}")


if __name__ == "__main__":
    main()