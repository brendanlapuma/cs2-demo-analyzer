"""
CS2 Demo Analyzer - Player Position Data Extraction

This module contains functions for extracting player position data from CS2 demo files.
"""

import os

try:
    from awpy import Demo
    import pandas as pd
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Please install with: pip install -r requirements.txt")
    raise


def extract_player_positions(demo_path: str = None, target_team: str = None, sample_interval: int = None, demo_obj: 'Demo' = None):
    """
    Extract player position data from a CS2 demo file.
    
    Extracts player positions at key moments: round start, freeze end, and optionally
    mid-round samples. Uses the awpy Demo.ticks property which contains player positions.
    Reference: https://awpy.readthedocs.io/en/latest/examples/parse_demo.html#
    
    Args:
        demo_path: Path to the .dem file (required if demo_obj not provided)
        target_team: Optional team name to filter players. If None, extracts all players.
        sample_interval: Optional interval in seconds to sample mid-round positions.
                        If None, only extracts round start and freeze end positions.
        demo_obj: Optional pre-parsed Demo object. If provided, demo_path is ignored.
                  Note: Demo object must be parsed with player_props=['X', 'Y', 'Z'] for position extraction.
        
    Returns:
        pandas DataFrame with columns:
        - player_name: Name of the player
        - player_side: 'CT' or 'T'
        - round_num: Round number
        - x, y, z: Player position coordinates
        - tick: Game tick
        - seconds_into_round: Seconds into the round (integer, for calculations)
        - time_into_round: Time into round formatted as MM:SS (e.g., "1:10" for 70 seconds)
        - phase: 'round_start', 'freeze_end', or 'mid_round'
        - match_file: Demo file name
    """
    # Support both path and pre-parsed Demo object
    if demo_obj is None:
        if demo_path is None or not os.path.exists(demo_path):
            print(f"Error: Demo file not found: {demo_path}")
            return None
        # Parse demo with position properties
        demo = Demo(demo_path)
        demo.parse(player_props=['X', 'Y', 'Z'])
        demo_path_to_use = demo_path
    else:
        demo = demo_obj
        demo_path_to_use = demo_path if demo_path else 'Unknown'
    
    try:
        
        # CS2 tick rate (typically 64 ticks per second)
        TICK_RATE = 64.0
        
        # Get rounds data for timing
        rounds_df = demo.rounds.to_pandas()
        
        # Get ticks data (player positions)
        ticks_df = demo.ticks.to_pandas()
        
        if ticks_df.empty:
            print(f"Warning: No tick data found in {demo_path}")
            return pd.DataFrame()
        
        # Create tick ranges for each round
        round_tick_ranges = {}
        sorted_rounds = sorted(rounds_df['round_num'].unique())
        for i, round_num in enumerate(sorted_rounds):
            round_data = rounds_df[rounds_df['round_num'] == round_num].iloc[0]
            start_tick = round_data['start']
            freeze_end_tick = round_data['freeze_end']
            end_tick = round_data['end']
            if i + 1 < len(sorted_rounds):
                next_round_num = sorted_rounds[i + 1]
                next_round_data = rounds_df[rounds_df['round_num'] == next_round_num].iloc[0]
                round_end_tick = next_round_data['start']
            else:
                round_end_tick = None
            round_tick_ranges[round_num] = {
                'start': start_tick,
                'freeze_end': freeze_end_tick,
                'end': end_tick,
                'round_end': round_end_tick
            }
        
        # Collect position data
        position_data = []
        
        # Process each round
        for round_num in sorted_rounds:
            tick_range = round_tick_ranges[round_num]
            start_tick = tick_range['start']
            freeze_end_tick = tick_range['freeze_end']
            end_tick = tick_range['end']
            round_end_tick = tick_range['round_end']
            
            # Get round's tick range (for mid-round sampling)
            if round_end_tick is not None:
                round_max_tick = round_end_tick
            elif end_tick is not None:
                round_max_tick = end_tick
            else:
                round_max_tick = None
            
            # Extract positions at round start
            round_start_ticks = ticks_df[
                (ticks_df['round_num'] == round_num) & 
                (ticks_df['tick'] == start_tick)
            ]
            for _, tick_row in round_start_ticks.iterrows():
                total_seconds = 0
                time_into_round = "0:00"
                position_data.append({
                    'player_name': tick_row.get('name', 'Unknown'),
                    'player_side': tick_row.get('side', '').upper() if pd.notna(tick_row.get('side', '')) else None,
                    'round_num': round_num,
                    'x': tick_row.get('X', None),
                    'y': tick_row.get('Y', None),
                    'z': tick_row.get('Z', None),
                    'tick': start_tick,
                    'seconds_into_round': total_seconds,
                    'time_into_round': time_into_round,
                    'phase': 'round_start',
                    'match_file': os.path.basename(demo_path_to_use) if demo_path_to_use != 'Unknown' else 'Unknown'
                })
            
            # Extract positions at freeze end
            freeze_end_ticks = ticks_df[
                (ticks_df['round_num'] == round_num) & 
                (ticks_df['tick'] == freeze_end_tick)
            ]
            for _, tick_row in freeze_end_ticks.iterrows():
                total_seconds = int((freeze_end_tick - start_tick) / TICK_RATE)
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                time_into_round = f"{minutes}:{seconds:02d}"
                position_data.append({
                    'player_name': tick_row.get('name', 'Unknown'),
                    'player_side': tick_row.get('side', '').upper() if pd.notna(tick_row.get('side', '')) else None,
                    'round_num': round_num,
                    'x': tick_row.get('X', None),
                    'y': tick_row.get('Y', None),
                    'z': tick_row.get('Z', None),
                    'tick': freeze_end_tick,
                    'seconds_into_round': total_seconds,
                    'time_into_round': time_into_round,
                    'phase': 'freeze_end',
                    'match_file': os.path.basename(demo_path_to_use) if demo_path_to_use != 'Unknown' else 'Unknown'
                })
            
            # Extract mid-round samples if interval specified
            if sample_interval is not None and round_max_tick is not None:
                # Sample at regular intervals (in seconds, convert to ticks)
                sample_interval_ticks = int(sample_interval * TICK_RATE)
                current_tick = freeze_end_tick + sample_interval_ticks
                
                while current_tick < round_max_tick:
                    # Find closest tick to sample time
                    sample_ticks = ticks_df[
                        (ticks_df['round_num'] == round_num) & 
                        (ticks_df['tick'] >= current_tick - sample_interval_ticks // 2) &
                        (ticks_df['tick'] <= current_tick + sample_interval_ticks // 2)
                    ]
                    
                    # Get unique players at this time (use closest tick)
                    if not sample_ticks.empty:
                        # Group by player and get closest tick
                        for player_name in sample_ticks['name'].unique():
                            player_ticks = sample_ticks[sample_ticks['name'] == player_name].copy()
                            # Use tick closest to target
                            player_ticks['tick_diff'] = abs(player_ticks['tick'] - current_tick)
                            closest_tick_row = player_ticks.loc[player_ticks['tick_diff'].idxmin()]
                            
                            total_seconds = int((closest_tick_row['tick'] - start_tick) / TICK_RATE)
                            minutes = total_seconds // 60
                            seconds = total_seconds % 60
                            time_into_round = f"{minutes}:{seconds:02d}"
                            position_data.append({
                                'player_name': closest_tick_row.get('name', 'Unknown'),
                                'player_side': closest_tick_row.get('side', '').upper() if pd.notna(closest_tick_row.get('side', '')) else None,
                                'round_num': round_num,
                                'x': closest_tick_row.get('X', None),
                                'y': closest_tick_row.get('Y', None),
                                'z': closest_tick_row.get('Z', None),
                                'tick': closest_tick_row['tick'],
                                'seconds_into_round': total_seconds,
                                'time_into_round': time_into_round,
                                'phase': 'mid_round',
                                'match_file': os.path.basename(demo_path_to_use) if demo_path_to_use != 'Unknown' else 'Unknown'
                            })
                    
                    current_tick += sample_interval_ticks
        
        position_df = pd.DataFrame(position_data)
        
        # Filter by target team if specified
        if target_team is not None and not position_df.empty:
            # Filter by player name containing target team (case-insensitive)
            # This is a simple approach - can be enhanced with proper team player mapping
            position_df = position_df[
                position_df['player_name'].str.contains(target_team, case=False, na=False)
            ]
        
        return position_df
        
    except Exception as e:
        print(f"Error extracting player position data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Clean up Demo object if we created it
        if demo_obj is None and 'demo' in locals():
            del demo

