# CS2 Demo Analyzer

A Python tool for analyzing Counter-Strike 2 (CS2) demo files to extract team tendencies and strategic patterns.

## Features

- **T-Side Analysis**: Bombsite preferences, pistol round behaviors, entry fragger patterns
- **CT-Side Analysis**: Site stacking patterns, push locations and timings
- **Utility Analysis**: Landing spot clustering for smokes, flashes, molotovs, and HE grenades
- **Strategic Insights**: Economy patterns, round timing, and strategy success correlation

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

*(Usage instructions will be updated as development progresses)*

1. Place your CS2 demo files (.dem) in the `demos/` folder
2. Run the analyzer:
```bash
python analyzer.py
```

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
