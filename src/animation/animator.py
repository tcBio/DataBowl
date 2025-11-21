"""
Animation utilities for NFL tracking data.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
import numpy as np
import pandas as pd
from typing import Optional, Callable, List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from visualization.field import NFLField


class PlayAnimator:
    """Animate NFL plays with player tracking data."""

    def __init__(
        self,
        tracking_data: pd.DataFrame,
        figsize: tuple = (14, 7),
        fps: int = 10
    ):
        """
        Initialize play animator.

        Args:
            tracking_data: DataFrame with tracking data for a single play
            figsize: Figure size
            fps: Frames per second for animation
        """
        self.tracking = tracking_data.sort_values('frameId')
        self.figsize = figsize
        self.fps = fps

        # Extract unique frames
        self.frames = sorted(self.tracking['frameId'].unique())
        self.n_frames = len(self.frames)

        # Separate ball from players
        self.ball_tracking = self.tracking[self.tracking['club'] == 'football'].copy()
        self.player_tracking = self.tracking[self.tracking['club'] != 'football'].copy()

    def create_animation(
        self,
        title: str = "NFL Play Animation",
        show_trails: bool = True,
        trail_length: int = 10,
        show_speed_vectors: bool = True,
        show_ball_trajectory: bool = True,
        color_map: Optional[dict] = None
    ) -> animation.FuncAnimation:
        """
        Create animation of the play.

        Args:
            title: Animation title
            show_trails: Whether to show player movement trails
            trail_length: Number of frames to show in trail
            show_speed_vectors: Whether to show speed/direction vectors
            show_ball_trajectory: Whether to show ball trajectory
            color_map: Dictionary mapping team abbreviations to colors

        Returns:
            FuncAnimation object
        """
        # Setup field
        field = NFLField(figsize=self.figsize)
        fig, ax = field.create_field()

        # Initialize plot elements
        self.player_scatter = None
        self.ball_scatter = None
        self.trail_lines = []
        self.speed_arrows = []
        self.ball_trajectory_line = None
        self.frame_text = None

        # Color mapping
        if color_map is None:
            # Get unique teams
            teams = self.player_tracking['club'].unique()
            color_map = {
                teams[0]: '#FF6B6B',  # Red for team 1
                teams[1]: '#4ECDC4' if len(teams) > 1 else '#FF6B6B',  # Cyan for team 2
                'football': '#FFD93D'  # Yellow for ball
            }

        self.color_map = color_map
        self.field = field
        self.show_trails = show_trails
        self.trail_length = trail_length
        self.show_speed_vectors = show_speed_vectors
        self.show_ball_trajectory = show_ball_trajectory

        # Add title
        field.add_title(title)

        # Frame counter
        self.frame_text = ax.text(
            5, field.FIELD_WIDTH - 5,
            '',
            fontsize=12,
            color='white',
            fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.7)
        )

        # Create animation
        anim = FuncAnimation(
            fig,
            self._update_frame,
            frames=self.n_frames,
            interval=1000 / self.fps,
            blit=False,
            repeat=True
        )

        return anim

    def _update_frame(self, frame_idx: int):
        """
        Update function for each frame of animation.

        Args:
            frame_idx: Index of current frame
        """
        current_frame_id = self.frames[frame_idx]

        # Get data for current frame
        frame_data = self.player_tracking[
            self.player_tracking['frameId'] == current_frame_id
        ]

        ball_data = self.ball_tracking[
            self.ball_tracking['frameId'] == current_frame_id
        ]

        # Clear previous scatter plots
        if self.player_scatter is not None:
            self.player_scatter.remove()
        if self.ball_scatter is not None:
            self.ball_scatter.remove()

        # Plot players
        if len(frame_data) > 0:
            colors = [self.color_map.get(team, 'gray') for team in frame_data['club']]

            self.player_scatter = self.field.ax.scatter(
                frame_data['x'],
                frame_data['y'],
                c=colors,
                s=200,
                alpha=0.9,
                edgecolors='white',
                linewidths=2,
                zorder=10
            )

            # Add jersey numbers
            for _, player in frame_data.iterrows():
                if pd.notna(player['jerseyNumber']):
                    self.field.ax.text(
                        player['x'],
                        player['y'],
                        str(int(player['jerseyNumber'])),
                        color='white',
                        fontsize=7,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        zorder=11
                    )

        # Plot ball
        if len(ball_data) > 0:
            self.ball_scatter = self.field.ax.scatter(
                ball_data['x'],
                ball_data['y'],
                c=self.color_map['football'],
                s=150,
                marker='o',
                alpha=1.0,
                edgecolors='white',
                linewidths=2,
                zorder=12
            )

        # Show ball trajectory up to current frame
        if self.show_ball_trajectory:
            ball_history = self.ball_tracking[
                self.ball_tracking['frameId'] <= current_frame_id
            ]

            if len(ball_history) > 1:
                if self.ball_trajectory_line is not None:
                    self.ball_trajectory_line.remove()

                self.ball_trajectory_line, = self.field.ax.plot(
                    ball_history['x'],
                    ball_history['y'],
                    color=self.color_map['football'],
                    linewidth=2,
                    linestyle='--',
                    alpha=0.5,
                    zorder=9
                )

        # Show trails
        if self.show_trails:
            # Remove old trails
            for line in self.trail_lines:
                line.remove()
            self.trail_lines = []

            # Get historical frames for trails
            trail_start_frame = max(0, frame_idx - self.trail_length)
            trail_frame_ids = self.frames[trail_start_frame:frame_idx + 1]

            # Plot trail for each player
            for nfl_id in frame_data['nflId'].unique():
                if pd.notna(nfl_id):
                    player_trail = self.player_tracking[
                        (self.player_tracking['nflId'] == nfl_id) &
                        (self.player_tracking['frameId'].isin(trail_frame_ids))
                    ].sort_values('frameId')

                    if len(player_trail) > 1:
                        team = player_trail.iloc[-1]['club']
                        color = self.color_map.get(team, 'gray')

                        line, = self.field.ax.plot(
                            player_trail['x'],
                            player_trail['y'],
                            color=color,
                            linewidth=1.5,
                            alpha=0.3,
                            zorder=5
                        )
                        self.trail_lines.append(line)

        # Show speed vectors
        if self.show_speed_vectors:
            # Remove old arrows
            for arrow in self.speed_arrows:
                arrow.remove()
            self.speed_arrows = []

            for _, player in frame_data.iterrows():
                if pd.notna(player['s']) and player['s'] > 0:
                    # Calculate vector components
                    # dir is direction in degrees
                    dir_rad = np.radians(player['dir'])
                    dx = player['s'] * np.cos(dir_rad) * 0.5  # Scale for visibility
                    dy = player['s'] * np.sin(dir_rad) * 0.5

                    team = player['club']
                    color = self.color_map.get(team, 'gray')

                    arrow = self.field.ax.arrow(
                        player['x'],
                        player['y'],
                        dx, dy,
                        head_width=1,
                        head_length=0.8,
                        fc=color,
                        ec=color,
                        alpha=0.6,
                        linewidth=1.5,
                        zorder=9
                    )
                    self.speed_arrows.append(arrow)

        # Update frame counter
        time_elapsed = frame_idx / self.fps
        self.frame_text.set_text(
            f'Frame: {current_frame_id} | Time: {time_elapsed:.1f}s'
        )

        # Get event for this frame
        event = frame_data['event'].iloc[0] if len(frame_data) > 0 else None
        if pd.notna(event) and event:
            self.frame_text.set_text(
                f'Frame: {current_frame_id} | Time: {time_elapsed:.1f}s | {event}'
            )

    def save_animation(
        self,
        filepath: str,
        format: str = 'mp4',
        dpi: int = 100,
        bitrate: int = 1800,
        **kwargs
    ):
        """
        Save animation to file.

        Args:
            filepath: Output file path
            format: Output format ('mp4', 'gif')
            dpi: Resolution
            bitrate: Video bitrate (for mp4)
            **kwargs: Additional arguments passed to animation creator
        """
        anim = self.create_animation(**kwargs)

        if format == 'mp4':
            writer = FFMpegWriter(fps=self.fps, bitrate=bitrate)
            anim.save(filepath, writer=writer, dpi=dpi)
        elif format == 'gif':
            writer = PillowWriter(fps=self.fps)
            anim.save(filepath, writer=writer, dpi=dpi)
        else:
            raise ValueError(f"Unsupported format: {format}")

        print(f"Animation saved to: {filepath}")


def create_comparison_animation(
    tracking_data_list: List[pd.DataFrame],
    titles: List[str],
    nrows: int = 1,
    ncols: int = 2,
    figsize: tuple = (20, 8),
    fps: int = 10
) -> animation.FuncAnimation:
    """
    Create side-by-side comparison animation of multiple plays.

    Args:
        tracking_data_list: List of tracking DataFrames
        titles: List of titles for each play
        nrows: Number of rows in subplot grid
        ncols: Number of columns in subplot grid
        figsize: Figure size
        fps: Frames per second

    Returns:
        FuncAnimation object
    """
    # TODO: Implement multi-play comparison animation
    raise NotImplementedError("Comparison animation not yet implemented")


if __name__ == "__main__":
    # Example usage would require actual tracking data
    print("PlayAnimator class ready for use")
    print("Example: animator = PlayAnimator(tracking_df)")
    print("         anim = animator.create_animation(title='My Play')")
    print("         animator.save_animation('output.mp4', format='mp4')")
