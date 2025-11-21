#!/usr/bin/env python3
"""
Generate play recommendations for YouTube overlay visualization.

Usage:
    python generate_play_recommendations.py

Output:
    - RECOMMENDED_PLAYS.md: Detailed recommendation report
    - outputs/top_20_plays.csv: CSV export of top plays
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data.loader import NFLDataLoader, extract_ball_in_air_frames
from selection.play_recommender import PlayRecommender


def main():
    """Generate play recommendations."""

    print("="*80)
    print("NFL Big Data Bowl 2026 - Play Recommendation Generator")
    print("="*80)
    print()

    # Check if data exists
    data_dir = Path('data/raw')
    if not data_dir.exists():
        print(f"❌ Error: Data directory not found: {data_dir}")
        print()
        print("Please download the NFL Big Data Bowl 2026 data from Kaggle:")
        print("https://www.kaggle.com/competitions/nfl-big-data-bowl-2026-analytics/data")
        print()
        print("Place the CSV files in: data/raw/")
        return 1

    # Check for required files
    required_files = ['games.csv', 'plays.csv', 'players.csv']
    missing_files = [f for f in required_files if not (data_dir / f).exists()]

    if missing_files:
        print(f"❌ Error: Missing required data files: {missing_files}")
        print()
        print("Please ensure these files are in data/raw/:")
        for f in required_files:
            print(f"  - {f}")
        return 1

    # Load data
    print("Loading NFL data...")
    try:
        loader = NFLDataLoader(str(data_dir))
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return 1

    print(f"✅ Data loaded successfully!")
    print(f"   Games: {len(loader.games)}")
    print(f"   Plays: {len(loader.plays)}")
    print(f"   Players: {len(loader.players)}")
    print()

    # Initialize recommender
    print("Initializing Play Recommender...")
    recommender = PlayRecommender(loader)
    print("✅ Recommender ready")
    print()

    # Get top recommendations
    print("Analyzing play inventory and scoring for YouTube overlay suitability...")
    print("(This may take a minute...)")
    print()

    try:
        top_20 = recommender.get_top_recommendations(
            n=20,
            min_air_yards=20,
            youtube_quality='HIGH'
        )
    except Exception as e:
        print(f"❌ Error analyzing plays: {e}")
        return 1

    print(f"✅ Found {len(top_20)} highly recommended plays")
    print()

    # Display summary
    print("="*80)
    print("TOP 5 PREVIEW")
    print("="*80)
    print()

    for idx, (_, play) in enumerate(top_20.head(5).iterrows(), 1):
        print(f"{idx}. {play['possessionTeam']} vs {play['defensiveTeam']} (Week {play['week']})")
        print(f"   Score: {play['total_score']:.2f}/10 | Air Yards: {play['passLength']:.0f} | Result: {play['passResult']}")
        desc = str(play['playDescription'])[:70]
        print(f"   {desc}...")

        # YouTube search
        query = recommender.generate_youtube_query(play)
        print(f"   YouTube: {query}")
        print()

    print("(See RECOMMENDED_PLAYS.md for full details)")
    print()

    # Generate report
    print("="*80)
    print("GENERATING REPORTS")
    print("="*80)
    print()

    print("1. Creating detailed markdown report...")
    try:
        report_path = recommender.create_recommendation_report(
            output_path='RECOMMENDED_PLAYS.md'
        )
        print(f"   ✅ {report_path}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 1

    print()
    print("2. Exporting top plays to CSV...")
    try:
        output_dir = Path('outputs')
        output_dir.mkdir(exist_ok=True)

        export_cols = [
            'gameId', 'playId', 'week', 'quarter', 'down', 'yardsToGo',
            'possessionTeam', 'defensiveTeam', 'passLength', 'passResult',
            'total_score', 'youtube_likelihood', 'playDescription'
        ]

        csv_path = output_dir / 'top_20_plays.csv'
        top_20[export_cols].to_csv(csv_path, index=False)
        print(f"   ✅ {csv_path}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 1

    print()

    # Test ball-in-air extraction
    print("="*80)
    print("TESTING BALL-IN-AIR EXTRACTION (Play #1)")
    print("="*80)
    print()

    test_play = top_20.iloc[0]
    game_id = test_play['gameId']
    play_id = test_play['playId']

    print(f"Play: {test_play['playDescription'][:80]}...")
    print()

    try:
        # Get metadata
        metadata = loader.get_play_metadata(game_id, play_id)

        # Load tracking
        print("Loading tracking data...")
        tracking = loader.get_play_tracking(game_id, play_id, week=metadata['week'])

        # Extract ball-in-air
        print("Extracting ball-in-air period...")
        ball_in_air, info = extract_ball_in_air_frames(tracking)

        print()
        print("Results:")
        print(f"  Total frames: {len(tracking['frameId'].unique())}")
        print(f"  Ball-in-air frames: {info['frames_in_air']}")
        print(f"  Duration: {info['time_in_air']:.2f} seconds")

        if info['time_in_air'] >= 2.0:
            print(f"  ✅ EXCELLENT! {info['time_in_air']:.2f}s is perfect for overlay visualization")
        elif info['time_in_air'] >= 1.5:
            print(f"  ✓ Good! {info['time_in_air']:.2f}s is workable")
        else:
            print(f"  ⚠ Note: {info['time_in_air']:.2f}s is brief (consider longer plays)")

    except Exception as e:
        print(f"⚠ Could not test ball-in-air extraction: {e}")
        print("(This is OK - tracking data might not be downloaded yet)")

    print()

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print(f"✅ Generated recommendations for {len(top_20)} plays")
    print()
    print("Statistics:")
    print(f"  Average Air Yards: {top_20['passLength'].mean():.1f}")
    print(f"  Average Score: {top_20['total_score'].mean():.2f}/10")
    print(f"  Touchdowns: {len(top_20[top_20['playDescription'].str.contains('TOUCHDOWN', case=False, na=False)])}")
    print(f"  Interceptions: {len(top_20[top_20['passResult'] == 'IN'])}")
    print(f"  4th Quarter: {len(top_20[top_20['quarter'] == 4])}")
    print()

    print("Next Steps:")
    print("  1. Review RECOMMENDED_PLAYS.md for detailed play information")
    print("  2. Search YouTube using the provided queries")
    print("  3. Download footage for plays with available video")
    print("  4. Test synchronization with top-ranked plays")
    print("  5. Create proof-of-concept overlay for 1 play")
    print()

    print("="*80)
    print("✅ COMPLETE!")
    print("="*80)

    return 0


if __name__ == "__main__":
    exit(main())
