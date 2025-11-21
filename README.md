# NFL Big Data Bowl 2026 - Broadcast Visualization Track

## Project Overview

This project is a submission for the **NFL Big Data Bowl 2026 - Broadcast Visualization Track**. The goal is to create compelling animations, videos, or charts that visualize player movement while the ball is in the air during pass plays.

**Competition Deadline**: December 17, 2025
**Track**: Broadcast Visualization
**Objective**: Generate animations/visualizations that best visualize the movement of players with the ball in the air

## Project Structure

```
.
├── data/
│   ├── raw/              # Raw data from Kaggle (not committed to git)
│   └── processed/        # Processed/cleaned data
├── notebooks/            # Jupyter notebooks for exploration and prototyping
├── src/
│   ├── data/            # Data loading and processing utilities
│   ├── visualization/   # Visualization utilities and functions
│   └── animation/       # Animation generation code
├── outputs/
│   ├── videos/          # Final video outputs
│   ├── animations/      # HTML/interactive animations
│   ├── images/          # Static images/frames
│   └── figures/         # Publication-quality figures
├── submissions/         # Final competition submissions
├── reports/             # Analysis reports and documentation
└── data.md             # Data documentation
```

## Data

See [data.md](data.md) for detailed information about the datasets used in this project.

## Setup

### Requirements

```bash
pip install -r requirements.txt
```

### Data Download

1. Download the data from [Kaggle NFL Big Data Bowl 2026](https://www.kaggle.com/competitions/nfl-big-data-bowl-2026-analytics/data)
2. Place the CSV files in `data/raw/`

## Visualization Approach

### Key Focus Areas

1. **Player Tracking Visualization**: Visualize player movement and positioning while the ball is in the air
2. **Ball Trajectory**: Show the football's path through the air
3. **Coverage Dynamics**: Highlight defensive coverage and receiver separation
4. **Timing and Spacing**: Demonstrate the timing between QB release and receiver position
5. **Storytelling**: Create narratives around specific plays or patterns

### Technical Stack

- **Data Processing**: pandas, numpy, polars
- **Visualization**: matplotlib, plotly, seaborn
- **Animation**: matplotlib.animation, plotly animated charts, manim (optional)
- **Video Editing**: moviepy, opencv
- **Interactive**: Plotly Dash, Streamlit (optional)

## Development Workflow

1. **Exploratory Data Analysis** (`notebooks/01_eda.ipynb`)
   - Understand data structure
   - Identify interesting plays
   - Initial visualization prototypes

2. **Feature Engineering** (`notebooks/02_features.ipynb`)
   - Calculate ball trajectory
   - Compute player separation metrics
   - Identify coverage types

3. **Visualization Development** (`notebooks/03_visualization.ipynb`)
   - Create static visualizations
   - Develop animation prototypes
   - Refine visual design

4. **Animation Production** (`src/animation/`)
   - Generate final animations
   - Add annotations and storytelling elements
   - Export to video format

## Key Insights to Visualize

- **Pre-snap vs Post-snap**: How does player positioning change once the ball is snapped?
- **Route Development**: How do routes evolve while the ball is in flight?
- **Coverage Breakdown**: When and how does coverage break down?
- **Optimal Throw Points**: Visualize the ideal moment to release the ball
- **Separation Creation**: Show how receivers create separation from defenders

## Submission Guidelines

From NFL guidelines:
- Answer the specific prompt (player movement with ball in air)
- Ensure figures/charts are properly sized and readable
- Don't wildly overstate capabilities
- Clearly state limitations
- Focus on quality over quantity

## License

MIT License - See [LICENSE](LICENSE) for details

## Author

Brian Worthington

## Resources

- [NFL Big Data Bowl 2026 - Analytics](https://www.kaggle.com/competitions/nfl-big-data-bowl-2026-analytics)
- [NFL Operations - Big Data Bowl](https://operations.nfl.com/gameday/analytics/big-data-bowl/)
- [Past Winners and Submissions](https://operations.nfl.com/gameday/analytics/big-data-bowl/)
