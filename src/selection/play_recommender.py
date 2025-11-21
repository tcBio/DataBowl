"""
Intelligent play recommendation system for YouTube overlay visualization.
Analyzes tracking data to find compelling plays with YouTube footage availability.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.loader import NFLDataLoader, extract_ball_in_air_frames


class PlayRecommender:
    """Recommend compelling plays for YouTube overlay visualization."""

    def __init__(self, loader: NFLDataLoader):
        """
        Initialize recommender.

        Args:
            loader: NFLDataLoader instance
        """
        self.loader = loader

    def score_play_for_youtube(self, play_row: pd.Series) -> Dict[str, float]:
        """
        Score a play's suitability for YouTube overlay visualization.

        Args:
            play_row: Single row from plays DataFrame

        Returns:
            Dictionary of scores and reasons
        """
        scores = {}

        # 1. Air Yards Score (longer = more time in air = better visualization)
        air_yards = play_row.get('passLength', 0)
        if pd.notna(air_yards):
            if air_yards >= 40:
                scores['air_yards'] = 10
            elif air_yards >= 25:
                scores['air_yards'] = 8
            elif air_yards >= 15:
                scores['air_yards'] = 5
            else:
                scores['air_yards'] = 2
        else:
            scores['air_yards'] = 0

        # 2. Play Result Score (completions and INTs more interesting than incompletions)
        result = play_row.get('passResult', '')
        if result == 'C':
            # Check if touchdown
            desc = str(play_row.get('playDescription', '')).upper()
            if 'TOUCHDOWN' in desc:
                scores['result'] = 10  # TDs almost always on YouTube
            else:
                scores['result'] = 7
        elif result == 'IN':
            scores['result'] = 9  # Interceptions are highlight-worthy
        else:
            scores['result'] = 3  # Incompletions less likely on YouTube

        # 3. Game Importance Score
        week = play_row.get('week', 0)
        if week >= 15:  # Playoff push
            scores['importance'] = 8
        elif week >= 10:
            scores['importance'] = 6
        else:
            scores['importance'] = 5

        # 4. Score Situation (close games more likely featured)
        home_score = play_row.get('preSnapHomeScore', 0)
        visitor_score = play_row.get('preSnapVisitorScore', 0)
        score_diff = abs(home_score - visitor_score)

        if score_diff <= 7:
            scores['situation'] = 8  # One score game
        elif score_diff <= 14:
            scores['situation'] = 6
        else:
            scores['situation'] = 4

        # 5. Down & Distance (clutch situations)
        down = play_row.get('down', 0)
        yards_to_go = play_row.get('yardsToGo', 0)

        if down == 3 or down == 4:
            if yards_to_go >= 7:
                scores['down_distance'] = 8  # 3rd/4th and long
            else:
                scores['down_distance'] = 6
        else:
            scores['down_distance'] = 5

        # 6. Quarter (late game more dramatic)
        quarter = play_row.get('quarter', 1)
        if quarter == 4:
            scores['quarter'] = 8
        elif quarter == 3:
            scores['quarter'] = 6
        else:
            scores['quarter'] = 5

        # Total score (weighted average)
        weights = {
            'air_yards': 0.25,      # Most important for visualization
            'result': 0.20,         # Completions/INTs more likely on YouTube
            'importance': 0.15,
            'situation': 0.15,
            'down_distance': 0.15,
            'quarter': 0.10
        }

        total_score = sum(scores[k] * weights[k] for k in scores.keys())

        return {
            'total_score': total_score,
            'breakdown': scores
        }

    def get_youtube_search_quality(self, play_row: pd.Series) -> str:
        """
        Estimate likelihood of finding YouTube footage.

        Args:
            play_row: Single row from plays DataFrame

        Returns:
            'HIGH', 'MEDIUM', or 'LOW'
        """
        score_info = self.score_play_for_youtube(play_row)
        total = score_info['total_score']

        if total >= 7.5:
            return 'HIGH'
        elif total >= 6.0:
            return 'MEDIUM'
        else:
            return 'LOW'

    def analyze_play_inventory(self) -> pd.DataFrame:
        """
        Analyze all pass plays and score them.

        Returns:
            DataFrame with plays and scores
        """
        # Get all pass plays
        pass_plays = self.loader.plays[
            (self.loader.plays['isDropback'] == True) &
            (self.loader.plays['passResult'].isin(['C', 'I', 'IN']))
        ].copy()

        print(f"Analyzing {len(pass_plays)} pass plays...")

        # Score each play
        scores = []
        for idx, play in pass_plays.iterrows():
            score_info = self.score_play_for_youtube(play)
            scores.append({
                'gameId': play['gameId'],
                'playId': play['playId'],
                'total_score': score_info['total_score'],
                'youtube_likelihood': self.get_youtube_search_quality(play),
                **score_info['breakdown']
            })

        scores_df = pd.DataFrame(scores)

        # Merge with play data
        result = pass_plays.merge(scores_df, on=['gameId', 'playId'])

        # Sort by score
        result = result.sort_values('total_score', ascending=False)

        print(f"Scored {len(result)} plays")
        print(f"HIGH YouTube likelihood: {len(result[result['youtube_likelihood'] == 'HIGH'])}")
        print(f"MEDIUM YouTube likelihood: {len(result[result['youtube_likelihood'] == 'MEDIUM'])}")

        return result

    def get_top_recommendations(
        self,
        n: int = 20,
        min_air_yards: float = 20,
        youtube_quality: str = 'HIGH'
    ) -> pd.DataFrame:
        """
        Get top N play recommendations.

        Args:
            n: Number of plays to return
            min_air_yards: Minimum air yards
            youtube_quality: 'HIGH', 'MEDIUM', or 'LOW'

        Returns:
            DataFrame with top recommendations
        """
        # Analyze inventory
        scored_plays = self.analyze_play_inventory()

        # Filter
        filtered = scored_plays[
            (scored_plays['passLength'] >= min_air_yards) &
            (scored_plays['youtube_likelihood'] == youtube_quality)
        ]

        # Get top N
        top_plays = filtered.head(n)

        return top_plays

    def generate_youtube_query(self, play_row: pd.Series) -> str:
        """
        Generate YouTube search query for a play.

        Args:
            play_row: Single row from plays DataFrame

        Returns:
            YouTube search query string
        """
        # Get game info
        game = self.loader.games[
            self.loader.games['gameId'] == play_row['gameId']
        ].iloc[0]

        # Get teams
        home_team = game['homeTeamAbbr']
        away_team = game['visitorTeamAbbr']
        possession = play_row['possessionTeam']
        defense = play_row['defensiveTeam']

        # Get play details
        desc = str(play_row['playDescription'])
        yards = int(play_row['passLength']) if pd.notna(play_row['passLength']) else 0

        # Extract QB and receiver from description
        # Format is usually "QB pass [direction] to RECEIVER"
        qb_name = "QB"
        receiver_name = "receiver"

        if " pass " in desc and " to " in desc:
            parts = desc.split(" pass ")
            if len(parts) > 0:
                qb_part = parts[0].strip().split()
                if qb_part:
                    qb_name = qb_part[-1]  # Last word before "pass"

            parts = desc.split(" to ")
            if len(parts) > 1:
                receiver_part = parts[1].strip().split()
                if receiver_part:
                    receiver_name = receiver_part[0]  # First word after "to"

        # Build query
        query_parts = []

        # Add player names if extracted
        if qb_name != "QB":
            query_parts.append(qb_name)

        if receiver_name != "receiver":
            query_parts.append(receiver_name)

        # Add yards if significant
        if yards >= 20:
            query_parts.append(f"{yards} yards")

        # Add teams
        query_parts.append(possession)
        query_parts.append("vs")
        query_parts.append(defense)

        # Add year
        season = game.get('season', 2023)
        query_parts.append(str(season))

        # Add result type
        if play_row['passResult'] == 'IN':
            query_parts.append("interception")
        elif 'TOUCHDOWN' in desc.upper():
            query_parts.append("touchdown")
        else:
            query_parts.append("highlights")

        return " ".join(query_parts)

    def create_recommendation_report(
        self,
        output_path: str = "RECOMMENDED_PLAYS.md"
    ) -> str:
        """
        Create detailed recommendation report.

        Args:
            output_path: Path to save markdown report

        Returns:
            Path to created report
        """
        # Get top recommendations
        top_20 = self.get_top_recommendations(n=20, min_air_yards=20, youtube_quality='HIGH')

        # Build markdown report
        lines = []
        lines.append("# Recommended Plays for YouTube Overlay Visualization")
        lines.append("")
        lines.append("## Selection Criteria")
        lines.append("")
        lines.append("Plays are scored on:")
        lines.append("- **Air Yards** (25%): Longer passes = more time in air = better visualization")
        lines.append("- **Play Result** (20%): TDs and INTs more likely on YouTube")
        lines.append("- **Game Importance** (15%): Late season games featured more")
        lines.append("- **Score Situation** (15%): Close games more dramatic")
        lines.append("- **Down & Distance** (15%): 3rd/4th down clutch moments")
        lines.append("- **Quarter** (10%): 4th quarter most exciting")
        lines.append("")
        lines.append(f"**Total Plays Analyzed:** {len(self.loader.plays)}")
        lines.append(f"**Pass Plays:** {len(self.loader.plays[self.loader.plays['isDropback'] == True])}")
        lines.append(f"**High YouTube Likelihood:** {len(top_20)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Top 20 Recommended Plays")
        lines.append("")

        for idx, (_, play) in enumerate(top_20.iterrows(), 1):
            game = self.loader.games[
                self.loader.games['gameId'] == play['gameId']
            ].iloc[0]

            lines.append(f"### Play #{idx}: {play['possessionTeam']} vs {play['defensiveTeam']}")
            lines.append("")

            # Game info
            lines.append(f"**Game:** Week {play['week']}, {game['gameDate']}")
            lines.append(f"**Teams:** {game['homeTeamAbbr']} vs {game['visitorTeamAbbr']}")
            lines.append(f"**Score:** {play['preSnapHomeScore']}-{play['preSnapVisitorScore']}")
            lines.append("")

            # Play details
            lines.append(f"**Situation:** Q{play['quarter']}, {play['down']}")
            if play['down'] in [1, 2, 3, 4]:
                down_text = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th'}[play['down']]
                lines.append(f" & {play['yardsToGo']} at {play['yardlineSide']} {play['yardlineNumber']}")
            lines.append("")

            # Play description
            desc = str(play['playDescription'])[:150]
            lines.append(f"**Play:** {desc}...")
            lines.append("")

            # Key metrics
            lines.append(f"**Air Yards:** {play['passLength']:.1f}")
            lines.append(f"**Result:** {play['passResult']}")
            if pd.notna(play.get('pff_passCoverage')):
                lines.append(f"**Coverage:** {play['pff_passCoverage']}")
            lines.append("")

            # Scoring
            lines.append(f"**Visualization Score:** {play['total_score']:.2f}/10")
            lines.append(f"**YouTube Likelihood:** {play['youtube_likelihood']}")
            lines.append("")

            # YouTube search
            query = self.generate_youtube_query(play)
            lines.append(f"**YouTube Search:**")
            lines.append(f"```")
            lines.append(query)
            lines.append(f"```")
            lines.append("")

            # Direct link
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            lines.append(f"[Search YouTube]({search_url})")
            lines.append("")

            # Why compelling
            lines.append(f"**Why This Play:**")
            reasons = []

            if play['passLength'] >= 40:
                reasons.append(f"- Deep pass ({play['passLength']:.0f} yards) = extended ball-in-air time")

            if 'TOUCHDOWN' in desc.upper():
                reasons.append("- Touchdown = guaranteed YouTube highlights")

            if play['passResult'] == 'IN':
                reasons.append("- Interception = dramatic defensive play")

            if play['down'] >= 3:
                reasons.append(f"- {play['down']}rd/4th down clutch situation")

            if abs(play['preSnapHomeScore'] - play['preSnapVisitorScore']) <= 7:
                reasons.append("- One-score game = high stakes")

            if play['quarter'] == 4:
                reasons.append("- 4th quarter drama")

            for reason in reasons:
                lines.append(reason)

            lines.append("")

            # Game/Play IDs for loading
            lines.append(f"**Data:** `gameId={play['gameId']}`, `playId={play['playId']}`")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Summary stats
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append(f"- Average Air Yards: {top_20['passLength'].mean():.1f}")
        lines.append(f"- Average Score: {top_20['total_score'].mean():.2f}/10")
        lines.append(f"- Touchdowns: {len(top_20[top_20['playDescription'].str.contains('TOUCHDOWN', case=False, na=False)])}")
        lines.append(f"- Interceptions: {len(top_20[top_20['passResult'] == 'IN'])}")
        lines.append(f"- 4th Quarter: {len(top_20[top_20['quarter'] == 4])}")
        lines.append("")

        # Write to file
        output = "\n".join(lines)

        with open(output_path, 'w') as f:
            f.write(output)

        print(f"Recommendation report saved to: {output_path}")

        return output_path


if __name__ == "__main__":
    print("Play Recommender for YouTube Overlay Visualization")
    print("\nUsage:")
    print("""
    from src.selection.play_recommender import PlayRecommender
    from src.data.loader import NFLDataLoader

    # Load data
    loader = NFLDataLoader('data/raw')

    # Create recommender
    recommender = PlayRecommender(loader)

    # Get top 20 plays
    top_plays = recommender.get_top_recommendations(n=20)

    # Generate report
    recommender.create_recommendation_report('RECOMMENDED_PLAYS.md')
    """)
