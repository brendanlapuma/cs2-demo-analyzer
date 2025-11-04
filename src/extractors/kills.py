"""
CS2 Demo Analyzer - Kill Event Data Extraction

This module contains functions for extracting kill/death event data from CS2 demo files.
"""

import os

try:
    from awpy import Demo
    import pandas as pd
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Please install with: pip install -r requirements.txt")
    raise


def extract_kill_events(demo_path: str = None, target_team: str = None, demo_obj: 'Demo' = None):
    """
    Extract kill/death event data from a CS2 demo file.
    
    Extracts all kill events with attacker, victim, weapon, location, and timing.
    Identifies entry frags (first kill of each round).
    Uses the awpy Demo.kills property which contains processed kill data.
    Reference: https://awpy.readthedocs.io/en/latest/examples/parse_demo.html#
    
    Args:
        demo_path: Path to the .dem file (required if demo_obj not provided)
        target_team: Optional team name to filter kills. If None, extracts all kills.
        demo_obj: Optional pre-parsed Demo object. If provided, demo_path is ignored.
        
    Returns:
        pandas DataFrame with columns:
        - attacker_name: Name of player who got the kill
        - victim_name: Name of player who died
        - weapon: Weapon used for the kill
        - attacker_side: 'CT' or 'T'
        - victim_side: 'CT' or 'T'
        - round_num: Round number
        - tick: Game tick when kill occurred
        - seconds_into_round: Seconds into the round (integer, for calculations)
        - time_into_round: Time into round formatted as MM:SS (e.g., "1:10" for 70 seconds)
        - x, y, z: Attacker position coordinates
        - is_entry_frag: True if this is the first kill of the round, False otherwise
        - headshot: True if headshot, False otherwise
        - match_file: Demo file name
    """
    # Support both path and pre-parsed Demo object
    if demo_obj is None:
        if demo_path is None or not os.path.exists(demo_path):
            print(f"Error: Demo file not found: {demo_path}")
            return None
        demo = Demo(demo_path)
        demo.parse()
        demo_path_to_use = demo_path
    else:
        demo = demo_obj
        demo_path_to_use = demo_path if demo_path else 'Unknown'
    
    try:
        
        # CS2 tick rate (typically 64 ticks per second)
        TICK_RATE = 64.0
        
        # Get rounds data for timing
        rounds_df = demo.rounds.to_pandas()
        
        # Get kills data
        kills_df = demo.kills.to_pandas()
        
        if kills_df.empty:
            print(f"Warning: No kill data found in {demo_path}")
            return pd.DataFrame()
        
        # Create tick ranges for each round (for timing calculation)
        round_tick_ranges = {}
        sorted_rounds = sorted(rounds_df['round_num'].unique())
        for i, round_num in enumerate(sorted_rounds):
            round_data = rounds_df[rounds_df['round_num'] == round_num].iloc[0]
            start_tick = round_data['start']
            round_tick_ranges[round_num] = {'start': start_tick}
        
        # Process kills and add derived fields
        kill_data = []
        
        # Sort kills by round and tick to identify entry frags
        kills_sorted = kills_df.sort_values(['round_num', 'tick']).reset_index(drop=True)
        
        # Track first kill per round for entry frag detection
        first_kill_per_round = set()
        
        for i, (_, kill) in enumerate(kills_sorted.iterrows()):
            round_num = kill['round_num']
            tick = kill['tick']
            
            # Check if this is the first kill of the round
            if round_num not in first_kill_per_round:
                first_kill_per_round.add(round_num)
                is_entry_frag = True
            else:
                is_entry_frag = False
            
            # Calculate seconds into round and format as MM:SS
            start_tick = round_tick_ranges.get(round_num, {}).get('start', tick)
            total_seconds = int((tick - start_tick) / TICK_RATE) if start_tick <= tick else 0
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            time_into_round = f"{minutes}:{seconds:02d}"
            
            kill_data.append({
                'attacker_name': kill.get('attacker_name', 'Unknown'),
                'victim_name': kill.get('victim_name', 'Unknown'),
                'weapon': kill.get('weapon', 'Unknown'),
                'attacker_side': kill.get('attacker_side', '').upper() if pd.notna(kill.get('attacker_side', '')) else None,
                'victim_side': kill.get('victim_side', '').upper() if pd.notna(kill.get('victim_side', '')) else None,
                'round_num': round_num,
                'tick': tick,
                'seconds_into_round': total_seconds,  # Keep as integer seconds for calculations
                'time_into_round': time_into_round,  # Formatted as MM:SS
                'x': kill.get('attacker_X', None),
                'y': kill.get('attacker_Y', None),
                'z': kill.get('attacker_Z', None),
                'is_entry_frag': is_entry_frag,
                'headshot': kill.get('headshot', False) if pd.notna(kill.get('headshot', False)) else False,
                'match_file': os.path.basename(demo_path_to_use) if demo_path_to_use != 'Unknown' else 'Unknown'
            })
        
        kills_output_df = pd.DataFrame(kill_data)
        
        # Filter by target team if specified
        if target_team is not None and not kills_output_df.empty:
            # Filter by attacker name containing target team (case-insensitive)
            # This is a simple approach - can be enhanced with proper team player mapping
            kills_output_df = kills_output_df[
                kills_output_df['attacker_name'].str.contains(target_team, case=False, na=False)
            ]
        
        return kills_output_df
        
    except Exception as e:
        print(f"Error extracting kill event data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Clean up Demo object if we created it
        if demo_obj is None and 'demo' in locals():
            del demo

