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
    that consistently play together on the same side.
    
    In CS2, each match has two teams of 5 players. This function identifies
    which team of 5 appears consistently across multiple demos.
    
    Args:
        demo_paths: List of paths to demo files
        min_players: Minimum number of players to consider it the same team
        
    Returns:
        Set of player names that form the common team
    """
    if not demo_paths:
        return set()
    
    # Get team compositions from each demo
    # Each demo will have 2 teams (T and CT), we need to track which 5-player groups appear together
    team_compositions_per_demo = []
    
    for demo_path in demo_paths:
        if not os.path.exists(demo_path):
            continue
        
        try:
            demo = Demo(demo_path)
            demo.parse()
            
            # Get players and their sides from the first few rounds to identify teams
            if hasattr(demo, 'ticks'):
                ticks_df = demo.ticks.to_pandas()
                
                # Sample from early rounds to get team compositions
                early_ticks = ticks_df[ticks_df['round_num'].isin([1, 2, 3])]
                
                if not early_ticks.empty and 'name' in early_ticks.columns and 'side' in early_ticks.columns:
                    # Group players by side in the first round
                    first_round = early_ticks[early_ticks['round_num'] == 1]
                    
                    # Get unique players per side
                    t_players = set(first_round[first_round['side'].str.upper() == 'T']['name'].unique())
                    ct_players = set(first_round[first_round['side'].str.upper() == 'CT']['name'].unique())
                    
                    # Store both teams (we'll figure out which is common later)
                    if len(t_players) >= 4:  # Should be 5, but allow for 4 in case of missing data
                        team_compositions_per_demo.append(('T', t_players))
                    if len(ct_players) >= 4:
                        team_compositions_per_demo.append(('CT', ct_players))
            
            del demo
            
        except Exception as e:
            print(f"Warning: Could not parse {demo_path}: {e}")
            continue
    
    if not team_compositions_per_demo:
        return set()
    
    # Find which team composition appears most frequently across demos
    # Compare each team to all others and count overlaps
    team_overlap_scores = []
    
    for i, (side_i, team_i) in enumerate(team_compositions_per_demo):
        overlap_count = 0
        total_overlap_players = Counter()
        
        for j, (side_j, team_j) in enumerate(team_compositions_per_demo):
            if i != j:
                overlap = team_i & team_j
                if len(overlap) >= min_players:
                    overlap_count += 1
                    total_overlap_players.update(overlap)
        
        team_overlap_scores.append({
            'team': team_i,
            'overlap_count': overlap_count,
            'consistent_players': set(player for player, count in total_overlap_players.items() 
                                     if count >= len(demo_paths) * 0.6)
        })
    
    # Find the team with the most overlaps (appears in most demos)
    if team_overlap_scores:
        best_team = max(team_overlap_scores, key=lambda x: (x['overlap_count'], len(x['team'])))
        
        # Return the consistent players (appear in most demos with this team)
        if best_team['consistent_players'] and len(best_team['consistent_players']) >= min_players:
            return best_team['consistent_players']
        elif len(best_team['team']) >= min_players:
            return best_team['team']
    
    return set()


def identify_all_teams(demo_paths: List[str], min_players: int = 4, min_demos: int = 2) -> List[Set[str]]:
    """
    Identify all teams that appear in multiple demos within a map folder.
    
    This function finds all teams that appear in at least min_demos demos,
    allowing multiple teams to be analyzed if they each have multiple matches.
    
    Args:
        demo_paths: List of paths to demo files
        min_players: Minimum number of players to consider it the same team
        min_demos: Minimum number of demos a team must appear in to be included
        
    Returns:
        List of sets, where each set contains player names forming a team
    """
    if not demo_paths or len(demo_paths) < min_demos:
        return []
    
    # Get team compositions from each demo
    team_compositions_per_demo = []
    
    for demo_path in demo_paths:
        if not os.path.exists(demo_path):
            continue
        
        try:
            demo = Demo(demo_path)
            demo.parse()
            
            # Get players and their sides from the first few rounds to identify teams
            if hasattr(demo, 'ticks'):
                ticks_df = demo.ticks.to_pandas()
                
                # Sample from early rounds to get team compositions
                early_ticks = ticks_df[ticks_df['round_num'].isin([1, 2, 3])]
                
                if not early_ticks.empty and 'name' in early_ticks.columns and 'side' in early_ticks.columns:
                    # Group players by side in the first round
                    first_round = early_ticks[early_ticks['round_num'] == 1]
                    
                    # Get unique players per side
                    t_players = set(first_round[first_round['side'].str.upper() == 'T']['name'].unique())
                    ct_players = set(first_round[first_round['side'].str.upper() == 'CT']['name'].unique())
                    
                    # Store both teams with their demo path for tracking
                    if len(t_players) >= min_players:
                        team_compositions_per_demo.append({
                            'demo': demo_path,
                            'team': t_players
                        })
                    if len(ct_players) >= min_players:
                        team_compositions_per_demo.append({
                            'demo': demo_path,
                            'team': ct_players
                        })
            
            del demo
            
        except Exception as e:
            print(f"Warning: Could not parse {demo_path}: {e}")
            continue
    
    if not team_compositions_per_demo:
        return []
    
    # Group similar teams together (teams with min_players overlap)
    team_groups = []
    used_indices = set()
    
    for i, comp_i in enumerate(team_compositions_per_demo):
        if i in used_indices:
            continue
        
        # Start a new team group
        team_group = {
            'teams': [comp_i['team']],
            'demos': {comp_i['demo']},
            'all_players': comp_i['team'].copy()
        }
        used_indices.add(i)
        
        # Find all similar teams
        for j, comp_j in enumerate(team_compositions_per_demo):
            if j in used_indices or j <= i:
                continue
            
            # Check if this team overlaps with our group
            overlap = comp_i['team'] & comp_j['team']
            if len(overlap) >= min_players:
                team_group['teams'].append(comp_j['team'])
                team_group['demos'].add(comp_j['demo'])
                team_group['all_players'].update(comp_j['team'])
                used_indices.add(j)
        
        # Only include teams that appear in multiple demos
        if len(team_group['demos']) >= min_demos:
            # Find the consistent players across this team's appearances
            player_counts = Counter()
            for team in team_group['teams']:
                player_counts.update(team)
            
            # Players that appear in at least 60% of this team's matches
            threshold = len(team_group['demos']) * 0.6
            consistent_players = {player for player, count in player_counts.items() 
                                 if count >= threshold}
            
            if len(consistent_players) >= min_players:
                team_groups.append(consistent_players)
    
    return team_groups


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

