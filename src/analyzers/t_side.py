"""
T-Side Analysis Module

Analyzes Terrorist side gameplay including:
- Bombsite preferences and plant rates
- Win rates per bombsite
- T-side fragging statistics
- Utility usage patterns
"""

import pandas as pd


def analyze_t_side(rounds_df, kills_df, utility_df):
    """
    Analyze T-side tendencies including bombsite preferences.
    
    Args:
        rounds_df: DataFrame with round data including 'side', 'bombsite', 'winner' columns
        kills_df: DataFrame with kill events
        utility_df: DataFrame with utility usage events
        
    Returns:
        Dictionary containing T-side statistics:
        - total_rounds: Number of T-side rounds played
        - wins/losses: Round outcomes
        - win_rate: Percentage of rounds won
        - total_plants: Number of bomb plants
        - plant_rate: Percentage of rounds with bomb plant
        - bombsite_stats: Per-bombsite statistics (plants, wins, win rate, percentage)
        - kills: Fragging statistics (total, entry frags, headshots)
        - utility: Utility usage statistics (total, by type, average per round)
    """
    if rounds_df.empty:
        return None
    
    t_rounds = rounds_df[rounds_df['side'] == 'T'].copy()
    
    if t_rounds.empty:
        return {'error': 'No T-side rounds found'}
    
    t_wins = (t_rounds['winner'] == 'T').sum()
    t_losses = len(t_rounds) - t_wins
    t_win_rate = (t_wins / len(t_rounds) * 100) if len(t_rounds) > 0 else 0
    
    # Bombsite analysis
    planted_rounds = t_rounds[t_rounds['bombsite'] != 'not_planted']
    plant_rate = (len(planted_rounds) / len(t_rounds) * 100) if len(t_rounds) > 0 else 0
    
    bombsite_stats = {}
    if not planted_rounds.empty:
        for site in planted_rounds['bombsite'].unique():
            site_rounds = planted_rounds[planted_rounds['bombsite'] == site]
            site_wins = (site_rounds['winner'] == 'T').sum()
            bombsite_stats[site] = {
                'plants': int(len(site_rounds)),
                'wins': int(site_wins),
                'win_rate': float((site_wins / len(site_rounds) * 100) if len(site_rounds) > 0 else 0),
                'percentage': float((len(site_rounds) / len(planted_rounds) * 100))
            }
    
    # T-side kills
    t_kills = None
    if kills_df is not None and not kills_df.empty:
        kills_with_side = kills_df.merge(
            rounds_df[['round_num', 'side']], 
            on='round_num', 
            how='left'
        )
        t_side_kills = kills_with_side[
            (kills_with_side['side'] == 'T') & 
            (kills_with_side['attacker_side'] == 'T')
        ]
        
        if not t_side_kills.empty:
            t_kills = {
                'total': int(len(t_side_kills)),
                'entry_frags': int(t_side_kills['is_entry_frag'].sum()),
                'headshots': int(t_side_kills['headshot'].sum()),
                'headshot_rate': float((t_side_kills['headshot'].sum() / len(t_side_kills) * 100))
            }
    
    # T-side utility
    t_utility = None
    if utility_df is not None and not utility_df.empty:
        utility_with_side = utility_df.merge(
            rounds_df[['round_num', 'side']], 
            on='round_num', 
            how='left'
        )
        t_side_utility = utility_with_side[
            (utility_with_side['side'] == 'T') & 
            (utility_with_side['thrower_side'] == 'T')
        ]
        
        if not t_side_utility.empty:
            t_utility = {
                'total': int(len(t_side_utility)),
                'by_type': {k: int(v) for k, v in t_side_utility['grenade_type'].value_counts().to_dict().items()},
                'avg_per_round': float(len(t_side_utility) / len(t_rounds))
            }
    
    return {
        'total_rounds': int(len(t_rounds)),
        'wins': int(t_wins),
        'losses': int(t_losses),
        'win_rate': float(t_win_rate),
        'total_plants': int(len(planted_rounds)),
        'plant_rate': float(plant_rate),
        'bombsite_stats': bombsite_stats,
        'kills': t_kills,
        'utility': t_utility
    }
