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
