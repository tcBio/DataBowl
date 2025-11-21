"""
Data loading utilities for NFL Big Data Bowl 2026.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple


class NFLDataLoader:
    """Load and manage NFL tracking data."""

    def __init__(self, data_dir: str = "data/raw"):
        """
        Initialize data loader.

        Args:
            data_dir: Path to directory containing raw CSV files
        """
        self.data_dir = Path(data_dir)
        self._games = None
        self._plays = None
        self._players = None
        self._player_play = None

    @property
    def games(self) -> pd.DataFrame:
        """Load games data (cached)."""
        if self._games is None:
            self._games = pd.read_csv(self.data_dir / "games.csv")
        return self._games

    @property
    def plays(self) -> pd.DataFrame:
        """Load plays data (cached)."""
        if self._plays is None:
            self._plays = pd.read_csv(self.data_dir / "plays.csv")
        return self._plays

    @property
    def players(self) -> pd.DataFrame:
        """Load players data (cached)."""
        if self._players is None:
            self._players = pd.read_csv(self.data_dir / "players.csv")
        return self._players

    @property
    def player_play(self) -> pd.DataFrame:
        """Load player_play data (cached)."""
        if self._player_play is None:
            self._player_play = pd.read_csv(self.data_dir / "player_play.csv")
        return self._player_play

    def load_tracking_week(self, week: int) -> pd.DataFrame:
        """
        Load tracking data for a specific week.

        Args:
            week: Week number (1-9)

        Returns:
            DataFrame with tracking data for the week
        """
        file_path = self.data_dir / f"tracking_week_{week}.csv"
        return pd.read_csv(file_path)

    def load_tracking_weeks(self, weeks: List[int]) -> pd.DataFrame:
        """
        Load and combine tracking data for multiple weeks.

        Args:
            weeks: List of week numbers to load

        Returns:
            Combined DataFrame with tracking data
        """
        dfs = []
        for week in weeks:
            df = self.load_tracking_week(week)
            dfs.append(df)
        return pd.concat(dfs, ignore_index=True)

    def get_play_tracking(
        self,
        game_id: int,
        play_id: int,
        week: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get tracking data for a specific play.

        Args:
            game_id: Game identifier
            play_id: Play identifier
            week: Week number (if known, for faster loading)

        Returns:
            DataFrame with tracking data for the play
        """
        if week is not None:
            tracking = self.load_tracking_week(week)
        else:
            # Find which week this game is in
            game_week = self.games[self.games['gameId'] == game_id]['week'].iloc[0]
            tracking = self.load_tracking_week(game_week)

        play_tracking = tracking[
            (tracking['gameId'] == game_id) &
            (tracking['playId'] == play_id)
        ].copy()

        return play_tracking

    def get_pass_plays(
        self,
        min_air_yards: Optional[float] = None,
        max_air_yards: Optional[float] = None,
        pass_result: Optional[List[str]] = None,
        coverage_type: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Filter pass plays based on criteria.

        Args:
            min_air_yards: Minimum air yards
            max_air_yards: Maximum air yards
            pass_result: List of pass results to include (e.g., ['C', 'I', 'IN'])
            coverage_type: List of coverage types to include

        Returns:
            Filtered DataFrame of plays
        """
        plays = self.plays[self.plays['isDropback'] == True].copy()

        if min_air_yards is not None:
            plays = plays[plays['passLength'] >= min_air_yards]

        if max_air_yards is not None:
            plays = plays[plays['passLength'] <= max_air_yards]

        if pass_result is not None:
            plays = plays[plays['passResult'].isin(pass_result)]

        if coverage_type is not None:
            plays = plays[plays['pff_passCoverage'].isin(coverage_type)]

        return plays

    def get_play_metadata(self, game_id: int, play_id: int) -> dict:
        """
        Get metadata for a specific play.

        Args:
            game_id: Game identifier
            play_id: Play identifier

        Returns:
            Dictionary with play metadata
        """
        play = self.plays[
            (self.plays['gameId'] == game_id) &
            (self.plays['playId'] == play_id)
        ].iloc[0]

        game = self.games[self.games['gameId'] == game_id].iloc[0]

        return {
            'game_id': game_id,
            'play_id': play_id,
            'week': game['week'],
            'home_team': game['homeTeamAbbr'],
            'away_team': game['visitorTeamAbbr'],
            'possession_team': play['possessionTeam'],
            'defensive_team': play['defensiveTeam'],
            'quarter': play['quarter'],
            'down': play['down'],
            'yards_to_go': play['yardsToGo'],
            'pass_result': play['passResult'],
            'pass_length': play['passLength'],
            'play_description': play['playDescription'],
            'coverage': play.get('pff_passCoverage', 'Unknown'),
            'formation': play.get('offenseFormation', 'Unknown')
        }


def extract_ball_in_air_frames(tracking: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Extract only the frames where the ball is in the air.

    Args:
        tracking: Full tracking data for a play

    Returns:
        Tuple of (filtered tracking data, info dict with frame indices)
    """
    # Find pass_forward event
    pass_forward_frame = tracking[
        tracking['event'] == 'pass_forward'
    ]['frameId'].min()

    # Find pass arrival/outcome events
    outcome_events = [
        'pass_arrived',
        'pass_outcome_caught',
        'pass_outcome_incomplete',
        'pass_outcome_interception'
    ]

    outcome_frame = tracking[
        tracking['event'].isin(outcome_events)
    ]['frameId'].min()

    # If we couldn't find clear markers, return full play
    if pd.isna(pass_forward_frame) or pd.isna(outcome_frame):
        return tracking, {
            'pass_forward_frame': None,
            'outcome_frame': None,
            'frames_in_air': len(tracking['frameId'].unique())
        }

    # Filter to ball-in-air frames
    ball_in_air = tracking[
        (tracking['frameId'] >= pass_forward_frame) &
        (tracking['frameId'] <= outcome_frame)
    ].copy()

    info = {
        'pass_forward_frame': pass_forward_frame,
        'outcome_frame': outcome_frame,
        'frames_in_air': len(ball_in_air['frameId'].unique()),
        'time_in_air': (outcome_frame - pass_forward_frame) / 10.0  # 10 Hz
    }

    return ball_in_air, info


if __name__ == "__main__":
    # Example usage
    loader = NFLDataLoader()

    # Load some pass plays
    pass_plays = loader.get_pass_plays(
        min_air_yards=20,
        pass_result=['C', 'IN']
    )

    print(f"Found {len(pass_plays)} deep pass plays")
    print(f"\nFirst play: {pass_plays.iloc[0]['playDescription']}")
