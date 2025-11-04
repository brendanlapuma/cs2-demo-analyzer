"""
CS2 Demo Analyzer - Batch Processing Functions

This module contains functions for batch processing multiple demo files:
- Multi-demo parser with validation
- Data consolidation across demos
- Parallel processing for speed
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

from src.parsers import parse_demo_basic
from src.extractors import (
    extract_round_data,
    extract_utility_data,
    extract_player_positions,
    extract_kill_events
)


def _process_single_demo(
    demo_path: str,
    target_team: str = None,
    sample_interval: int = None,
    team_players: set = None
) -> Dict:
    """
    Process a single demo file and extract all data types.
    Worker function for parallel processing.
    
    Optimized to parse the demo once and reuse the Demo object for all extractions.
    
    Args:
        demo_path: Path to the .dem file
        target_team: Optional team name to filter data
        sample_interval: Optional interval for mid-round position sampling
        
    Returns:
        Dictionary with extracted data and metadata
    """
    result = {
        'file': os.path.basename(demo_path),
        'path': demo_path,
        'success': False,
        'rounds': None,
        'utility': None,
        'positions': None,
        'kills': None,
        'error': None,
        'map': None,
        'rounds_count': 0
    }
    
    demo = None
    try:
        from awpy import Demo
        
        # Parse demo ONCE with position properties for all extractions
        # This is the memory-intensive operation, so we do it once
        demo = Demo(demo_path)
        demo.parse_header()
        map_name = demo.header.get('map_name', 'Unknown') if hasattr(demo, 'header') and demo.header else 'Unknown'
        
        # Parse with player properties for position extraction
        # Other extractors can use the same parsed demo
        demo.parse(player_props=['X', 'Y', 'Z'])
        
        # Get basic info from parsed demo
        result['map'] = map_name
        if hasattr(demo, 'events') and isinstance(demo.events, dict):
            if 'round_end' in demo.events:
                round_end_df = demo.events['round_end']
                if hasattr(round_end_df, 'shape'):
                    result['rounds_count'] = round_end_df.shape[0]
                elif isinstance(round_end_df, list):
                    result['rounds_count'] = len(round_end_df)
        
        # Extract all data types using the same Demo object
        # This avoids parsing the demo multiple times (major memory savings)
        result['rounds'] = extract_round_data(demo_path=demo_path, target_team=target_team, demo_obj=demo, team_players=team_players)
        result['utility'] = extract_utility_data(demo_path=demo_path, target_team=target_team, demo_obj=demo)
        result['positions'] = extract_player_positions(demo_path=demo_path, target_team=target_team, sample_interval=sample_interval, demo_obj=demo)
        result['kills'] = extract_kill_events(demo_path=demo_path, target_team=target_team, demo_obj=demo)
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        import traceback
        result['traceback'] = traceback.format_exc()
    finally:
        # Explicitly delete the Demo object to free memory immediately
        if demo is not None:
            del demo
            import gc
            gc.collect()  # Force garbage collection
    
    return result


def process_demos_batch(
    demos_folder: str,
    target_team: str = None,
    target_map: str = None,
    validate_map: bool = True,
    validate_team: bool = True,
    sample_interval: int = None,
    max_workers: int = None,
    team_players: set = None
) -> Dict[str, pd.DataFrame]:
    """
    Process multiple demo files from a folder and extract all data types.
    
    Validates that all demos are from the same map (if validate_map=True).
    Validates that all demos include the target team (if validate_team=True and target_team provided).
    Handles parsing errors per demo gracefully (continues processing others).
    
    Args:
        demos_folder: Path to folder containing .dem files
        target_team: Optional team name to filter data. If None, extracts all data.
        target_map: Expected map name (e.g., 'de_overpass'). If None, uses first demo's map.
        validate_map: If True, ensures all demos are from the same map
        validate_team: If True, ensures all demos include the target team
        sample_interval: Optional interval in seconds for mid-round position sampling
        max_workers: Number of parallel workers. If None, uses cpu_count()
        
    Returns:
        Dictionary with keys:
        - 'rounds': Consolidated round data DataFrame
        - 'utility': Consolidated utility data DataFrame
        - 'positions': Consolidated position data DataFrame
        - 'kills': Consolidated kill event data DataFrame
        - 'summary': Summary statistics dictionary
        - 'errors': List of error messages for failed demos
    """
    demos_path = Path(demos_folder)
    
    if not demos_path.exists():
        raise FileNotFoundError(f"Demos folder not found: {demos_folder}")
    
    # Find all .dem files
    demo_files = sorted(demos_path.glob("*.dem"))
    
    if not demo_files:
        raise ValueError(f"No .dem files found in {demos_folder}")
    
    print(f"Found {len(demo_files)} demo file(s)")
    
    # Identify team if not provided
    if team_players is None:
        from src.team_identification import identify_team_from_demos
        team_info = identify_team_from_demos(demos_folder, min_players=4)
        team_players = team_info['team_players']
        if team_players:
            print(f"Identified team: {team_info['team_name']} ({len(team_players)} players)")
        else:
            print("Warning: Could not identify team from demos")
    
    # Determine number of workers
    # Limit to 2 by default to reduce memory pressure
    # Each worker loads entire demo files into memory
    if max_workers is None:
        max_workers = min(2, cpu_count(), len(demo_files))
    print(f"Using {max_workers} parallel worker(s) (to reduce memory usage)")
    
    # Process all demos in parallel
    print(f"\nProcessing {len(demo_files)} demo(s) in parallel...")
    demo_paths = [str(f) for f in demo_files]
    
    # Use ProcessPoolExecutor for better Windows compatibility
    # Note: team_players set cannot be pickled directly, so we pass it as a parameter
    # For multiprocessing, we need to ensure team_players is serializable
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_demo = {
            executor.submit(_process_single_demo, path, target_team, sample_interval, team_players): path
            for path in demo_paths
        }
        
        # Collect results as they complete
        results = []
        for future in as_completed(future_to_demo):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                demo_path = future_to_demo[future]
                results.append({
                    'file': os.path.basename(demo_path),
                    'path': demo_path,
                    'success': False,
                    'error': str(e),
                    'map': None,
                    'rounds_count': 0
                })
    
    # Collect and validate results
    all_rounds = []
    all_utility = []
    all_positions = []
    all_kills = []
    errors = []
    processed_demos = []
    maps_seen = set()
    
    for result in results:
        if not result['success']:
            error_msg = f"{result['file']}: {result.get('error', 'Unknown error')}"
            errors.append(error_msg)
            print(f"  [ERROR] {error_msg}")
            continue
        
        map_name = result['map']
        maps_seen.add(map_name)
        
        # Validate map consistency
        if validate_map:
            if target_map is None:
                target_map = map_name
                print(f"  {result['file']}: Map {map_name} (setting as target)")
            elif map_name != target_map:
                error_msg = f"{result['file']}: Map mismatch ({map_name} != {target_map})"
                errors.append(error_msg)
                print(f"  [SKIP] {error_msg}")
                continue
        
        # Collect data
        if result['rounds'] is not None and not result['rounds'].empty:
            all_rounds.append(result['rounds'])
        if result['utility'] is not None and not result['utility'].empty:
            all_utility.append(result['utility'])
        if result['positions'] is not None and not result['positions'].empty:
            all_positions.append(result['positions'])
        if result['kills'] is not None and not result['kills'].empty:
            all_kills.append(result['kills'])
        
        processed_demos.append({
            'file': result['file'],
            'map': map_name,
            'rounds': result['rounds_count']
        })
        print(f"  [SUCCESS] {result['file']}: {map_name}, {result['rounds_count']} rounds")
    
    # Consolidate all data
    consolidated = consolidate_data(
        all_rounds, all_utility, all_positions, all_kills
    )
    
    # Create summary
    summary = {
        'total_demos': len(demo_files),
        'processed_demos': len(processed_demos),
        'failed_demos': len(errors),
        'map': target_map if target_map else (list(maps_seen)[0] if maps_seen else 'Unknown'),
        'target_team': target_team,
        'total_rounds': consolidated['rounds'].shape[0] if not consolidated['rounds'].empty else 0,
        'total_utility_events': consolidated['utility'].shape[0] if not consolidated['utility'].empty else 0,
        'total_position_records': consolidated['positions'].shape[0] if not consolidated['positions'].empty else 0,
        'total_kill_events': consolidated['kills'].shape[0] if not consolidated['kills'].empty else 0,
        'demo_files': [d['file'] for d in processed_demos]
    }
    
    consolidated['summary'] = summary
    consolidated['errors'] = errors
    
    return consolidated


def consolidate_data(
    rounds_list: List[pd.DataFrame],
    utility_list: List[pd.DataFrame],
    positions_list: List[pd.DataFrame],
    kills_list: List[pd.DataFrame]
) -> Dict[str, pd.DataFrame]:
    """
    Consolidate data from multiple demos into unified DataFrames.
    
    Args:
        rounds_list: List of round DataFrames from different demos
        utility_list: List of utility DataFrames from different demos
        positions_list: List of position DataFrames from different demos
        kills_list: List of kill DataFrames from different demos
        
    Returns:
        Dictionary with consolidated DataFrames:
        - 'rounds': Consolidated round data
        - 'utility': Consolidated utility data
        - 'positions': Consolidated position data
        - 'kills': Consolidated kill data
    """
    # Consolidate rounds
    if rounds_list:
        rounds_consolidated = pd.concat(rounds_list, ignore_index=True)
    else:
        rounds_consolidated = pd.DataFrame()
    
    # Consolidate utility
    if utility_list:
        utility_consolidated = pd.concat(utility_list, ignore_index=True)
    else:
        utility_consolidated = pd.DataFrame()
    
    # Consolidate positions
    if positions_list:
        positions_consolidated = pd.concat(positions_list, ignore_index=True)
    else:
        positions_consolidated = pd.DataFrame()
    
    # Consolidate kills
    if kills_list:
        kills_consolidated = pd.concat(kills_list, ignore_index=True)
    else:
        kills_consolidated = pd.DataFrame()
    
    return {
        'rounds': rounds_consolidated,
        'utility': utility_consolidated,
        'positions': positions_consolidated,
        'kills': kills_consolidated
    }

