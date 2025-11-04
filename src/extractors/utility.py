"""
CS2 Demo Analyzer - Utility (Grenade) Data Extraction

This module contains functions for extracting utility/grenade data from CS2 demo files.
"""

import os

try:
    from awpy import Demo
    import pandas as pd
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Please install with: pip install -r requirements.txt")
    raise


def extract_utility_data(demo_path: str = None, target_team: str = None, demo_obj: 'Demo' = None):
    """
    Extract utility (grenade) data from a CS2 demo file.
    
    Extracts all grenade events: smokes, flashes, molotovs, and HE grenades.
    Uses grenade detonation events which contain landing coordinates.
    Reference: https://awpy.readthedocs.io/en/latest/examples/parse_demo.html#
    
    Args:
        demo_path: Path to the .dem file (required if demo_obj not provided)
        target_team: Optional team name to filter utility. If None, extracts all utility.
        demo_obj: Optional pre-parsed Demo object. If provided, demo_path is ignored.
        
    Returns:
        pandas DataFrame with columns:
        - grenade_type: 'smoke', 'flash', 'molotov', 'he'
        - x, y, z: Landing coordinates
        - thrower_name: Name of player who threw the grenade
        - thrower_side: 'CT' or 'T'
        - round_num: Round number
        - tick: Game tick when grenade detonated
        - seconds_into_round: Seconds into the round (integer, for calculations)
        - time_into_round: Time into round formatted as MM:SS (e.g., "1:10" for 70 seconds)
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
        
        # Get rounds data for tick-to-round matching and timing
        rounds_df = demo.rounds.to_pandas()
        
        # Create tick ranges for each round
        round_tick_ranges = {}
        sorted_rounds = sorted(rounds_df['round_num'].unique())
        for i, round_num in enumerate(sorted_rounds):
            round_data = rounds_df[rounds_df['round_num'] == round_num].iloc[0]
            start_tick = round_data['start']
            if i + 1 < len(sorted_rounds):
                next_round_num = sorted_rounds[i + 1]
                next_round_data = rounds_df[rounds_df['round_num'] == next_round_num].iloc[0]
                end_tick = next_round_data['start']
            else:
                end_tick = None
            round_tick_ranges[round_num] = {'start': start_tick, 'end': end_tick}
        
        # Collect all grenade events
        utility_data = []
        
        # Map event names to grenade types
        grenade_events = {
            'smokegrenade_detonate': 'smoke',
            'flashbang_detonate': 'flash',
            'hegrenade_detonate': 'he',
            'inferno_startburn': 'molotov'
        }
        
        # Process each grenade event type
        for event_name, grenade_type in grenade_events.items():
            if event_name not in demo.events:
                continue
            
            event_df = demo.events[event_name].to_pandas()
            
            for _, event in event_df.iterrows():
                tick = event['tick']
                x = event.get('x', None)
                y = event.get('y', None)
                z = event.get('z', None)
                thrower_name = event.get('user_name', 'Unknown')
                thrower_side = event.get('user_side', '').upper() if pd.notna(event.get('user_side', '')) else None
                
                # Match to round by tick
                round_num = None
                total_seconds = None
                
                for rnd_num, tick_range in round_tick_ranges.items():
                    start_tick = tick_range['start']
                    end_tick = tick_range['end']
                    
                    if end_tick is not None:
                        if start_tick <= tick < end_tick:
                            round_num = rnd_num
                            total_seconds = int((tick - start_tick) / TICK_RATE)
                            break
                    else:
                        # Last round
                        if tick >= start_tick:
                            round_num = rnd_num
                            total_seconds = int((tick - start_tick) / TICK_RATE)
                            break
                
                # Skip if couldn't match to round
                if round_num is None or total_seconds is None:
                    continue
                
                # Format time as MM:SS
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                time_into_round = f"{minutes}:{seconds:02d}"
                
                utility_data.append({
                    'grenade_type': grenade_type,
                    'x': x,
                    'y': y,
                    'z': z,
                    'thrower_name': thrower_name,
                    'thrower_side': thrower_side,
                    'round_num': round_num,
                    'tick': tick,
                    'seconds_into_round': total_seconds,  # Integer seconds for calculations
                    'time_into_round': time_into_round,  # Formatted as MM:SS
                    'match_file': os.path.basename(demo_path_to_use) if demo_path_to_use != 'Unknown' else 'Unknown'
                })
        
        utility_df = pd.DataFrame(utility_data)
        
        # Filter by target team if specified
        if target_team is not None and not utility_df.empty:
            # Filter by thrower name containing target team (case-insensitive)
            # This is a simple approach - can be enhanced with proper team player mapping
            utility_df = utility_df[
                utility_df['thrower_name'].str.contains(target_team, case=False, na=False)
            ]
        
        return utility_df
        
    except Exception as e:
        print(f"Error extracting utility data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Clean up Demo object if we created it
        if demo_obj is None and 'demo' in locals():
            del demo

