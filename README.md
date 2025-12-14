# CS2 Demo Analyzer

A Python tool for analyzing Counter-Strike 2 (CS2) demo files to generate comprehensive team scouting reports with strategic patterns and tendencies.

## Features

- **Team Identification**: Automatically identifies the common team across multiple demo files
- **Map-Specific Analysis**: Generates separate scouting reports for each map
- **T-Side Analysis**: 
  - Bombsite preferences and win rates per site
  - Plant rate and post-plant success
  - Entry fragging patterns
  - Utility usage breakdown
- **CT-Side Analysis**: 
  - Round win rates and defensive success
  - Retake success rates
  - CT aggression (entry frags on defense)
  - Utility usage patterns
- **Comprehensive Reporting**: Generates text reports, JSON data, and CSV exports

## Requirements

- Python 3.11+
- Virtual environment (recommended)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd cs2-demo-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Organizing Demo Files

Organize your demo files by map in the `demos/` folder:

```
demos/
  inferno/
    match1.dem
    match2.dem
  nuke/
    match1.dem
    match2.dem
  ancient/
    match1.dem
```

**Important**: All demos in a map folder should contain matches with the same team. The analyzer will identify the common team across all demos in each folder.

### Running the Analyzer

```bash
python analyzer.py
```

The analyzer will:
1. Identify the common team across all demos in each map folder
2. Parse all demo files and extract relevant data
3. Analyze team tendencies on both T-side and CT-side
4. Generate comprehensive scouting reports in the `output/` folder

### Output Files

For each map, the analyzer generates:

- **Text Report** (`{map}_scouting_report_{timestamp}.txt`): Human-readable scouting report with:
  - Team roster
  - T-side statistics (win rate, bombsite preferences, utility usage)
  - CT-side statistics (retake success, defensive patterns)
  - Overall match statistics

- **JSON Data** (`{map}_data_{timestamp}.json`): Machine-readable data for further analysis

- **CSV Files** (`{map}_csv_{timestamp}/`): Raw data exports
  - `rounds.csv`: Round-by-round results with side information
  - `kills.csv`: All kill events with entry frag tracking
  - `utility.csv`: All utility usage events
  - `positions.csv`: Player position samples throughout matches

## Project Structure

```
cs2-demo-analyzer/
├── analyzer.py              # Main entry point - runs the analysis pipeline
├── requirements.txt         # Python dependencies
├── README.md               # This file
│
├── src/                    # Core modules
│   ├── analyzers/         # Analysis modules
│   │   ├── __init__.py    # Package exports
│   │   ├── t_side.py      # T-side tendency analysis (bombsites, plants, wins)
│   │   ├── ct_side.py     # CT-side tendency analysis (retakes, defense)
│   │   └── reports.py     # Report generation (text, JSON, CSV)
│   │
│   ├── extractors/        # Data extraction
│   │   ├── rounds.py      # Round data with side tracking
│   │   ├── kills.py       # Kill events and entry frags
│   │   ├── utility.py     # Utility usage events
│   │   └── positions.py   # Player position tracking
│   │
│   ├── parsers.py         # Demo file parsing
│   ├── team_identification.py  # Team detection across demos
│   └── batch.py           # Batch processing utilities
│
├── demos/                  # Demo files organized by map
│   ├── inferno/
│   ├── nuke/
│   └── ancient/
│
├── output/                 # Generated reports
│   ├── *_report_*.txt     # Text scouting reports
│   ├── *_data_*.json      # JSON data exports
│   └── *_csv_*/           # CSV data folders
│
└── tests/                  # Test files
    └── test_*.py
```

### Module Responsibilities

**`analyzer.py`** - Main entry point
- Scans demo folders and identifies teams
- Orchestrates the analysis pipeline
- Generates reports in multiple formats

**`src/analyzers/`** - Analysis functions (separated by purpose)
- `t_side.py`: Analyzes T-side gameplay (bombsite preferences, plant success)
- `ct_side.py`: Analyzes CT-side gameplay (retakes, defensive success)
- `reports.py`: Generates text, JSON, and CSV reports

**`src/extractors/`** - Data extraction from demos
- `rounds.py`: Extracts round outcomes with side tracking
- `kills.py`: Extracts kill events with entry frag detection
- `utility.py`: Extracts grenade usage events
- `positions.py`: Samples player positions during gameplay

**`src/team_identification.py`** - Team detection
- Identifies teams that appear across multiple demos
- Uses tick data to group players by side
- Supports multiple teams per map folder

## Code Organization

The project follows a modular design pattern:

1. **Data Extraction**: `src/extractors/` modules parse demo files and extract specific data types
2. **Team Identification**: `src/team_identification.py` groups players into teams across demos
3. **Analysis**: `analyzers/` modules analyze extracted data and compute statistics
4. **Report Generation**: `analyzers/reports.py` formats results into multiple output formats
5. **Orchestration**: `analyzer.py` coordinates the entire pipeline

This separation makes it easy to:
- Add new analysis types (create a new file in `src/analyzers/`)
- Modify report formats (edit `src/analyzers/reports.py`)
- Extract additional data (add modules to `src/extractors/`)

## Example Output

### T-Side Analysis
```
T-SIDE ANALYSIS
Total T-Side Rounds: 24
Record: 12W - 12L
Win Rate: 50.0%

Bomb Plants: 12
Plant Rate: 50.0%

Bombsite Preferences:
Site                 Plants     % of Plants     Wins       Win Rate
bombsite_b           9            75.0%         7            77.8%
bombsite_a           3            25.0%         3           100.0%
```

### CT-Side Analysis
```
CT-SIDE ANALYSIS
Total CT-Side Rounds: 15
Record: 11W - 4L
Win Rate: 73.3%

Rounds with Bomb Plant: 9
Successful Retakes: 7
Overall Retake Success Rate: 77.8%

Retake Success by Bombsite:
Site                 Plants Against       Retakes Won          Success Rate
bombsite_a           7                    6                      85.7%
bombsite_b           2                    1                      50.0%
```

## Development

### Adding New Analysis Types

To add a new analysis module:

1. Create a new file in `src/analyzers/` (e.g., `src/analyzers/economy.py`)
2. Implement analysis function(s) that accept DataFrames and return dictionaries
3. Export function in `src/analyzers/__init__.py`
4. Import and call in `analyzer.py`
5. Add results to report in `src/analyzers/reports.py`

Example:
```python
# src/analyzers/economy.py
def analyze_economy(rounds_df, kills_df):
    """Analyze economy management patterns."""
    # Your analysis logic
    return {
        'eco_rounds': ...,
        'force_buys': ...,
        'full_buys': ...
    }
```

### Running Tests

```bash
python -m pytest tests/
```

## Credits

This project uses the [awpy](https://github.com/pnxenopoulos/awpy) library for parsing CS2 demo files.

## License

MIT License - see LICENSE file for details.

cs2-demo-analyzer/
├── demos/          # Input demo files (.dem)
├── output/         # Generated analysis reports
├── src/            # Source modules
│   ├── __init__.py
│   ├── parsers.py           # Basic demo parsing utilities
│   ├── extractors.py        # Data extraction functions (rounds, utility, positions, kills)
│   ├── batch.py              # Batch processing multiple demos
│   ├── team_identification.py # Team identification and side determination
│   └── analysis.py           # Analysis functions (bombsite hits, etc.)
├── tests/          # Test suite
│   ├── __init__.py
│   └── test_all.py          # Comprehensive test suite
├── analyzer.py     # Main entry point
├── requirements.txt
└── README.md
```

## Testing

Run the test suite:
```bash
python -m tests.test_all
```

## Notes

- All demos must be from the same map
- All demos must include the target team
- Typically processes 3-20 matches (average ~5)
