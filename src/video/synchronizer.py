"""
Synchronize NFL tracking data with video footage.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Optional
from scipy.interpolate import interp1d


class VideoTrackingSynchronizer:
    """Synchronize tracking data frames with video frames."""

    def __init__(self, video_path: Path, tracking_data: pd.DataFrame):
        """
        Initialize synchronizer.

        Args:
            video_path: Path to video file
            tracking_data: DataFrame with tracking data (already filtered to ball-in-air)
        """
        self.video_path = video_path
        self.tracking_data = tracking_data.sort_values('frameId')

        # Load video
        self.video = cv2.VideoCapture(str(video_path))
        self.video_fps = self.video.get(cv2.CAP_PROP_FPS)
        self.video_frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Tracking data info
        self.tracking_fps = 10  # NFL tracking is 10 Hz
        self.tracking_frames = sorted(self.tracking_data['frameId'].unique())

        print(f"Video: {self.video_fps} fps, {self.video_frame_count} frames")
        print(f"Tracking: {self.tracking_fps} fps, {len(self.tracking_frames)} frames")

    def set_sync_points(self, sync_map: Dict[int, int]):
        """
        Set synchronization points between video and tracking.

        Args:
            sync_map: Dictionary mapping tracking frame IDs to video frame numbers
                     e.g., {pass_forward_frame: 45, outcome_frame: 78}
        """
        self.sync_map = sync_map

        # Calculate time offset
        tracking_frame_ids = list(sync_map.keys())
        video_frame_nums = list(sync_map.values())

        if len(sync_map) >= 2:
            # Linear interpolation between sync points
            self.sync_interpolator = interp1d(
                tracking_frame_ids,
                video_frame_nums,
                kind='linear',
                fill_value='extrapolate'
            )
        else:
            # Simple offset
            tracking_frame = tracking_frame_ids[0]
            video_frame = video_frame_nums[0]
            self.frame_offset = video_frame - tracking_frame

        print(f"Sync points set: {sync_map}")

    def get_video_frame_for_tracking(self, tracking_frame_id: int) -> int:
        """
        Get corresponding video frame number for a tracking frame.

        Args:
            tracking_frame_id: Tracking data frame ID

        Returns:
            Video frame number (0-indexed)
        """
        if hasattr(self, 'sync_interpolator'):
            video_frame = int(self.sync_interpolator(tracking_frame_id))
        elif hasattr(self, 'frame_offset'):
            video_frame = tracking_frame_id + self.frame_offset
        else:
            raise ValueError("Sync points not set. Call set_sync_points() first.")

        return max(0, min(video_frame, self.video_frame_count - 1))

    def interpolate_tracking_data(self, target_fps: int = 30) -> pd.DataFrame:
        """
        Interpolate tracking data to match video frame rate.

        Args:
            target_fps: Target frames per second (typically video fps)

        Returns:
            DataFrame with interpolated tracking data
        """
        # Calculate number of interpolated frames needed
        tracking_duration = len(self.tracking_frames) / self.tracking_fps
        num_interpolated_frames = int(tracking_duration * target_fps)

        # Create new frame timeline
        original_frames = self.tracking_frames
        new_frames = np.linspace(
            original_frames[0],
            original_frames[-1],
            num_interpolated_frames
        )

        interpolated_data = []

        # Interpolate each player's movement
        for nfl_id in self.tracking_data['nflId'].unique():
            if pd.isna(nfl_id):
                # Handle ball (nflId is NaN)
                player_data = self.tracking_data[
                    self.tracking_data['nflId'].isna()
                ].copy()
            else:
                player_data = self.tracking_data[
                    self.tracking_data['nflId'] == nfl_id
                ].copy()

            if len(player_data) < 2:
                continue

            player_data = player_data.sort_values('frameId')

            # Interpolate x, y, s (speed), dir (direction)
            for column in ['x', 'y', 's', 'dir', 'o']:
                if column in player_data.columns:
                    # Create interpolator
                    f = interp1d(
                        player_data['frameId'],
                        player_data[column],
                        kind='linear',
                        fill_value='extrapolate'
                    )

                    # Interpolate values
                    interpolated_values = f(new_frames)

                    # Store in player data
                    for i, (frame, value) in enumerate(zip(new_frames, interpolated_values)):
                        if i >= len(interpolated_data):
                            interpolated_data.append({
                                'frameId': frame,
                                'interpolated_frame_idx': i,
                                'nflId': nfl_id,
                                'club': player_data.iloc[0]['club'],
                                'jerseyNumber': player_data.iloc[0].get('jerseyNumber'),
                                column: value
                            })
                        else:
                            if interpolated_data[i]['nflId'] == nfl_id:
                                interpolated_data[i][column] = value

        interpolated_df = pd.DataFrame(interpolated_data)

        print(f"Interpolated {len(self.tracking_frames)} frames to {len(new_frames)} frames")

        return interpolated_df

    def get_synced_frame(self, tracking_frame_id: int) -> Optional[np.ndarray]:
        """
        Get video frame corresponding to tracking frame.

        Args:
            tracking_frame_id: Tracking data frame ID

        Returns:
            Video frame as numpy array (BGR format) or None if failed
        """
        video_frame_num = self.get_video_frame_for_tracking(tracking_frame_id)

        # Seek to frame
        self.video.set(cv2.CAP_PROP_POS_FRAMES, video_frame_num)

        # Read frame
        success, frame = self.video.read()

        if success:
            return frame
        else:
            print(f"Failed to read video frame {video_frame_num}")
            return None

    def find_sync_points_interactive(self) -> Dict[int, int]:
        """
        Interactive tool to identify sync points.

        Returns:
            Dictionary mapping tracking frame IDs to video frame numbers
        """
        print("\n=== Interactive Sync Point Finder ===")
        print("Instructions:")
        print("1. Play will show tracking data events")
        print("2. Identify corresponding video frame for each event")
        print("3. Use video player to find exact frame number")
        print()

        # Get key events from tracking data
        events = self.tracking_data[self.tracking_data['event'].notna()].copy()
        events = events.drop_duplicates(subset=['event'])

        print("Key events in tracking data:")
        for idx, row in events.iterrows():
            print(f"  Frame {row['frameId']}: {row['event']}")

        print()
        print("Now use a video player to identify these events in your video.")
        print("Suggested: VLC Media Player (shows frame numbers)")
        print()

        sync_map = {}

        for idx, row in events.iterrows():
            tracking_frame = row['frameId']
            event_name = row['event']

            print(f"\nEvent: {event_name} (tracking frame {tracking_frame})")
            video_frame = input(f"Enter corresponding video frame number (or 'skip'): ")

            if video_frame.lower() != 'skip':
                try:
                    sync_map[tracking_frame] = int(video_frame)
                    print(f"  Mapped: tracking frame {tracking_frame} → video frame {video_frame}")
                except ValueError:
                    print(f"  Invalid input, skipping...")

        if len(sync_map) >= 1:
            print(f"\nSync points captured: {sync_map}")
            return sync_map
        else:
            print("\nNo sync points captured!")
            return {}

    def __del__(self):
        """Release video capture."""
        if hasattr(self, 'video'):
            self.video.release()


if __name__ == "__main__":
    print("VideoTrackingSynchronizer module")
    print("\nExample usage:")
    print("""
    from src.video.synchronizer import VideoTrackingSynchronizer

    # Initialize
    sync = VideoTrackingSynchronizer('video.mp4', ball_in_air_tracking)

    # Set sync points (manually identified)
    sync.set_sync_points({
        35: 45,   # tracking frame 35 = video frame 45 (pass_forward)
        58: 78    # tracking frame 58 = video frame 78 (pass_arrived)
    })

    # Interpolate tracking to match video fps
    smooth_tracking = sync.interpolate_tracking_data(target_fps=30)

    # Get synced video frame
    frame = sync.get_synced_frame(tracking_frame_id=40)
    """)
