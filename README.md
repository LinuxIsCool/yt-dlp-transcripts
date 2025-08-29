# yt-dlp-transcripts

A powerful Python tool for extracting video information and transcripts from YouTube videos, playlists, channels, and channel playlists. Built on top of `yt-dlp` and `youtube-transcript-api`.

## Features

- 📹 **Single Video Processing** - Extract metadata and transcripts from individual YouTube videos
- 📚 **Playlist Support** - Process entire playlists with progress tracking
- 📺 **Channel Videos** - Download information from all videos on a channel
- 🗂️ **Channel Playlists** - Process all playlists from a channel
- 🔄 **Resume Capability** - Automatically skip already processed videos
- 🎯 **Auto-Detection** - Automatically detect URL type (video/playlist/channel)
- 📊 **Rich Metadata** - Extract title, description, upload date, duration, view count, and more
- 📝 **Transcript Extraction** - Get full video transcripts when available
- 💾 **CSV Export** - Save all data in easily accessible CSV format

## Installation

### Via pip 
```bash
pip install yt-dlp-transcripts

# As a command-line tool (after pip install)
yt-dlp-transcripts -u "https://www.youtube.com/watch?v=VIDEO_ID" -o video.csv
```

### To run from source
```bash
git clone https://github.com/yourusername/yt-dlp-transcripts.git
cd yt-dlp-transcripts
poetry install
poetry shell

# With poetry (after poetry install and poetry shell)
python -m yt_dlp_transcripts -u "https://www.youtube.com/watch?v=VIDEO_ID" -o video.csv
```

## Usage

```bash
yt-dlp-transcripts -u "https://www.youtube.com/watch?v=VIDEO_ID" -o output.csv
yt-dlp-transcripts -u "https://www.youtube.com/playlist?list=PLAYLIST_ID" -o output.csv
yt-dlp-transcripts -u "https://www.youtube.com/@channelname/videos" -o output.csv
yt-dlp-transcripts -u "https://www.youtube.com/@channelname/playlists" -o output.csv
```

### Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--url` | `-u` | YouTube URL (auto-detects type) | `https://youtube.com/...` |
| `--output` | `-o` | Output CSV file path | `output.csv` |
| `--help` | | Show help message | (flag, no value) |

## Output Format

The tool exports data to CSV with the following fields:

### Common Fields
- `video_id` - YouTube video ID
- `title` - Video title
- `url` - Video URL
- `description` - Video description
- `transcript` - Full video transcript (when available)
- `upload_date` - Upload date (YYYYMMDD format)
- `duration` - Video duration in seconds
- `view_count` - Number of views
- `channel` - Channel name
- `channel_id` - Channel ID

### Additional Fields for Playlists
- `playlist_name` - Name of the source playlist
- `playlist_url` - URL of the source playlist

### Additional Fields for Channel Videos
- `channel_source_url` - URL of the channel page

## Examples

### Research and Analysis
```bash
# Analyze a conference talk playlist
yt-dlp-transcripts -u "https://www.youtube.com/playlist?list=PLconf2024" -o conference_talks.csv

# Extract all videos from an educational channel
yt-dlp-transcripts -u "https://www.youtube.com/@3blue1brown/videos" -o math_videos.csv
```

### Content Creation
```bash
# Get transcripts from your competitor's channel
yt-dlp-transcripts -u "https://www.youtube.com/@competitor/videos" -o competitor_analysis.csv

# Archive your own channel's content
yt-dlp-transcripts -u "https://www.youtube.com/@yourchannel/videos" -o my_backup.csv
```

### Academic Research
```bash
# Collect lecture series for analysis
yt-dlp-transcripts -u "https://www.youtube.com/playlist?list=PLlecture" -o lectures.csv

# Get transcripts from multiple related playlists
yt-dlp-transcripts -u "https://www.youtube.com/@university/playlists" -o all_courses.csv
```

### Python API Usage

```python
from yt_dlp_transcripts import (
    get_video_info,
    process_single_video,
    process_playlist,
    process_channel,
    detect_url_type
)

# Get video information as dictionary
video_data = get_video_info("https://www.youtube.com/watch?v=VIDEO_ID")
print(video_data['title'])
print(video_data['transcript'])
print(video_data['duration'])

# Process content and save to CSV
process_single_video("https://www.youtube.com/watch?v=VIDEO_ID", "output.csv")
process_playlist("https://www.youtube.com/playlist?list=PLAYLIST_ID", "output.csv")
process_channel("https://www.youtube.com/@channel/videos", "output.csv", mode='videos')

# Auto-detect URL type
url_type = detect_url_type("https://www.youtube.com/watch?v=VIDEO_ID")  # Returns: 'video'
```

## Features in Detail

### Resume Capability
The tool automatically tracks processed videos and skips them on subsequent runs. This allows you to:
- Interrupt and resume large downloads
- Update your dataset with only new videos
- Avoid redundant API calls

### Progress Tracking
When processing multiple videos, the tool shows:
- Current video number and total count
- Video title being processed
- Success/skip status for each video

### Error Handling
- Gracefully handles missing transcripts
- Continues processing even if individual videos fail
- Provides clear error messages for troubleshooting

### Rate Limiting
The tool respects YouTube's rate limits. If you encounter 429 errors:
- The tool will continue processing and get available metadata
- Transcripts may be unavailable during rate limiting
- Consider adding delays or processing in smaller batches


## Requirements

- Python 3.9+
- yt-dlp
- youtube-transcript-api
- click

## Limitations

- **Transcript Availability**: Not all videos have transcripts available
- **Rate Limiting**: YouTube may rate limit requests with large datasets
- **Private Videos**: Cannot access private or age-restricted content without authentication
- **API Changes**: YouTube's API may change, affecting functionality

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Running Tests
```bash
pytest
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Transcript extraction via [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)
- CLI interface powered by [click](https://click.palletsprojects.com/)

## Author

[Shawn Anderson](https://linuxiscool.xyz)

## Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/yourusername/yt-dlp-transcripts/issues)
- Check existing issues for solutions
- Provide detailed error messages and URLs (when possible) for debugging

## Changelog

### v0.1.0 (2025-08-28)
- Initial release
- Support for videos, playlists, channels, and channel playlists
- Auto-detection of URL types
- Resume capability for interrupted downloads
- CSV export with comprehensive metadata
