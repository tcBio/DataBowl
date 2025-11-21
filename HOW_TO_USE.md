# How to Use This Project - Quick Start Guide

## ✅ What You Have Now

A complete YouTube overlay pipeline with intelligent play recommendation system.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Place Your Data

You mentioned you already downloaded the NFL data. Place the CSV files here:

```
data/raw/
├── games.csv
├── plays.csv
├── players.csv
├── player_play.csv
├── tracking_week_1.csv
├── tracking_week_2.csv
├── ... (all tracking files)
└── tracking_week_9.csv
```

**Note:** These files are gitignored (won't be committed) - that's correct!

### Step 2: Generate Play Recommendations

Run the automated play recommendation system:

**Option A: Command Line (Fastest)**
```bash
python generate_play_recommendations.py
```

**Option B: Jupyter Notebook (Interactive)**
```bash
jupyter notebook notebooks/02_play_selection.ipynb
```

**What This Does:**
- Loads all your NFL data
- Analyzes ~20,000+ pass plays
- Scores each play for YouTube overlay suitability
- Generates top 20 recommendations with YouTube search queries
- Creates detailed report: `RECOMMENDED_PLAYS.md`
- Exports CSV: `outputs/top_20_plays.csv`
- Tests ball-in-air extraction on #1 play

**Output Example:**
```
TOP 5 PREVIEW
=============

1. KC vs BUF (Week 6)
   Score: 8.5/10 | Air Yards: 48 | Result: C
   Mahomes pass deep right to Kelce for 48 yards TOUCHDOWN...
   YouTube: Mahomes Kelce 48 yards KC vs BUF 2023 touchdown

2. LAC vs LV (Week 4)
   Score: 8.3/10 | Air Yards: 52 | Result: C
   Herbert pass deep middle to Allen for 52 yards...
   YouTube: Herbert Allen 52 yards LAC vs LV 2023 highlights

...
```

### Step 3: Review Recommendations

Open the generated report:

```bash
cat RECOMMENDED_PLAYS.md
# or
open RECOMMENDED_PLAYS.md
```

**What You'll Find:**
- Top 20 plays ranked by overlay visualization quality
- YouTube search queries for each play
- Direct YouTube search links
- Why each play is compelling
- Game/Play IDs for data loading
- Estimated ball-in-air time
- Summary statistics

---

## 📊 What the Recommender Scores

Each play is scored on:

1. **Air Yards (25%)** - Longer passes = more time for visualization
   - 40+ yards: 10/10
   - 25-40 yards: 8/10
   - 15-25 yards: 5/10

2. **Play Result (20%)** - YouTube availability
   - Touchdown: 10/10
   - Interception: 9/10
   - Completion: 7/10
   - Incomplete: 3/10

3. **Game Importance (15%)** - Prime time, playoffs
4. **Score Situation (15%)** - Close games
5. **Down & Distance (15%)** - 3rd/4th down clutch moments
6. **Quarter (10%)** - 4th quarter drama

**YouTube Likelihood:**
- **HIGH** (Score ≥7.5): Famous plays, very likely on YouTube
- **MEDIUM** (Score 6.0-7.5): Good plays, possibly on YouTube
- **LOW** (Score <6.0): May need alternate footage

---

## 🎬 Next Steps After Getting Recommendations

### 1. Find YouTube Footage (Manual)

For each recommended play:

```bash
# Example from RECOMMENDED_PLAYS.md
Play #1: KC vs BUF (Week 6)
YouTube Search: "Mahomes Kelce 48 yards KC vs BUF 2023 touchdown"
```

**Click the search link** or paste query into YouTube.

**Tips:**
- Look for "highlights" or "all plays" compilations
- Prime time games (SNF, MNF) have better coverage
- Playoff games guaranteed footage
- Check NFL's official channel

### 2. Download Video Clip

Once you find the play on YouTube:

```python
from src.video.downloader import YouTubeDownloader

downloader = YouTubeDownloader(output_dir='data/videos')

# Download and trim to just the play
video_path = downloader.download_video(
    url="https://www.youtube.com/watch?v=abc123",
    output_name="play_1_mahomes_kelce",
    start_time="02:15",  # When play starts in video
    end_time="02:25"     # When play ends
)
```

### 3. Load Tracking Data for That Play

```python
from src.data.loader import NFLDataLoader, extract_ball_in_air_frames

# From RECOMMENDED_PLAYS.md
game_id = 2023100800  # Example
play_id = 1234        # Example

# Load data
loader = NFLDataLoader('data/raw')
tracking = loader.get_play_tracking(game_id, play_id)

# Extract ONLY ball-in-air frames
ball_in_air, info = extract_ball_in_air_frames(tracking)

print(f"Ball in air for {info['time_in_air']:.2f} seconds")
```

### 4. Create Overlay (See Implementation Guide)

Full workflow in: `YOUTUBE_OVERLAY_IMPLEMENTATION_GUIDE.md`

---

## 📁 Project Structure Explained

```
DataBowl/
│
├── generate_play_recommendations.py  ← RUN THIS FIRST!
│
├── data/
│   ├── raw/                          ← PUT YOUR CSV FILES HERE
│   └── videos/                       ← Downloaded YouTube clips
│
├── src/
│   ├── data/
│   │   └── loader.py                 ← Load NFL data
│   ├── selection/
│   │   └── play_recommender.py       ← Intelligent play scoring
│   ├── video/
│   │   ├── downloader.py             ← Download YouTube footage
│   │   ├── synchronizer.py           ← Sync data with video
│   │   └── overlay.py                ← Render overlays
│   └── visualization/
│       └── field.py                  ← Animated field (fallback)
│
├── notebooks/
│   ├── 01_exploratory_data_analysis.ipynb
│   └── 02_play_selection.ipynb       ← Interactive play selection
│
├── outputs/
│   ├── top_20_plays.csv              ← Generated by recommender
│   └── videos/                       ← Final overlaid videos
│
└── Documentation/
    ├── HOW_TO_USE.md                 ← YOU ARE HERE
    ├── RECOMMENDED_PLAYS.md          ← Generated recommendations
    ├── PROJECT_ALIGNMENT.md          ← Competition alignment proof
    ├── YOUTUBE_OVERLAY_IMPLEMENTATION_GUIDE.md
    ├── YOUTUBE_OVERLAY_STRATEGY.md
    └── CRITICAL_RECOMMENDATIONS.md
```

---

## 🔧 Troubleshooting

### "Error: Data directory not found"

**Solution:**
```bash
# Create directory if needed
mkdir -p data/raw

# Copy your downloaded CSV files
cp /path/to/your/downloads/*.csv data/raw/
```

### "Error: Missing required data files"

You need at minimum:
- `games.csv`
- `plays.csv`
- `players.csv`
- At least one `tracking_week_X.csv`

Download from: https://www.kaggle.com/competitions/nfl-big-data-bowl-2026-analytics/data

### "No plays found with HIGH YouTube likelihood"

This means:
- Data might be incomplete
- Adjust criteria in recommender:
  ```python
  top_plays = recommender.get_top_recommendations(
      n=20,
      min_air_yards=15,        # Lower threshold
      youtube_quality='MEDIUM'  # Accept medium quality
  )
  ```

---

## 📈 Expected Output

After running `generate_play_recommendations.py`:

**Console Output:**
```
===========================================
NFL Big Data Bowl 2026 - Play Recommendation Generator
===========================================

Loading NFL data...
✅ Data loaded successfully!
   Games: 272
   Plays: 45,623
   Players: 2,845

Initializing Play Recommender...
✅ Recommender ready

Analyzing play inventory...
Analyzing 18,234 pass plays...
Scored 18,234 plays
HIGH YouTube likelihood: 156
MEDIUM YouTube likelihood: 1,234

✅ Found 20 highly recommended plays

[... TOP 5 PREVIEW ...]

GENERATING REPORTS
✅ RECOMMENDED_PLAYS.md
✅ outputs/top_20_plays.csv

TESTING BALL-IN-AIR EXTRACTION (Play #1)
Results:
  Total frames: 87
  Ball-in-air frames: 23
  Duration: 2.30 seconds
  ✅ EXCELLENT! 2.30s is perfect for overlay visualization

✅ COMPLETE!
```

**Files Created:**
- `RECOMMENDED_PLAYS.md` (detailed report with YouTube links)
- `outputs/top_20_plays.csv` (spreadsheet for easy filtering)

---

## 🎯 Your Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR WORKFLOW                            │
└─────────────────────────────────────────────────────────────┘

1. [YOU] Place CSV files in data/raw/             ← START HERE

2. [AUTO] Run: python generate_play_recommendations.py
          ↓
          Creates RECOMMENDED_PLAYS.md with top 20 plays
          Each play has YouTube search query

3. [YOU] Open RECOMMENDED_PLAYS.md
          ↓
          Pick top 5-7 plays that look most compelling

4. [YOU] Search YouTube for each play
          ↓
          Find video footage

5. [AUTO] Download video with downloader.py

6. [AUTO] Load tracking data with loader.py

7. [AUTO] Sync video & data with synchronizer.py

8. [AUTO] Render overlays with overlay.py

9. [YOU] Submit 5-7 amazing visualizations!
```

---

## ⏱️ Time Estimates

- **Place data files:** 5 minutes
- **Run recommendations:** 2-5 minutes
- **Review plays:** 10 minutes
- **Search YouTube:** 20-30 minutes (for 5 plays)
- **Download videos:** 10 minutes
- **First overlay (proof of concept):** 2-3 hours
- **Each additional overlay:** 30-60 minutes

**Total to 5 visualizations:** ~8-10 hours

---

## 🆘 Need Help?

**Documentation:**
1. `HOW_TO_USE.md` ← You are here (getting started)
2. `RECOMMENDED_PLAYS.md` ← Generated play list
3. `YOUTUBE_OVERLAY_IMPLEMENTATION_GUIDE.md` ← Full technical workflow
4. `PROJECT_ALIGNMENT.md` ← Why this approach wins

**Key Scripts:**
- `generate_play_recommendations.py` ← Generate play list
- `notebooks/02_play_selection.ipynb` ← Interactive exploration

**Quick Reference:**
```python
# Load data
from src.data.loader import NFLDataLoader
loader = NFLDataLoader('data/raw')

# Get recommendations
from src.selection.play_recommender import PlayRecommender
recommender = PlayRecommender(loader)
top_plays = recommender.get_top_recommendations(n=20)

# Download video
from src.video.downloader import YouTubeDownloader
downloader = YouTubeDownloader()
video = downloader.download_video(url, output_name="play1")

# Extract ball-in-air
from src.data.loader import extract_ball_in_air_frames
tracking = loader.get_play_tracking(game_id, play_id)
ball_in_air, info = extract_ball_in_air_frames(tracking)
```

---

## ✅ You're Ready!

**You have:**
- ✅ Complete implementation
- ✅ Intelligent play recommender
- ✅ YouTube download tools
- ✅ Video synchronization
- ✅ Overlay rendering
- ✅ Step-by-step guides

**You need:**
- ⏳ Run `python generate_play_recommendations.py`
- ⏳ Find YouTube footage for top plays
- ⏳ Create your first overlay!

**Start now:** `python generate_play_recommendations.py`
