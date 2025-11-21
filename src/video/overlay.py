"""
Overlay tracking data visualizations onto video footage.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Optional, List


class TrackingOverlayRenderer:
    """Render tracking data overlays on video frames."""

    def __init__(
        self,
        field_bounds: Tuple[int, int, int, int] = None,
        colors: Dict[str, Tuple[int, int, int]] = None
    ):
        """
        Initialize overlay renderer.

        Args:
            field_bounds: (x_min, y_min, x_max, y_max) pixel coordinates of field in video
            colors: Dictionary mapping team names to BGR colors for OpenCV
        """
        self.field_bounds = field_bounds

        if colors is None:
            # Default colors (BGR format for OpenCV)
            self.colors = {
                'offense': (75, 107, 255),   # Red-ish
                'defense': (196, 205, 78),    # Cyan-ish
                'ball': (61, 217, 255)        # Yellow-ish
            }
        else:
            self.colors = colors

    def set_field_calibration(
        self,
        video_points: np.ndarray,
        field_points: np.ndarray
    ):
        """
        Calibrate field coordinate transformation using homography.

        Args:
            video_points: Array of (x, y) pixel coordinates in video (Nx2)
            field_points: Array of (x, y) yard coordinates on field (Nx2)

        Example:
            # Mark 4 corners of field in video
            video_pts = np.array([
                [100, 50],   # Top-left corner
                [1800, 50],  # Top-right corner
                [100, 1000], # Bottom-left corner
                [1800, 1000] # Bottom-right corner
            ])

            # Corresponding field coordinates (yards)
            field_pts = np.array([
                [10, 0],    # 10 yard line, left sideline
                [110, 0],   # 110 yard line, left sideline
                [10, 53.3], # 10 yard line, right sideline
                [110, 53.3] # 110 yard line, right sideline
            ])

            renderer.set_field_calibration(video_pts, field_pts)
        """
        # Compute homography matrix
        self.homography, _ = cv2.findHomography(field_points, video_points)

        print(f"Field calibration set with {len(video_points)} points")

    def field_to_video_coords(self, x: float, y: float) -> Tuple[int, int]:
        """
        Transform field coordinates to video pixel coordinates.

        Args:
            x: X-coordinate in yards (0-120)
            y: Y-coordinate in yards (0-53.3)

        Returns:
            (pixel_x, pixel_y) in video
        """
        if not hasattr(self, 'homography'):
            raise ValueError("Field calibration not set. Call set_field_calibration() first.")

        # Apply homography transformation
        field_pt = np.array([[[x, y]]], dtype=np.float32)
        video_pt = cv2.perspectiveTransform(field_pt, self.homography)

        pixel_x = int(video_pt[0][0][0])
        pixel_y = int(video_pt[0][0][1])

        return pixel_x, pixel_y

    def draw_player(
        self,
        frame: np.ndarray,
        x: float,
        y: float,
        team: str,
        jersey_number: Optional[int] = None,
        radius: int = 15
    ) -> np.ndarray:
        """
        Draw a player marker on the frame.

        Args:
            frame: Video frame (numpy array)
            x: Player x-coordinate in yards
            y: Player y-coordinate in yards
            team: Team identifier
            jersey_number: Jersey number to display
            radius: Marker radius in pixels

        Returns:
            Frame with player drawn
        """
        pixel_x, pixel_y = self.field_to_video_coords(x, y)

        color = self.colors.get(team, (255, 255, 255))

        # Draw circle
        cv2.circle(frame, (pixel_x, pixel_y), radius, color, -1)
        cv2.circle(frame, (pixel_x, pixel_y), radius, (255, 255, 255), 2)

        # Draw jersey number
        if jersey_number is not None:
            text = str(int(jersey_number))
            font = cv2.FONT_HERSHEY_BOLD
            font_scale = 0.5
            thickness = 2

            # Get text size for centering
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = pixel_x - text_size[0] // 2
            text_y = pixel_y + text_size[1] // 2

            cv2.putText(
                frame, text, (text_x, text_y),
                font, font_scale, (0, 0, 0), thickness + 1
            )  # Black outline
            cv2.putText(
                frame, text, (text_x, text_y),
                font, font_scale, (255, 255, 255), thickness
            )  # White text

        return frame

    def draw_player_trail(
        self,
        frame: np.ndarray,
        positions: List[Tuple[float, float]],
        team: str,
        alpha: float = 0.6
    ) -> np.ndarray:
        """
        Draw a trail showing player's recent movement.

        Args:
            frame: Video frame
            positions: List of (x, y) positions in yards (recent to past)
            team: Team identifier
            alpha: Trail transparency

        Returns:
            Frame with trail drawn
        """
        if len(positions) < 2:
            return frame

        color = self.colors.get(team, (255, 255, 255))

        # Convert positions to pixel coordinates
        pixel_positions = [
            self.field_to_video_coords(x, y) for x, y in positions
        ]

        # Draw line segments with decreasing opacity
        for i in range(len(pixel_positions) - 1):
            start = pixel_positions[i]
            end = pixel_positions[i + 1]

            # Opacity decreases for older positions
            segment_alpha = alpha * ((len(pixel_positions) - i) / len(pixel_positions))

            # Create overlay
            overlay = frame.copy()
            cv2.line(overlay, start, end, color, 3)

            # Blend with original frame
            cv2.addWeighted(overlay, segment_alpha, frame, 1 - segment_alpha, 0, frame)

        return frame

    def draw_separation_line(
        self,
        frame: np.ndarray,
        receiver_pos: Tuple[float, float],
        defender_pos: Tuple[float, float],
        distance: float
    ) -> np.ndarray:
        """
        Draw line showing separation between receiver and defender.

        Args:
            frame: Video frame
            receiver_pos: (x, y) in yards
            defender_pos: (x, y) in yards
            distance: Separation distance in yards

        Returns:
            Frame with separation line drawn
        """
        rec_pixel = self.field_to_video_coords(*receiver_pos)
        def_pixel = self.field_to_video_coords(*defender_pos)

        # Color-code by distance
        if distance < 2:
            color = (0, 0, 255)      # Red: tight coverage
        elif distance < 5:
            color = (0, 255, 255)    # Yellow: moderate separation
        else:
            color = (0, 255, 0)      # Green: open

        # Draw line
        cv2.line(frame, rec_pixel, def_pixel, color, 2)

        # Draw distance text at midpoint
        mid_x = (rec_pixel[0] + def_pixel[0]) // 2
        mid_y = (rec_pixel[1] + def_pixel[1]) // 2

        text = f"{distance:.1f} yds"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2

        # Background rectangle for readability
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        cv2.rectangle(
            frame,
            (mid_x - 5, mid_y - text_size[1] - 5),
            (mid_x + text_size[0] + 5, mid_y + 5),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            frame, text, (mid_x, mid_y),
            font, font_scale, color, thickness
        )

        return frame

    def draw_speed_indicator(
        self,
        frame: np.ndarray,
        x: float,
        y: float,
        speed: float,
        direction: float,
        team: str
    ) -> np.ndarray:
        """
        Draw arrow showing player speed and direction.

        Args:
            frame: Video frame
            x, y: Player position in yards
            speed: Speed in yards/second
            direction: Direction in degrees
            team: Team identifier

        Returns:
            Frame with speed arrow drawn
        """
        pixel_x, pixel_y = self.field_to_video_coords(x, y)

        color = self.colors.get(team, (255, 255, 255))

        # Scale arrow length by speed
        arrow_length = min(int(speed * 5), 50)  # Max 50 pixels

        # Calculate arrow end point
        direction_rad = np.radians(direction)
        end_x = int(pixel_x + arrow_length * np.cos(direction_rad))
        end_y = int(pixel_y + arrow_length * np.sin(direction_rad))

        # Draw arrow
        cv2.arrowedLine(
            frame,
            (pixel_x, pixel_y),
            (end_x, end_y),
            color,
            2,
            tipLength=0.3
        )

        # Draw speed text
        speed_mph = speed * 2.04545  # Convert yards/sec to mph
        text = f"{speed_mph:.1f} mph"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1

        text_x = pixel_x + 5
        text_y = pixel_y - 10

        cv2.putText(
            frame, text, (text_x, text_y),
            font, font_scale, (0, 0, 0), thickness + 1
        )  # Outline
        cv2.putText(
            frame, text, (text_x, text_y),
            font, font_scale, color, thickness
        )

        return frame

    def draw_info_overlay(
        self,
        frame: np.ndarray,
        info: Dict[str, str],
        position: str = 'top-left'
    ) -> np.ndarray:
        """
        Draw information overlay on frame.

        Args:
            frame: Video frame
            info: Dictionary of key-value pairs to display
            position: 'top-left', 'top-right', 'bottom-left', 'bottom-right'

        Returns:
            Frame with info overlay
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        line_height = 30

        # Determine starting position
        if position == 'top-left':
            x, y = 20, 40
        elif position == 'top-right':
            x, y = frame.shape[1] - 300, 40
        elif position == 'bottom-left':
            x, y = 20, frame.shape[0] - (len(info) * line_height) - 20
        else:  # bottom-right
            x, y = frame.shape[1] - 300, frame.shape[0] - (len(info) * line_height) - 20

        # Draw semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (x - 10, y - 30),
            (x + 280, y + (len(info) * line_height) - 10),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Draw text
        current_y = y
        for key, value in info.items():
            text = f"{key}: {value}"
            cv2.putText(
                frame, text, (x, current_y),
                font, font_scale, (255, 255, 255), thickness
            )
            current_y += line_height

        return frame


if __name__ == "__main__":
    print("TrackingOverlayRenderer module")
    print("\nExample usage:")
    print("""
    from src.video.overlay import TrackingOverlayRenderer

    # Initialize renderer
    renderer = TrackingOverlayRenderer()

    # Calibrate field (identify 4 corners in video)
    video_pts = np.array([[100, 50], [1800, 50], [100, 1000], [1800, 1000]])
    field_pts = np.array([[10, 0], [110, 0], [10, 53.3], [110, 53.3]])
    renderer.set_field_calibration(video_pts, field_pts)

    # Load video frame
    frame = cv2.imread('frame.jpg')

    # Draw player
    frame = renderer.draw_player(frame, x=50, y=26.65, team='offense', jersey_number=15)

    # Draw separation line
    frame = renderer.draw_separation_line(
        frame,
        receiver_pos=(55, 30),
        defender_pos=(52, 28),
        distance=3.2
    )

    # Save
    cv2.imwrite('overlaid_frame.jpg', frame)
    """)
