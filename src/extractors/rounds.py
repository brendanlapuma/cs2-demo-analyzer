"""
CS2 Demo Analyzer - Round Data Extraction

This module contains functions for extracting round-level data from CS2 demo files.
"""

import os

try:
    from awpy import Demo
    import pandas as pd
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Please install with: pip install -r requirements.txt")
    raise


def extract_round_data(demo_path: str = None, target_team: str = None, demo_obj: 'Demo' = None, team_players: set = None):
    """
    Extract round-level data from a CS2 demo file.
    
    Uses the awpy Demo.rounds property which already contains processed round data.
    Reference: https://awpy.readthedocs.io/en/latest/examples/parse_demo.html#
    
    Args:
        demo_path: Path to the .dem file (required if demo_obj not provided)
        target_team: Optional team name to filter rounds. If None, extracts all rounds. (Deprecated: use team_players instead)
        demo_obj: Optional pre-parsed Demo object. If provided, demo_path is ignored.
        team_players: Optional set of player names that belong to the target team. Used to determine side per round.
        
    Returns:
        pandas DataFrame with columns:
        - round_num: Round number
        - winner: 'CT' or 'T'
        - bombsite: Site name/ID if bomb was planted, 'not_planted' otherwise
        - side: 'CT' or 'T' (side the target team played on this round, None if no target_team)
        - is_pistol: True if pistol round, False otherwise
        - reason: Round end reason
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
        
        # Use the rounds property which already has all round data processed
        # See: https://awpy.readthedocs.io/en/latest/examples/parse_demo.html#
        rounds_df = demo.rounds.to_pandas()
        
        if rounds_df.empty:
            print(f"Warning: No rounds found in {demo_path}")
            return pd.DataFrame()
        
        # Get accurate bombsite information from bomb property
        # The rounds.bomb_site may be incomplete, so we use demo.bomb for accuracy
        bombsite_map = {}
        if hasattr(demo_obj, 'bomb'):
            bomb_df = demo_obj.bomb.to_pandas()
            # Filter for planted events and map to rounds
            if 'status' in bomb_df.columns:
                planted_bombs = bomb_df[bomb_df['status'] == 'planted']
            else:
                # If no status column, assume all are planted
                planted_bombs = bomb_df
            
            # Map bombsite by round_num and tick
            for _, bomb_row in planted_bombs.iterrows():
                if 'round_num' in bomb_row and 'tick' in bomb_row and 'bombsite' in bomb_row:
                    round_num = bomb_row['round_num']
                    tick = bomb_row['tick']
                    bombsite = bomb_row['bombsite']
                    # Normalize bombsite name (BombsiteA -> bombsite_a, BombsiteB -> bombsite_b)
                    if bombsite:
                        bombsite_normalized = bombsite.lower().replace('bombsite', 'bombsite_')
                        bombsite_map[(round_num, tick)] = bombsite_normalized
        
        # Rename columns for consistency and add derived fields
        rounds_df = rounds_df.rename(columns={
            'bomb_site': 'bombsite'
        })
        
        # Update bombsite from bomb property if available
        if bombsite_map:
            # Match rounds to bomb events by round_num and bomb_plant tick
            for idx, row in rounds_df.iterrows():
                round_num = row['round_num']
                bomb_plant_tick = row.get('bomb_plant')
                
                if pd.notna(bomb_plant_tick):
                    # Find matching bombsite
                    matching_site = None
                    for (rnd, tick), site in bombsite_map.items():
                        if rnd == round_num and abs(tick - bomb_plant_tick) < 100:  # Within 100 ticks
                            matching_site = site
                            break
                    
                    if matching_site:
                        rounds_df.at[idx, 'bombsite'] = matching_site
                    # If no match found but bomb was planted, check if we have any bombsite for this round
                    elif rounds_df.at[idx, 'bombsite'] == 'bombsite_b':
                        # Check if there's a different bombsite for this round
                        round_bombs = [site for (rnd, _), site in bombsite_map.items() if rnd == round_num]
                        if round_bombs:
                            rounds_df.at[idx, 'bombsite'] = round_bombs[0]  # Use first bombsite found for this round
        
        # Determine if pistol round
        # CS2 format: First to 13 wins, pistol rounds are round 1 and round 14 (first round of second half)
        rounds_df['is_pistol'] = rounds_df['round_num'].isin([1, 14])
        
        # Add match file name
        rounds_df['match_file'] = os.path.basename(demo_path_to_use) if demo_path_to_use != 'Unknown' else 'Unknown'
        
        # Normalize winner to uppercase
        rounds_df['winner'] = rounds_df['winner'].str.upper()
        
        # Side determination for target team
        # Note: 'side' column indicates which side (T or CT) the target team played on each round
        rounds_df['side'] = None
        
        # If team_players is provided, determine which side they played each round
        if team_players is not None:
            from src.team_identification import determine_team_side_for_round
            
            # Ensure demo has ticks parsed (needed for side determination)
            if not hasattr(demo_obj, 'ticks') or demo_obj.ticks is None:
                # Re-parse with ticks if needed
                if demo_obj is None:
                    demo_for_ticks = Demo(demo_path_to_use)
                    demo_for_ticks.parse(player_props=['X', 'Y', 'Z'])
                else:
                    # If ticks not parsed, we can't determine sides
                    demo_for_ticks = None
            else:
                demo_for_ticks = demo_obj
            
            if demo_for_ticks:
                # Determine side for each round
                sides = []
                for _, round_row in rounds_df.iterrows():
                    round_num = round_row['round_num']
                    team_side = determine_team_side_for_round(demo_for_ticks, round_num, team_players)
                    sides.append(team_side)
                
                rounds_df['side'] = sides
                
                # Clean up if we created a new demo object
                if demo_obj is None and demo_for_ticks != demo:
                    del demo_for_ticks
        
        # Select and order columns
        columns = ['round_num', 'winner', 'bombsite', 'side', 'is_pistol', 'reason', 'match_file']
        rounds_df = rounds_df[columns]
        
        return rounds_df
        
    except Exception as e:
        print(f"Error extracting round data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Clean up Demo object if we created it
        if demo_obj is None and 'demo' in locals():
            del demo

