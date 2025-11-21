"""
NFL field visualization utilities.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Arc
import numpy as np
from typing import Optional, Tuple


class NFLField:
    """Create and manage NFL field visualizations."""

    # Field dimensions (yards)
    FIELD_LENGTH = 120  # Including end zones
    FIELD_WIDTH = 53.3
    END_ZONE_LENGTH = 10

    # Colors
    FIELD_COLOR = '#2d5016'  # Dark green
    LINE_COLOR = 'white'
    END_ZONE_COLOR = '#1a3a0f'  # Darker green

    def __init__(self, figsize: Tuple[float, float] = (12, 6.4)):
        """
        Initialize NFL field.

        Args:
            figsize: Figure size (width, height) in inches
        """
        self.figsize = figsize
        self.fig = None
        self.ax = None

    def create_field(
        self,
        line_of_scrimmage: Optional[float] = None,
        first_down_line: Optional[float] = None,
        show_yard_labels: bool = True
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Create a standard NFL field.

        Args:
            line_of_scrimmage: X-coordinate of line of scrimmage
            first_down_line: X-coordinate of first down line
            show_yard_labels: Whether to show yard line labels

        Returns:
            Tuple of (figure, axes)
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize, dpi=100)

        # Set field limits
        self.ax.set_xlim(0, self.FIELD_LENGTH)
        self.ax.set_ylim(0, self.FIELD_WIDTH)

        # Field background
        self.ax.add_patch(Rectangle(
            (0, 0),
            self.FIELD_LENGTH,
            self.FIELD_WIDTH,
            facecolor=self.FIELD_COLOR,
            zorder=0
        ))

        # End zones
        self.ax.add_patch(Rectangle(
            (0, 0),
            self.END_ZONE_LENGTH,
            self.FIELD_WIDTH,
            facecolor=self.END_ZONE_COLOR,
            alpha=0.3,
            zorder=0
        ))

        self.ax.add_patch(Rectangle(
            (110, 0),
            self.END_ZONE_LENGTH,
            self.FIELD_WIDTH,
            facecolor=self.END_ZONE_COLOR,
            alpha=0.3,
            zorder=0
        ))

        # Draw yard lines
        for yard in range(10, 110, 5):
            # Major yard lines (every 5 yards)
            linewidth = 1.5 if yard % 10 == 0 else 0.8
            self.ax.plot(
                [yard, yard],
                [0, self.FIELD_WIDTH],
                color=self.LINE_COLOR,
                linewidth=linewidth,
                alpha=0.7,
                zorder=1
            )

            # Yard numbers
            if show_yard_labels and yard % 10 == 0:
                yard_num = yard - 10 if yard <= 60 else 120 - yard
                if 10 < yard < 110:
                    # Left side
                    self.ax.text(
                        yard, 5,
                        str(yard_num),
                        color=self.LINE_COLOR,
                        fontsize=14,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        rotation=0,
                        zorder=1
                    )
                    # Right side
                    self.ax.text(
                        yard, self.FIELD_WIDTH - 5,
                        str(yard_num),
                        color=self.LINE_COLOR,
                        fontsize=14,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        rotation=180,
                        zorder=1
                    )

        # Draw hash marks
        for yard in range(10, 110):
            # Left hash
            self.ax.plot(
                [yard, yard],
                [18.5, 19.5],
                color=self.LINE_COLOR,
                linewidth=0.5,
                alpha=0.5,
                zorder=1
            )
            # Right hash
            self.ax.plot(
                [yard, yard],
                [self.FIELD_WIDTH - 19.5, self.FIELD_WIDTH - 18.5],
                color=self.LINE_COLOR,
                linewidth=0.5,
                alpha=0.5,
                zorder=1
            )

        # Line of scrimmage
        if line_of_scrimmage is not None:
            self.ax.axvline(
                line_of_scrimmage,
                color='blue',
                linewidth=2,
                linestyle='--',
                alpha=0.7,
                zorder=2,
                label='Line of Scrimmage'
            )

        # First down line
        if first_down_line is not None:
            self.ax.axvline(
                first_down_line,
                color='yellow',
                linewidth=2,
                linestyle='--',
                alpha=0.7,
                zorder=2,
                label='First Down'
            )

        # Remove axes
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        return self.fig, self.ax

    def plot_players(
        self,
        x: np.ndarray,
        y: np.ndarray,
        team: np.ndarray,
        numbers: Optional[np.ndarray] = None,
        colors: Optional[dict] = None,
        size: float = 100,
        alpha: float = 0.8
    ):
        """
        Plot player positions on the field.

        Args:
            x: X-coordinates of players
            y: Y-coordinates of players
            team: Team identifiers
            numbers: Jersey numbers (optional)
            colors: Dictionary mapping team to color
            size: Marker size
            alpha: Transparency
        """
        if colors is None:
            colors = {
                'offense': '#FF6B6B',  # Red
                'defense': '#4ECDC4',  # Cyan
                'football': '#FFD93D'   # Yellow
            }

        unique_teams = np.unique(team)

        for t in unique_teams:
            mask = team == t
            color = colors.get(t, 'gray')

            self.ax.scatter(
                x[mask],
                y[mask],
                c=color,
                s=size,
                alpha=alpha,
                edgecolors='white',
                linewidths=1.5,
                zorder=10,
                label=t
            )

            # Add jersey numbers
            if numbers is not None:
                for xi, yi, num in zip(x[mask], y[mask], numbers[mask]):
                    if not pd.isna(num):
                        self.ax.text(
                            xi, yi,
                            str(int(num)),
                            color='white',
                            fontsize=8,
                            fontweight='bold',
                            ha='center',
                            va='center',
                            zorder=11
                        )

    def plot_ball_trajectory(
        self,
        x: np.ndarray,
        y: np.ndarray,
        color: str = '#FFD93D',
        linewidth: float = 2,
        alpha: float = 0.7,
        show_direction: bool = True
    ):
        """
        Plot the ball's trajectory.

        Args:
            x: X-coordinates of ball
            y: Y-coordinates of ball
            color: Line color
            linewidth: Line width
            alpha: Transparency
            show_direction: Whether to show direction arrows
        """
        # Plot trajectory line
        self.ax.plot(
            x, y,
            color=color,
            linewidth=linewidth,
            alpha=alpha,
            zorder=9,
            label='Ball Trajectory'
        )

        # Plot release and arrival points
        self.ax.scatter(
            x[0], y[0],
            color=color,
            s=150,
            marker='o',
            edgecolors='white',
            linewidths=2,
            zorder=10,
            label='Release'
        )

        self.ax.scatter(
            x[-1], y[-1],
            color=color,
            s=150,
            marker='*',
            edgecolors='white',
            linewidths=2,
            zorder=10,
            label='Target'
        )

        # Add direction arrows
        if show_direction and len(x) > 5:
            # Arrow at midpoint
            mid_idx = len(x) // 2
            dx = x[mid_idx + 1] - x[mid_idx]
            dy = y[mid_idx + 1] - y[mid_idx]

            self.ax.arrow(
                x[mid_idx], y[mid_idx],
                dx * 2, dy * 2,
                head_width=2,
                head_length=1.5,
                fc=color,
                ec=color,
                alpha=alpha,
                zorder=9
            )

    def add_title(
        self,
        title: str,
        subtitle: Optional[str] = None,
        fontsize: int = 16
    ):
        """
        Add title to the field visualization.

        Args:
            title: Main title
            subtitle: Subtitle (optional)
            fontsize: Font size for title
        """
        title_text = title
        if subtitle:
            title_text += f"\n{subtitle}"

        self.ax.set_title(
            title_text,
            fontsize=fontsize,
            fontweight='bold',
            color='white',
            pad=20
        )

    def add_legend(self, loc: str = 'upper right'):
        """Add legend to the field."""
        self.ax.legend(
            loc=loc,
            framealpha=0.8,
            fontsize=10
        )

    def save(self, filepath: str, dpi: int = 300, bbox_inches: str = 'tight'):
        """
        Save the field visualization.

        Args:
            filepath: Output file path
            dpi: Resolution
            bbox_inches: Bounding box setting
        """
        self.fig.savefig(
            filepath,
            dpi=dpi,
            bbox_inches=bbox_inches,
            facecolor=self.FIELD_COLOR
        )


if __name__ == "__main__":
    # Example usage
    import pandas as pd

    field = NFLField()
    field.create_field(line_of_scrimmage=30, first_down_line=40)

    # Sample player positions
    offense_x = np.array([30, 35, 40, 42, 45])
    offense_y = np.array([26.65, 20, 10, 30, 35])

    defense_x = np.array([32, 38, 43, 45, 48])
    defense_y = np.array([26.65, 15, 12, 32, 38])

    field.plot_players(
        np.concatenate([offense_x, defense_x]),
        np.concatenate([offense_y, defense_y]),
        np.array(['offense'] * 5 + ['defense'] * 5)
    )

    field.add_title("Example NFL Play Visualization")
    field.add_legend()

    plt.show()
