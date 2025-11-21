# Data Documentation

## Overview

This document describes the data used for the NFL Big Data Bowl 2026 Broadcast Visualization Track submission.

**Data Source**: [Kaggle - NFL Big Data Bowl 2026](https://www.kaggle.com/competitions/nfl-big-data-bowl-2026-analytics/data)

**Seasons Covered**: 2023-2024 NFL Regular Season

**Focus**: Pass plays with player tracking data while the ball is in the air

## Dataset Files

### 1. `tracking_week_[1-9].csv`
Player tracking data captured at 10 Hz (10 frames per second).

**Key Columns**:
- `gameId`: Unique game identifier
- `playId`: Unique play identifier within the game
- `nflId`: Unique player identifier (null for the ball)
- `frameId`: Frame number (starts at 1 for each play)
- `time`: Timestamp of the frame
- `jerseyNumber`: Player jersey number
- `club`: Team abbreviation (home/away/football)
- `playDirection`: Direction of play (left/right)
- `x`: Player x-coordinate (0-120 yards, parallel to sideline)
- `y`: Player y-coordinate (0-53.3 yards, parallel to end zone)
- `s`: Speed in yards/second
- `a`: Acceleration in yards/second²
- `dis`: Distance traveled from prior frame (yards)
- `o`: Player orientation (degrees, 0-360)
- `dir`: Direction of player movement (degrees, 0-360)
- `event`: Play event (e.g., 'pass_forward', 'pass_arrived', 'tackle', etc.)

**Critical Events for Broadcast Visualization**:
- `pass_forward`: QB releases the ball
- `pass_arrived`: Ball arrives at target location
- `pass_outcome_caught`: Pass is caught
- `pass_outcome_incomplete`: Pass is incomplete
- `pass_outcome_interception`: Pass is intercepted
- `pass_outcome_touchback`: Pass results in touchback

**Coordinate System**:
- Field is 120 yards long (including end zones): x ∈ [0, 120]
- Field is 53.3 yards wide: y ∈ [0, 53.3]
- x=0 is one end zone, x=120 is the other end zone
- y=0 is one sideline, y=53.3 is the other sideline
- `playDirection` indicates which direction offense is moving

### 2. `games.csv`
Game-level information.

**Key Columns**:
- `gameId`: Unique game identifier
- `season`: Season year
- `week`: Week number
- `gameDate`: Date of the game
- `gameTimeEastern`: Game start time (ET)
- `homeTeamAbbr`: Home team abbreviation
- `visitorTeamAbbr`: Visiting team abbreviation
- `homeFinalScore`: Home team final score
- `visitorFinalScore`: Visitor team final score

### 3. `plays.csv`
Play-level information and outcomes.

**Key Columns**:
- `gameId`: Unique game identifier
- `playId`: Unique play identifier
- `ballCarrierId`: Player ID of ball carrier (null for passes)
- `ballCarrierName`: Player name of ball carrier
- `playDescription`: Text description of the play
- `quarter`: Quarter of the play
- `down`: Down (1-4)
- `yardsToGo`: Yards needed for first down
- `possessionTeam`: Team with possession
- `defensiveTeam`: Team on defense
- `yardlineSide`: Side of field for line of scrimmage
- `yardlineNumber`: Yardline number (0-50)
- `gameClock`: Time remaining in quarter
- `preSnapHomeScore`: Home score before play
- `preSnapVisitorScore`: Visitor score before play
- `passResult`: Pass outcome (C=Complete, I=Incomplete, IN=Intercepted, etc.)
- `passLength`: Air yards (distance ball travels in air)
- `penaltyYards`: Penalty yards (if applicable)
- `prePenaltyPlayResult`: Yards gained before penalty
- `playResult`: Actual yards gained
- `isDropback`: Whether play involves a dropback
- `passProbability`: Pre-snap probability of pass (0-1)

**Pass-Specific Columns**:
- `passResult`: C (Complete), I (Incomplete), IN (Intercepted), S (Sack), R (Scramble)
- `offenseFormation`: Offensive formation (SHOTGUN, UNDER_CENTER, etc.)
- `personnelO`: Offensive personnel grouping
- `personnelD`: Defensive personnel grouping
- `dropbackType`: Type of dropback (TRADITIONAL, PLAY_ACTION, etc.)
- `pff_passCoverage`: Coverage type (Cover 1, Cover 2, etc.)
- `pff_passCoverageType`: Man or Zone coverage

### 4. `players.csv`
Player information.

**Key Columns**:
- `nflId`: Unique player identifier
- `displayName`: Player display name
- `position`: Position (QB, WR, TE, CB, S, etc.)
- `height`: Player height
- `weight`: Player weight
- `collegeName`: College attended

### 5. `player_play.csv`
Player-play relationships and statistics.

**Key Columns**:
- `gameId`: Unique game identifier
- `playId`: Unique play identifier
- `nflId`: Unique player identifier
- `hadRushAttempt`: Boolean - player had rush attempt
- `wasRusher`: Boolean - player was the rusher
- `passResult`: Result of pass (if player involved)
- `hadPassReception`: Boolean - player caught the pass
- `wasTargettedReceiver`: Boolean - player was targeted
- `hadInterception`: Boolean - player intercepted pass
- `hadDefensiveFumbleRecovery`: Boolean - player recovered fumble
- `inMotionAtBallSnap`: Boolean - player was in motion at snap
- `shiftSinceLineset`: Boolean - player shifted since line was set
- `motionSinceLineset`: Boolean - player in motion since line set

## Data Processing Notes

### Filtering for Ball-in-Air Analysis

To focus on player movement while the ball is in the air:

1. **Identify pass plays**: Filter `plays.csv` where `isDropback == True` and `passResult` in ['C', 'I', 'IN']

2. **Extract ball-in-air frames**:
   - Start frame: Where `event == 'pass_forward'` (QB releases ball)
   - End frame: Where `event` in ['pass_arrived', 'pass_outcome_caught', 'pass_outcome_incomplete', 'pass_outcome_interception']

3. **Ball trajectory**: Track rows where `club == 'football'` and `nflId` is null

### Key Metrics to Calculate

**For Receivers**:
- **Separation**: Distance from nearest defender at each frame
- **Target separation**: Separation at moment ball arrives
- **Route depth**: Maximum depth achieved during route
- **Route break points**: Frames where direction changes significantly

**For Defenders**:
- **Coverage quality**: How close defender stays to receiver
- **Recovery speed**: How quickly defender closes separation gap
- **Help coverage**: Distance to nearest help defender

**For Ball**:
- **Time in air**: Duration from release to arrival
- **Air yards**: Horizontal distance traveled
- **Arc height**: Estimate maximum height of ball trajectory
- **Target accuracy**: How close ball lands to receiver

## Data Quality Issues

### Missing Values
- Some `nflId` values may be null (especially for the ball)
- `pff_passCoverage` may be null for some plays
- Event markers may be missing or inconsistent

### Known Issues
- Coordinate system occasionally flips (check `playDirection`)
- Some frames may have timing irregularities
- Ball tracking may be less accurate than player tracking

## Recommendations for Visualization

### Interesting Plays to Visualize

1. **Deep shots**: `passLength > 30` - Dramatic separation and timing
2. **Contested catches**: `passResult == 'C'` with low target separation
3. **Interceptions**: `passResult == 'IN'` - Defender breaks on ball
4. **Coverage breakdowns**: High separation at target (>5 yards)
5. **Perfect coverage**: Complete passes with tight coverage (<2 yards)

### Visual Elements to Include

- **Field overlay**: Yard lines, hash marks, end zones
- **Player markers**: Different colors/shapes for offense/defense
- **Ball trajectory**: Arc showing ball path
- **Separation lines**: Lines connecting receivers to nearest defenders
- **Speed indicators**: Arrows or trails showing player speed/direction
- **Time remaining**: Show how much time left until ball arrival
- **Coverage shells**: Voronoi diagrams or coverage zones

## Data Size

- **Total tracking data**: ~10-15GB (all weeks combined)
- **Unique games**: ~500 games (2023-2024 seasons)
- **Pass plays**: ~20,000-30,000 pass plays
- **Frames per play**: ~30-100 frames (3-10 seconds at 10 Hz)

## Update Log

- **2025-11-21**: Initial data documentation created
- **[Add date]**: Add notes after data exploration
- **[Add date]**: Add specific play IDs for visualization candidates

---

**Note**: This document should be updated as you explore the data and identify specific plays, patterns, or issues relevant to your broadcast visualization.
