#!/usr/bin/env python3
"""
Test suite for yt_dlp_transcripts core functionality
"""

import pytest
import tempfile
import csv
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from yt_dlp_transcripts.core import (
    extract_video_id,
    detect_url_type,
    get_video_info,
    process_single_video,
    main
)


class TestExtractVideoId:
    """Test video ID extraction from various URL formats"""
    
    def test_standard_watch_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_watch_url_with_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXt&index=1"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_mobile_url(self):
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_invalid_url(self):
        url = "https://www.youtube.com/playlist?list=PLrAXt"
        assert extract_video_id(url) is None


class TestDetectUrlType:
    """Test URL type detection"""
    
    def test_video_url(self):
        assert detect_url_type("https://www.youtube.com/watch?v=VIDEO_ID") == "video"
        assert detect_url_type("https://youtu.be/VIDEO_ID") == "video"
    
    def test_playlist_url(self):
        assert detect_url_type("https://www.youtube.com/playlist?list=PLAYLIST_ID") == "playlist"
        # Note: watch URLs with list parameter are detected as videos (video takes precedence)
        assert detect_url_type("https://www.youtube.com/watch?v=VIDEO&list=PLAYLIST") == "video"
    
    def test_channel_videos_url(self):
        assert detect_url_type("https://www.youtube.com/@channel/videos") == "channel_videos"
        assert detect_url_type("https://www.youtube.com/c/channel/videos") == "channel_videos"
    
    def test_channel_playlists_url(self):
        # Should properly detect channel playlists URLs
        assert detect_url_type("https://www.youtube.com/@channel/playlists") == "channel_playlists"
    
    def test_channel_default_url(self):
        # Channel without specific tab defaults to videos
        assert detect_url_type("https://www.youtube.com/@channel") == "channel_videos"
    
    def test_unknown_url(self):
        assert detect_url_type("https://example.com") == "unknown"


class TestGetVideoInfo:
    """Test video information extraction"""
    
    @patch('yt_dlp_transcripts.core.yt_dlp.YoutubeDL')
    @patch('yt_dlp_transcripts.core.YouTubeTranscriptApi')
    def test_get_video_info_success(self, mock_transcript_api, mock_yt_dlp):
        # Mock yt-dlp response
        mock_ydl_instance = MagicMock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'id': 'test_id',
            'title': 'Test Video',
            'description': 'Test Description',
            'upload_date': '20240101',
            'duration': 300,
            'view_count': 1000,
            'channel': 'Test Channel',
            'channel_id': 'channel_123'
        }
        
        # Mock transcript API
        mock_transcript_api.get_transcript.return_value = [
            {'text': 'Hello'}, {'text': 'World'}
        ]
        
        result = get_video_info("https://www.youtube.com/watch?v=test_id")
        
        assert result['video_id'] == 'test_id'
        assert result['title'] == 'Test Video'
        assert result['transcript'] == 'Hello World'
        assert result['duration'] == 300
    
    @patch('yt_dlp_transcripts.core.yt_dlp.YoutubeDL')
    def test_get_video_info_no_transcript(self, mock_yt_dlp):
        # Mock yt-dlp response
        mock_ydl_instance = MagicMock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'id': 'test_id',
            'title': 'Test Video',
            'description': 'Test Description',
            'upload_date': '20240101',
            'duration': 300,
            'view_count': 1000,
            'channel': 'Test Channel',
            'channel_id': 'channel_123'
        }
        
        with patch('yt_dlp_transcripts.core.YouTubeTranscriptApi.get_transcript') as mock_transcript:
            mock_transcript.side_effect = Exception("No transcript")
            
            result = get_video_info("https://www.youtube.com/watch?v=test_id")
            
            assert result['video_id'] == 'test_id'
            assert result['transcript'] == ""  # Empty when no transcript


class TestCLI:
    """Test command-line interface"""
    
    def test_cli_no_args(self):
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0  # Should fail when required -u is missing
        assert "Missing option" in result.output or "required" in result.output.lower()
    
    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Download YouTube content information" in result.output
    
    @patch('yt_dlp_transcripts.core.process_single_video')
    def test_cli_auto_detect_video(self, mock_process):
        runner = CliRunner()
        result = runner.invoke(main, [
            '-u', 'https://www.youtube.com/watch?v=test_id',
            '-o', 'test.csv'
        ])
        assert "Detected URL type: video" in result.output
        mock_process.assert_called_once_with('https://www.youtube.com/watch?v=test_id', 'test.csv')
    
    @patch('yt_dlp_transcripts.core.process_playlist')
    def test_cli_auto_detect_playlist(self, mock_process):
        runner = CliRunner()
        result = runner.invoke(main, [
            '-u', 'https://www.youtube.com/playlist?list=PLtest',
            '-o', 'test.csv'
        ])
        assert "Detected URL type: playlist" in result.output
        mock_process.assert_called_once()
    
    @patch('yt_dlp_transcripts.core.process_channel')
    def test_cli_auto_detect_channel_videos(self, mock_process):
        runner = CliRunner()
        result = runner.invoke(main, [
            '-u', 'https://www.youtube.com/@channel/videos',
            '-o', 'test.csv'
        ])
        assert "Detected URL type: channel_videos" in result.output
        mock_process.assert_called_once_with('https://www.youtube.com/@channel/videos', 'test.csv', mode='videos')
    
    @patch('yt_dlp_transcripts.core.process_channel')
    def test_cli_auto_detect_channel_playlists(self, mock_process):
        runner = CliRunner()
        result = runner.invoke(main, [
            '-u', 'https://www.youtube.com/@channel/playlists',
            '-o', 'test.csv'
        ])
        assert "Detected URL type: channel_playlists" in result.output
        mock_process.assert_called_once_with('https://www.youtube.com/@channel/playlists', 'test.csv', mode='playlists')
    
    def test_cli_unknown_url(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            '-u', 'https://example.com/not-youtube',
            '-o', 'test.csv'
        ])
        assert "Error: Could not determine URL type" in result.output
        assert "Supported URL formats:" in result.output


class TestCSVOutput:
    """Test CSV output functionality"""
    
    @patch('yt_dlp_transcripts.core.get_video_info')
    def test_process_single_video_csv(self, mock_get_info):
        mock_get_info.return_value = {
            'video_id': 'test_id',
            'title': 'Test Video',
            'url': 'https://www.youtube.com/watch?v=test_id',
            'description': 'Test',
            'transcript': 'Test transcript',
            'upload_date': '20240101',
            'duration': 300,
            'view_count': 1000,
            'channel': 'Test Channel',
            'channel_id': 'ch_123'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            process_single_video('https://www.youtube.com/watch?v=test_id', temp_file)
            
            # Verify CSV was created correctly
            with open(temp_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['video_id'] == 'test_id'
                assert rows[0]['title'] == 'Test Video'
        finally:
            os.unlink(temp_file)
    
    @patch('yt_dlp_transcripts.core.get_video_info')
    def test_resume_capability(self, mock_get_info):
        """Test that already processed videos are skipped"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
            # Pre-populate with existing video
            writer = csv.DictWriter(f, fieldnames=['video_id', 'title'])
            writer.writeheader()
            writer.writerow({'video_id': 'existing_id', 'title': 'Existing Video'})
        
        try:
            # Try to process the same video again
            process_single_video('https://www.youtube.com/watch?v=existing_id', temp_file)
            
            # Verify it wasn't added twice
            with open(temp_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['video_id'] == 'existing_id'
            
            # get_video_info should not have been called
            mock_get_info.assert_not_called()
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])