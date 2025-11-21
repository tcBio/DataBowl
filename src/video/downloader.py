"""
YouTube video downloader for NFL play footage.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Dict
import json


class YouTubeDownloader:
    """Download and manage YouTube video clips of NFL plays."""

    def __init__(self, output_dir: str = "data/videos"):
        """
        Initialize downloader.

        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_video(
        self,
        url: str,
        output_name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        quality: str = "1080"
    ) -> Path:
        """
        Download video from YouTube.

        Args:
            url: YouTube video URL
            output_name: Output filename (without extension)
            start_time: Start time (format: HH:MM:SS or MM:SS)
            end_time: End time (format: HH:MM:SS or MM:SS)
            quality: Video quality (1080, 720, 480)

        Returns:
            Path to downloaded video file

        Requires:
            yt-dlp installed: pip install yt-dlp
        """
        if output_name is None:
            output_name = "play_video"

        output_path = self.output_dir / f"{output_name}.mp4"

        # Build yt-dlp command
        cmd = [
            "yt-dlp",
            "-f", f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
            "--merge-output-format", "mp4",
            "-o", str(output_path),
        ]

        # Add time trimming if specified
        if start_time and end_time:
            cmd.extend([
                "--download-sections",
                f"*{start_time}-{end_time}"
            ])

        cmd.append(url)

        # Execute download
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Video downloaded successfully: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            print(f"Download failed: {e.stderr}")
            raise

        except FileNotFoundError:
            raise RuntimeError(
                "yt-dlp not found. Install with: pip install yt-dlp"
            )

    def get_video_info(self, url: str) -> Dict:
        """
        Get metadata about a YouTube video.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with video metadata
        """
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            url
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            metadata = json.loads(result.stdout)

            return {
                'title': metadata.get('title'),
                'duration': metadata.get('duration'),
                'width': metadata.get('width'),
                'height': metadata.get('height'),
                'fps': metadata.get('fps'),
                'upload_date': metadata.get('upload_date'),
                'channel': metadata.get('channel')
            }

        except subprocess.CalledProcessError as e:
            print(f"Failed to get video info: {e.stderr}")
            raise

    def search_play_footage(
        self,
        qb_name: str,
        receiver_name: str,
        team: str,
        opponent: str,
        season: str
    ) -> str:
        """
        Generate search query to find play footage on YouTube.

        Args:
            qb_name: Quarterback name
            receiver_name: Receiver name
            team: Offensive team abbreviation
            opponent: Defensive team abbreviation
            season: Season year

        Returns:
            Formatted search query string

        Example:
            >>> downloader.search_play_footage(
            ...     "Mahomes", "Kelce", "KC", "BUF", "2023"
            ... )
            'Mahomes to Kelce Chiefs vs Bills 2023 highlights'
        """
        query = f"{qb_name} to {receiver_name} {team} vs {opponent} {season}"

        print(f"Suggested YouTube search: {query}")
        print(f"URL: https://www.youtube.com/results?search_query={query.replace(' ', '+')}")

        return query

    def trim_video(
        self,
        input_path: Path,
        output_path: Path,
        start_time: float,
        duration: float
    ):
        """
        Trim video to specific time range using ffmpeg.

        Args:
            input_path: Path to input video
            output_path: Path for output video
            start_time: Start time in seconds
            duration: Duration in seconds

        Requires:
            ffmpeg installed
        """
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-y",  # Overwrite output file
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Video trimmed successfully: {output_path}")

        except subprocess.CalledProcessError as e:
            print(f"Trimming failed: {e.stderr}")
            raise

        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg not found. Install with: sudo apt-get install ffmpeg"
            )


class PlayVideoMatcher:
    """Match tracking data plays to YouTube footage."""

    def __init__(self, loader):
        """
        Initialize matcher.

        Args:
            loader: NFLDataLoader instance
        """
        self.loader = loader

    def generate_search_query(self, game_id: int, play_id: int) -> str:
        """
        Generate YouTube search query for a specific play.

        Args:
            game_id: Game identifier
            play_id: Play identifier

        Returns:
            Search query string
        """
        metadata = self.loader.get_play_metadata(game_id, play_id)

        # Extract player names from play description
        description = metadata['play_description']

        # Build search query
        query_parts = [
            metadata['possession_team'],
            "vs",
            metadata['defensive_team'],
            f"week {metadata['week']}"
        ]

        # Add play type info
        if metadata['pass_result'] == 'C':
            query_parts.append("touchdown" if "TOUCHDOWN" in description else "completion")
        elif metadata['pass_result'] == 'IN':
            query_parts.append("interception")

        query = " ".join(query_parts)

        return query

    def get_downloadable_plays(
        self,
        plays_df,
        min_air_yards: float = 20
    ):
        """
        Filter plays that are likely to have YouTube footage.

        Args:
            plays_df: DataFrame of plays
            min_air_yards: Minimum air yards (big plays more likely on YouTube)

        Returns:
            Filtered DataFrame with plays likely to have footage
        """
        # Big plays in prime time games most likely to have footage
        candidates = plays_df[
            (plays_df['passLength'] >= min_air_yards) &
            (plays_df['passResult'].isin(['C', 'IN']))  # Completions or picks
        ].copy()

        # Prioritize touchdowns
        candidates['is_td'] = candidates['playDescription'].str.contains(
            'TOUCHDOWN',
            case=False,
            na=False
        )

        candidates = candidates.sort_values(
            by=['is_td', 'passLength'],
            ascending=[False, False]
        )

        return candidates


if __name__ == "__main__":
    # Example usage
    downloader = YouTubeDownloader()

    # Search for a play
    query = downloader.search_play_footage(
        qb_name="Patrick Mahomes",
        receiver_name="Travis Kelce",
        team="Chiefs",
        opponent="Bills",
        season="2023"
    )

    print(f"\nSearch YouTube for: {query}")
    print("\nOnce you find the video:")
    print("1. Copy the URL")
    print("2. Identify the timestamp of the play")
    print("3. Use downloader.download_video() to download the clip")
