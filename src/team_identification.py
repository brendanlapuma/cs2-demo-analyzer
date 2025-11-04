"""
CS2 Demo Analyzer - Team Identification Functions

This module contains functions for identifying teams and mapping them to sides (T/CT).
"""

import os
from typing import List, Set, Dict, Optional
from collections import Counter

try:
    from awpy import Demo
    import pandas as pd
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Please install with: pip install -r requirements.txt")
    raise


def identify_common_team(demo_paths: List[str], min_players: int = 4) -> Set[str]:
    """
    Identify the common team across multiple demo files by finding players
    that appear in all (or most) demos.
    
    Args:
        demo_paths: List of paths to demo files
        min_players: Minimum number of players to consider it the same team
        
    Returns:
        Set of player names that form the common team
    """
    if not demo_paths:
        return set()
    
    # Get all players from each demo
    all_players_per_demo = []
    
    for demo_path in demo_paths:
        if not os.path.exists(demo_path):
            continue
        
        try:
            demo = Demo(demo_path)
            demo.parse()
            
            # Get unique players from kills or ticks
            players = set()
            if hasattr(demo, 'kills'):
                kills_df = demo.kills.to_pandas()
                if 'attacker_name' in kills_df.columns:
                    players.update(kills_df['attacker_name'].dropna().unique())
                if 'victim_name' in kills_df.columns:
                    players.update(kills_df['victim_name'].dropna().unique())
            
            if hasattr(demo, 'ticks'):
                ticks_df = demo.ticks.to_pandas()
                if 'name' in ticks_df.columns:
                    players.update(ticks_df['name'].dropna().unique())
            
            all_players_per_demo.append(players)
            
            del demo
            
        except Exception as e:
            print(f"Warning: Could not parse {demo_path}: {e}")
            continue
    
    if not all_players_per_demo:
        return set()
    
    # Find players that appear in all demos
    common_players = set(all_players_per_demo[0])
    for players in all_players_per_demo[1:]:
        common_players &= players
    
    # If we found at least min_players in common, that's the team
    if len(common_players) >= min_players:
        return common_players
    
    # Otherwise, find players that appear in at least 80% of demos
    player_counts = Counter()
    for players in all_players_per_demo:
        player_counts.update(players)
    
    # Get players that appear in at least 80% of demos
    threshold = len(demo_paths) * 0.8
    frequent_players = {player for player, count in player_counts.items() if count >= threshold}
    
    if len(frequent_players) >= min_players:
        return frequent_players
    
    return set()


def determine_team_side_for_round(
    demo_obj: Demo, 
    round_num: int, 
    team_players: Set[str]
) -> Optional[str]:
    """
    Determine which side (T or CT) the target team played on in a specific round.
    
    Args:
        demo_obj: Parsed Demo object
        round_num: Round number to check
        team_players: Set of player names that belong to the target team
        
    Returns:
        'T' or 'CT' if team side can be determined, None otherwise
    """
    if not hasattr(demo_obj, 'ticks'):
        return None
    
    ticks_df = demo_obj.ticks.to_pandas()
    
    # Get ticks for this round
    round_ticks = ticks_df[ticks_df['round_num'] == round_num]
    
    if round_ticks.empty:
        return None
    
    # For each team player, find their side in this round
    player_sides = {}
    for player in team_players:
        player_ticks = round_ticks[round_ticks['name'] == player]
        if not player_ticks.empty and 'side' in player_ticks.columns:
            # Get the most common side for this player in this round
            sides = player_ticks['side'].dropna().unique()
            if len(sides) > 0:
                player_sides[player] = sides[0].upper()
    
    if not player_sides:
        return None
    
    # Count how many team players were on each side
    side_counts = {'T': 0, 'CT': 0}
    for side in player_sides.values():
        if side in side_counts:
            side_counts[side] += 1
    
    # If majority of team players are on one side, that's the team's side
    if side_counts['T'] > side_counts['CT']:
        return 'T'
    elif side_counts['CT'] > side_counts['T']:
        return 'CT'
    elif side_counts['T'] == side_counts['CT'] and side_counts['T'] > 0:
        # Tie - use the first player's side
        return list(player_sides.values())[0]
    
    return None


def identify_team_from_demos(demos_folder: str, min_players: int = 4) -> Dict:
    """
    Identify the common team across all demos in a folder.
    
    Args:
        demos_folder: Path to folder containing demo files
        min_players: Minimum number of players to consider it a team
        
    Returns:
        Dictionary with:
        - 'team_players': Set of player names
        - 'team_name': Generated team name
        - 'demo_count': Number of demos analyzed
    """
    from pathlib import Path
    
    demos_path = Path(demos_folder)
    if not demos_path.exists():
        return {
            'team_players': set(),
            'team_name': 'Unknown Team',
            'demo_count': 0
        }
    
    demo_files = sorted(demos_path.glob("*.dem"))
    demo_paths = [str(f) for f in demo_files]
    
    team_players = identify_common_team(demo_paths, min_players)
    
    # Generate team name
    if team_players:
        sorted_players = sorted(team_players)
        if len(sorted_players) <= 5:
            team_name = ", ".join(sorted_players)
        else:
            team_name = ", ".join(sorted_players[:5]) + f" (+{len(sorted_players) - 5} more)"
    else:
        team_name = "Unknown Team"
    
    return {
        'team_players': team_players,
        'team_name': team_name,
        'demo_count': len(demo_paths)
    }

