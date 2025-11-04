# CS2 Demo Analyzer - Project Scratchpad

## Background and Motivation

This project aims to analyze Counter-Strike 2 (CS2) demo files to extract general team tendencies and patterns. The analyzer will process multiple matches (typically 3-20, average ~5) from the same team playing on the same map, focusing on aggregated statistical analysis rather than granular player-level micro-tendencies.

**Core Objectives:**
- Identify team-wide strategic patterns and preferences
- Analyze both T-side and CT-side tendencies
- Extract utility usage patterns
- Provide actionable insights through simple, interpretable metrics
- Keep implementation simple and maintainable using statistical aggregation with light ML (clustering)

**Technology Stack:**
- Python (primary language)
- awpy (CS2 demo parsing)
- pandas, numpy (data handling)
- scikit-learn (clustering for utility spots)
- matplotlib (visualizations)

## Key Challenges and Analysis

1. **Demo Parsing Complexity**: Understanding awpy's data structure and extracting relevant events (rounds, grenades, positions, kills)
2. **Team Filtering**: Correctly identifying which side the target team is playing (T/CT) and filtering all data accordingly
3. **Map Coordinate Systems**: Different maps have different coordinate systems - need to handle map-specific zone definitions for stacks/pushes
4. **Pistol Round Detection**: Accurately identifying pistol rounds (rounds 1, 13, or low economy rounds)
5. **Event Timing**: Converting game ticks to seconds for meaningful timing analysis
6. **Data Aggregation**: Combining data from multiple demos while maintaining context (match, round number, side)
7. **CT Push Detection**: Defining what constitutes a "push" and detecting when players cross into T-controlled areas
8. **Site Stack Detection**: Defining site zones and identifying when 3+ players are in the same site area at round start

**Additional Feasible Features (Low Complexity):**
- Round win rate by bombsite hit (correlate strategy with success)
- Economy patterns (buy rounds vs eco/force buy rounds)
- Round duration patterns (average time to plant/defuse)
- Utility usage frequency by grenade type (simple counting)
- Entry fragger patterns (who gets first kill on T-side)
- Success rate of different bombsite hits

## High-level Task Breakdown

### Phase 1: Project Setup and Demo Parsing Foundation
**Status**: Not Started

**Task 1.1: Verify Environment Setup**
- Verify Python installation and virtual environment
- Confirm all required libraries are installed (awpy, pandas, numpy, scikit-learn, matplotlib)
- Test basic imports and library availability
- **Success Criteria**: All imports work without errors, pip list shows all required packages

**Task 1.2: Create Project Structure**
- Set up folder structure (e.g., `demos/` for input, `output/` for reports, `src/` for code)
- Create `requirements.txt` with pinned versions
- Add basic README with usage instructions
- **Success Criteria**: Clear project structure, requirements.txt exists, README updated

**Task 1.3: Basic Demo Parsing Test**
- Download or obtain a test CS2 demo file (.dem)
- Write basic script to parse a single demo using awpy
- Extract and print basic match info (teams, map, rounds)
- Handle parsing errors gracefully
- **Success Criteria**: Successfully parse a demo, print match metadata without errors

---

### Phase 2: Core Data Extraction
**Status**: Not Started

**Task 2.1: Round Data Extraction**
- Extract round-level data: round number, winner, bombsite (if planted), side (T/CT)
- Identify pistol rounds (rounds 1, 13, or economy-based detection)
- Filter for target team's rounds only
- Store in structured format (DataFrame)
- **Success Criteria**: Can extract all rounds for target team, correctly identify T/CT sides, detect pistol rounds

**Task 2.2: Utility (Grenade) Data Extraction**
- Extract all grenade events: type (smoke, flash, molotov, HE), landing coordinates (X/Y/Z), thrower team
- Filter for target team's utility only
- Extract timing information (round, tick, seconds into round)
- Store in DataFrame format
- **Success Criteria**: Extract all utility events for target team with correct coordinates and timing

**Task 2.3: Player Position Data Extraction**
- Extract player positions at key moments (round start/freeze end, mid-round samples)
- Filter for target team's players only
- Include tick/second timing information
- Handle different round phases
- **Success Criteria**: Can extract player positions at round start and throughout rounds for target team

**Task 2.4: Kill/Death Event Extraction**
- Extract kill events: attacker, victim, weapon, time, location
- Identify entry frags (first kill of round)
- Calculate round timing context
- **Success Criteria**: Extract all kill events with proper context for target team

---

### Phase 3: Batch Processing Multiple Demos
**Status**: Not Started

**Task 3.1: Multi-Demo Parser**
- Create function to process folder of .dem files
- Ensure all demos are from the same map (validation)
- Ensure all demos include the target team (validation)
- Combine data from multiple demos while preserving match context
- Handle parsing errors per demo (continue processing others)
- **Success Criteria**: Process multiple demos, aggregate data correctly, handle errors gracefully, validate map/team consistency

**Task 3.2: Data Consolidation**
- Merge round data from all demos
- Merge utility data from all demos
- Merge position data from all demos
- Add match identifier to maintain traceability
- **Success Criteria**: Single consolidated dataset with data from all processed demos

---

### Phase 4: T-Side Analysis Features
**Status**: Not Started

**Task 4.1: Bombsite Hit Analysis**
- Count bombsite plants per site (A vs B)
- Calculate percentage distribution
- Calculate win rate per bombsite
- Identify most frequently hit bombsite
- **Success Criteria**: Generate statistics showing bombsite preference and success rate

**Task 4.2: Pistol Round Behavior Analysis**
- Filter pistol rounds on T-side
- Analyze bombsite hits on pistol rounds
- Analyze utility usage on pistol rounds (if any)
- Identify pistol round patterns (rush vs execute vs split)
- Compare pistol vs non-pistol bombsite preferences
- **Success Criteria**: Generate statistics on pistol round tendencies and comparison with regular rounds

**Task 4.3: Entry Fragger Analysis**
- Identify first kill in each T-side round
- Count entry frags per player
- Calculate entry frag success rate (did round win after entry?)
- Identify primary entry fragger
- **Success Criteria**: Statistics on entry frag patterns and player roles

---

### Phase 5: CT-Side Analysis Features
**Status**: Not Started

**Task 5.1: Site Stack Detection**
- Define site zones using map coordinates (A-site and B-site bounding boxes)
- Count players per site at round start (freeze end)
- Identify stacks (3+ players in same site)
- Calculate stack frequency per site
- Identify most stacked site
- **Success Criteria**: Generate statistics on CT stacking patterns

**Task 5.2: CT Push Detection and Analysis**
- Define map zones (mid, long, connector areas) - may need map-specific definitions
- Detect when CT players cross into T-controlled areas
- Extract push timing (seconds into round)
- Group pushes by location
- Calculate average push timings per location
- Count push frequency per location
- **Success Criteria**: Generate statistics on CT push locations and timings

---

### Phase 6: Utility Analysis Features
**Status**: Not Started

**Task 6.1: Utility Landing Spot Clustering**
- For each grenade type (smoke, flash, molotov, HE):
  - Extract landing coordinates
  - Apply DBSCAN clustering to identify hotspots
  - Rank clusters by frequency
  - Identify top 3-5 most common landing spots per grenade type
- **Success Criteria**: Identify clustered utility landing spots with frequency rankings

**Task 6.2: Utility Usage Frequency**
- Count total utility usage per grenade type
- Calculate utility usage per round
- Compare utility usage T-side vs CT-side
- Analyze utility timing (early vs late round)
- **Success Criteria**: Generate statistics on utility usage patterns

---

### Phase 7: Additional Analysis Features
**Status**: Not Started

**Task 7.1: Economy Pattern Analysis**
- Detect buy rounds vs eco rounds vs force buys (based on equipment value)
- Calculate win rate per economy type
- Identify economy patterns (when do they force, when do they save)
- **Success Criteria**: Generate statistics on economy management patterns

**Task 7.2: Round Timing Analysis**
- Calculate average round duration
- Calculate time to bombsite control (T-side)
- Calculate time to site entry (T-side)
- Calculate time to rotate (CT-side)
- **Success Criteria**: Generate statistics on round timing patterns

**Task 7.3: Strategy Success Correlation**
- Correlate bombsite hits with round wins
- Identify which strategies are most successful
- Compare success rates across different approaches
- **Success Criteria**: Generate insights on which strategies work best for the team

---

### Phase 8: Visualization and Reporting
**Status**: Not Started

**Task 8.1: Create Visualization Functions**
- Create heatmap function for utility landing spots (scatter plot with clustering colors)
- Create bar charts for bombsite hit frequencies
- Create timeline visualizations for round events
- Create comparison charts (pistol vs non-pistol, T vs CT utility)
- **Success Criteria**: Functional visualization functions that produce clear, readable plots

**Task 8.2: Generate Analysis Report**
- Create structured text report with all findings
- Include statistics and percentages
- Include visualizations
- Format output as markdown or HTML
- Save to output folder
- **Success Criteria**: Comprehensive report file generated with all analysis results

---

### Phase 9: Testing and Refinement
**Status**: Not Started

**Task 9.1: End-to-End Testing**
- Test with real demo files (3-5 demos from same team/map)
- Verify all metrics are calculated correctly
- Check for edge cases (missing data, incomplete rounds)
- Validate against known patterns if possible
- **Success Criteria**: Successfully process real demo set and generate accurate report

**Task 9.2: Error Handling and Edge Cases**
- Handle missing demo files gracefully
- Handle demos with different map (skip with warning)
- Handle demos without target team (skip with warning)
- Handle incomplete round data
- Add informative error messages
- **Success Criteria**: Robust error handling, no crashes on edge cases

**Task 9.3: Code Cleanup and Documentation**
- Add docstrings to all functions
- Add type hints where helpful
- Refactor duplicated code
- Add comments for complex logic
- **Success Criteria**: Clean, well-documented codebase

---

## Project Status Board

- [x] **Phase 1**: Project Setup and Demo Parsing Foundation
  - [x] Task 1.1: Verify Environment Setup
  - [x] Task 1.2: Create Project Structure
  - [x] Task 1.3: Basic Demo Parsing Test
- [x] **Phase 2**: Core Data Extraction
  - [x] Task 2.1: Round Data Extraction
  - [x] Task 2.2: Utility (Grenade) Data Extraction
  - [x] Task 2.3: Player Position Data Extraction
  - [x] Task 2.4: Kill/Death Event Extraction
- [x] **Phase 3**: Batch Processing Multiple Demos
  - [x] Task 3.1: Multi-Demo Parser
  - [x] Task 3.2: Data Consolidation
- [ ] **Phase 4**: T-Side Analysis Features
  - [ ] Task 4.1: Bombsite Hit Analysis
  - [ ] Task 4.2: Pistol Round Behavior Analysis
  - [ ] Task 4.3: Entry Fragger Analysis
- [ ] **Phase 5**: CT-Side Analysis Features
  - [ ] Task 5.1: Site Stack Detection
  - [ ] Task 5.2: CT Push Detection and Analysis
- [ ] **Phase 6**: Utility Analysis Features
  - [ ] Task 6.1: Utility Landing Spot Clustering
  - [ ] Task 6.2: Utility Usage Frequency
- [ ] **Phase 7**: Additional Analysis Features
  - [ ] Task 7.1: Economy Pattern Analysis
  - [ ] Task 7.2: Round Timing Analysis
  - [ ] Task 7.3: Strategy Success Correlation
- [ ] **Phase 9**: Testing and Refinement
  - [ ] Task 9.1: End-to-End Testing
  - [ ] Task 9.2: Error Handling and Edge Cases
  - [ ] Task 9.3: Code Cleanup and Documentation

## Current Status / Progress Tracking

**Current Phase**: Code Refactoring - Improving Code Organization and Structure

**Latest Activity**: Starting refactoring to improve code organization - splitting large files into more manageable, compartmentalized modules.

**Completed Tasks**:
- ✓ Task 1.1: Environment verified - Python 3.11.9 installed, virtual environment active, all required packages (awpy 2.0.2, pandas 2.3.3, numpy 2.3.4, scikit-learn 1.7.2, matplotlib 3.10.7) installed
- ✓ Task 1.2: Project structure created - demos/ and output/ folders exist, requirements.txt and README.md in place
- ✓ Task 1.3: Basic demo parsing script created and tested - analyzer.py successfully parses demo structure, handles missing files gracefully
- ✓ Task 2.1: Round data extraction implemented - using `demo.rounds` property, extracts round_num, winner, bombsite (readable names), pistol round detection, reason
- ✓ Task 2.2: Utility data extraction implemented - extracts all grenade types with landing coordinates, thrower info, round/timing data
- ✓ Task 2.3: Player position extraction implemented - extracts positions at round_start, freeze_end, and optional mid-round samples
- ✓ Task 2.4: Kill event extraction implemented - extracts all kills with attacker/victim, weapon, location, timing, entry frag detection
- ✓ Task 3.1: Multi-Demo Parser implemented - `process_demos_batch()` function in `src/batch.py`, parallel processing with ProcessPoolExecutor, map validation, team validation, error handling per demo
- ✓ Task 3.2: Data Consolidation implemented - `consolidate_data()` function merges DataFrames from all demos, preserves match context via `match_file` column, returns consolidated datasets with summary statistics

**Refactoring Status**: COMPLETE ✓
- Successfully split `src/extractors.py` (670 lines) into compartmentalized modules
- Successfully split `tests/test_all.py` into separate test files
- All existing imports work (backwards compatible via `__init__.py`)
- All tests pass after refactoring

**Next Steps After Refactoring**: 
Ready to proceed to Phase 4: T-Side Analysis Features (Task 4.1 - Bombsite Hit Analysis)

## Refactoring Plan

### Goal
Refactor codebase to have better compartmentalization without being overly spread out:
1. Split `src/extractors.py` (670 lines) into logical modules
2. Split `tests/test_all.py` into separate test files
3. Maintain backwards compatibility with existing imports
4. Ensure all functionality remains intact

### Structure Changes

**Extractors Refactoring:**
- Create `src/extractors/` directory
- Split into 4 focused modules:
  - `src/extractors/rounds.py` - Round data extraction
  - `src/extractors/utility.py` - Utility/grenade data extraction
  - `src/extractors/positions.py` - Player position extraction
  - `src/extractors/kills.py` - Kill event extraction
- Create `src/extractors/__init__.py` to maintain backwards compatibility (re-export all functions)

**Tests Refactoring:**
- Split `tests/test_all.py` into:
  - `tests/test_team_identification.py` - Team identification tests
  - `tests/test_side_determination.py` - Side determination tests
  - `tests/test_batch_processing.py` - Batch processing tests
  - `tests/test_bombsite_analysis.py` - Bombsite analysis tests
- Keep `tests/test_all.py` as a test runner that imports and runs all tests (optional convenience)

**Success Criteria:**
- All existing imports continue to work (backwards compatible)
- Code is better organized with clear separation of concerns
- Each module has a single, clear responsibility
- All tests pass after refactoring
- No functionality is lost

## Executor's Feedback or Assistance Requests

**Refactoring Completion Report (Executor)**:
- **Extractors Refactoring**: Split `src/extractors.py` (670 lines) into 4 focused modules:
  - `src/extractors/rounds.py` - Round data extraction (156 lines)
  - `src/extractors/utility.py` - Utility/grenade data extraction (148 lines)
  - `src/extractors/positions.py` - Player position extraction (206 lines)
  - `src/extractors/kills.py` - Kill event extraction (131 lines)
  - `src/extractors/__init__.py` - Maintains backwards compatibility by re-exporting all functions
- **Tests Refactoring**: Split `tests/test_all.py` into 4 separate test files:
  - `tests/test_team_identification.py` - Team identification tests
  - `tests/test_side_determination.py` - Side determination tests
  - `tests/test_batch_processing.py` - Batch processing tests
  - `tests/test_bombsite_analysis.py` - Bombsite analysis tests
  - Updated `tests/test_all.py` to import and run all tests (acts as test runner)
- **Backwards Compatibility**: All existing imports continue to work via `__init__.py` re-exports
- **Verification**: All tests pass successfully after refactoring
- **Old File Cleanup**: Removed old `src/extractors.py` file after verifying new structure works
- **Benefits**: Better code organization, clearer separation of concerns, easier to maintain and extend

**Task 1.1-1.3 Completion Report (Executor)**:
- All Phase 1 tasks completed successfully
- Fixed import issue in analyzer.py: removed incorrect `from awpy.parser import DemoParser` import (awpy 2.0.2 only needs `from awpy import Demo`)
- Script tested and runs successfully, handles missing demo files gracefully

**Task 2.1 Completion Report (Executor)**:
- Round data extraction function `extract_round_data()` implemented and simplified
- **Updated to use awpy Demo.rounds property** (per https://awpy.readthedocs.io/en/latest/examples/parse_demo.html#)
- Successfully extracts: round number, winner, bombsite (readable names like 'bombsite_b'), pistol round detection, reason
- Much simpler implementation - awpy already processes round data including bomb_site information
- Returns pandas DataFrame with all round data
- **Note**: Side determination (T/CT) for target team requires target_team parameter - currently returns None for side column. Team filtering will be enhanced when target_team is provided in future tasks.
- Tested successfully: extracted 24 rounds with proper bombsite names (not numeric IDs)

**Task 2.2 Completion Report (Executor)**:
- Utility data extraction function `extract_utility_data()` implemented
- Extracts all grenade types: smoke, flash, molotov, HE
- Uses grenade detonation events: `smokegrenade_detonate`, `flashbang_detonate`, `hegrenade_detonate`, `inferno_startburn`
- Extracts: landing coordinates (x, y, z), thrower name/side, round number, tick, seconds into round
- Matches grenades to rounds using tick ranges
- Calculates seconds into round using CS2 tick rate (64 ticks/second)
- Returns pandas DataFrame with all utility data
- Tested successfully: extracted 324 utility events (102 smoke, 80 flash, 80 HE, 62 molotov), all with coordinates

**Task 2.3 Completion Report (Executor)**:
- Player position extraction function `extract_player_positions()` implemented
- Extracts positions at key moments: round_start, freeze_end, and optional mid-round samples
- Uses `demo.ticks` property with position properties (X, Y, Z)
- Supports optional `sample_interval` parameter (in seconds) for mid-round sampling
- Extracts: player name, side, round number, coordinates, tick, seconds into round, phase
- Matches positions to rounds using tick ranges
- Calculates seconds into round using CS2 tick rate (64 ticks/second)
- Returns pandas DataFrame with all position data
- Tested successfully: extracted 2120 position records (230 round_start, 240 freeze_end, 1650 mid_round with 10s sampling), all with coordinates, 10 unique players

**Task 2.4 Completion Report (Executor)**:
- Kill event extraction function `extract_kill_events()` implemented
- Extracts all kill events using `demo.kills` property
- Extracts: attacker name/side, victim name/side, weapon, round number, tick, seconds into round (integer), time_into_round (MM:SS format), attacker position (x, y, z), headshot status
- Identifies entry frags (first kill of each round) - one per round correctly detected
- Calculates time into round using CS2 tick rate (64 ticks/second), formatted as MM:SS (e.g., "1:10" for 70 seconds)
- Returns pandas DataFrame with all kill event data
- Tested successfully: extracted 174 kill events, 24 entry frags (one per round with kills), 85 headshots (48.9%), 173 with coordinates

**Fixes Applied (Post Task 2.4)**:
- Entry frag detection: Fixed to correctly identify first kill per round (was incorrectly using index comparison)
- Time formatting: Changed from decimal seconds to MM:SS format (e.g., "0:40", "1:18") across all extractors
- Pistol rounds: Updated from CSGO format (rounds 1, 16) to CS2 format (rounds 1, 14)
- Side column: Added documentation explaining it requires team mapping (will be populated when target_team is provided)

**Status**: Task 2.4 complete. Phase 2 (Core Data Extraction) is now complete! Ready to proceed to Phase 3 (Batch Processing Multiple Demos) or await user verification

**Task 3.1-3.2 Completion Report (Executor)**:
- Batch processing function `process_demos_batch()` implemented in `src/batch.py`
- Parallel processing using `ProcessPoolExecutor` for better Windows compatibility
- Map validation: Ensures all demos are from the same map (configurable via `validate_map` parameter)
- Team validation: Can validate that target team exists in all demos (configurable via `validate_team` parameter)
- Error handling: Gracefully handles parsing errors per demo, continues processing others
- Data consolidation: `consolidate_data()` function merges DataFrames from all demos
- Match context: Preserves demo file name in `match_file` column for traceability
- Summary statistics: Returns summary with processed demo count, total rounds, events, errors
- **Memory Optimization**: Refactored to parse each demo only once (was parsing 5 times per demo), reduced default workers to 2, added explicit memory cleanup with `del demo` and `gc.collect()`
- Tested successfully: Processed 3 demos (71 rounds, 1498 utility events, 502 kills, 1459 positions) with efficient resource usage

**Code Refactoring (Post Task 2.2)**:
- Refactored codebase into modular structure:
  - `src/parsers.py` - Basic demo parsing utilities
  - `src/extractors.py` - Data extraction functions (rounds, utility, future: positions, kills)
  - `analyzer.py` - Simplified main entry point (now ~70 lines vs 383 lines)
- Benefits: Better organization, easier to maintain, scalable for future features
- All functionality tested and working after refactor

## Lessons

*(This section will capture important learnings, fixes, and reusable information)*

### Key Notes:
- Match count is arbitrary (3-20 matches, average ~5)
- Focus on general tendencies, not hyper-granular micro-analysis
- Keep implementation simple - statistical aggregation with light ML (clustering)
- All analysis must be filtered for target team only
- All demos must be from the same map
- Use pandas DataFrames for data handling
- DBSCAN clustering for utility spot detection
- Map-specific coordinate systems will need handling

### Implementation Lessons:
- **awpy 2.0.2 Import**: Only import `from awpy import Demo`. The `awpy.parser.DemoParser` module doesn't exist in this version. The `Demo` class handles parsing directly.
- **Virtual Environment**: Always activate the virtual environment (`.\.venv\Scripts\Activate.ps1` on Windows PowerShell) before running scripts or installing packages
- **Python Version**: Confirmed working with Python 3.11.9 on Windows
  - **awpy API Structure**:
  - Map name: Use `demo.parse_header()` then access `demo.header['map_name']`
  - Events: `demo.events` is a dictionary where values are **Polars DataFrames**, not lists or pandas DataFrames
  - Round count: Count rows in `demo.events['round_end']` DataFrame using `.shape[0]`
  - Parse order: Call `demo.parse_header()` first for metadata, then `demo.parse()` for full event data
  - Convert Polars to pandas: Use `.to_pandas()` method on Polars DataFrames
  - **Use Demo properties directly**: `demo.rounds`, `demo.grenades`, `demo.kills`, `demo.ticks` are pre-processed Polars DataFrames (see https://awpy.readthedocs.io/en/latest/examples/parse_demo.html#)
  - `demo.rounds` already contains: round_num, winner, bomb_site (readable names like 'bombsite_b'), reason, bomb_plant tick, start, freeze_end, end
  - `demo.grenades` has: thrower, grenade_type, tick, X, Y, Z (but landing coords may be NaN - use events instead)
  - `demo.kills` has: attacker_name, victim_name, weapon, tick, round_num, attacker_X/Y/Z, headshot, etc.
  - `demo.ticks` has: player positions (X, Y, Z), name, side, round_num, tick (requires `player_props=['X', 'Y', 'Z']` in parse())
  - Grenade landing coordinates: Use `demo.events['smokegrenade_detonate']`, `demo.events['flashbang_detonate']`, `demo.events['hegrenade_detonate']`, `demo.events['inferno_startburn']` - these have `x`, `y`, `z` columns for landing positions
  - Round tick matching: Use `round_start` ticks to create boundaries (round N spans from round N start tick to round N+1 start tick)
  - Entry frag detection: Sort kills by round_num and tick, reset index, use set to track first kill per round
  - Time formatting: Convert seconds to MM:SS format (e.g., 70 seconds = "1:10"), keep integer seconds_into_round for calculations
  - CS2 format: Pistol rounds are rounds 1 and 14 (first to 13 wins), not 1 and 16 like CSGO
- **Windows Console Encoding**: Avoid Unicode characters like ✓/✗ in print statements - use ASCII-safe alternatives like [SUCCESS]/[ERROR]
- **Memory Optimization for Batch Processing**: Each demo was being parsed 5 times (basic info + 4 extractors), causing 100% CPU/RAM usage. Solution: Parse demo once per worker and pass Demo object to all extractors. Also limit max_workers to 2 by default to reduce memory pressure. Use explicit `del demo` and `gc.collect()` for cleanup.
- **Multiprocessing on Windows**: Must use `if __name__ == '__main__':` guard and `ProcessPoolExecutor` from `concurrent.futures` for better Windows compatibility (avoids RuntimeError with spawn method).

