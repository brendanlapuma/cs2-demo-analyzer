"""
CT-Side Analysis Module

Analyzes Counter-Terrorist side gameplay including:
- Defensive statistics and win rates
- Retake success rates (overall and per-bombsite)
- CT-side fragging statistics
- Utility usage patterns
"""

import pandas as pd


def analyze_ct_side(rounds_df, kills_df, utility_df):
    """
    Analyze CT-side tendencies including retake success rates.
    
    Args:
        rounds_df: DataFrame with round data including 'side', 'bombsite', 'winner' columns
        kills_df: DataFrame with kill events
        utility_df: DataFrame with utility usage events
        
    Returns:
        Dictionary containing CT-side statistics:
        - total_rounds: Number of CT-side rounds played
        - wins/losses: Round outcomes
        - win_rate: Percentage of rounds won
        - planted_against: Number of times bomb was planted
        - retakes_won: Number of successful retakes
        - retake_rate: Overall retake success percentage
        - retake_by_site: Per-bombsite retake statistics
        - kills: Fragging statistics (total, entry frags, headshots)
        - utility: Utility usage statistics (total, by type, average per round)
    """
    if rounds_df.empty:
        return None
    
    ct_rounds = rounds_df[rounds_df['side'] == 'CT'].copy()
    
    if ct_rounds.empty:
        return {'error': 'No CT-side rounds found'}
    
    ct_wins = (ct_rounds['winner'] == 'CT').sum()
    ct_losses = len(ct_rounds) - ct_wins
    ct_win_rate = (ct_wins / len(ct_rounds) * 100) if len(ct_rounds) > 0 else 0
    
    # Retake success - overall and per bombsite
    planted_rounds = ct_rounds[ct_rounds['bombsite'] != 'not_planted']
    retakes = (planted_rounds['winner'] == 'CT').sum()
    retake_rate = (retakes / len(planted_rounds) * 100) if len(planted_rounds) > 0 else 0
    
    # Per-bombsite retake stats
    retake_by_site = {}
    if not planted_rounds.empty:
        for site in planted_rounds['bombsite'].unique():
            site_rounds = planted_rounds[planted_rounds['bombsite'] == site]
            site_retakes = (site_rounds['winner'] == 'CT').sum()
            retake_by_site[site] = {
                'plants_against': int(len(site_rounds)),
                'retakes_won': int(site_retakes),
                'retake_rate': float((site_retakes / len(site_rounds) * 100) if len(site_rounds) > 0 else 0)
            }
    
    # CT-side kills
    ct_kills = None
    if kills_df is not None and not kills_df.empty:
        # Match kills to rounds by round_num and join with side info
        kills_with_side = kills_df.merge(
            rounds_df[['round_num', 'side']], 
            on='round_num', 
            how='left'
        )
        ct_side_kills = kills_with_side[
            (kills_with_side['side'] == 'CT') & 
            (kills_with_side['attacker_side'] == 'CT')
        ]
        
        if not ct_side_kills.empty:
            ct_kills = {
                'total': len(ct_side_kills),
                'entry_frags': int(ct_side_kills['is_entry_frag'].sum()),
                'headshots': int(ct_side_kills['headshot'].sum()),
                'headshot_rate': float((ct_side_kills['headshot'].sum() / len(ct_side_kills) * 100))
            }
    
    # CT-side utility
    ct_utility = None
    if utility_df is not None and not utility_df.empty:
        utility_with_side = utility_df.merge(
            rounds_df[['round_num', 'side']], 
            on='round_num', 
            how='left'
        )
        ct_side_utility = utility_with_side[
            (utility_with_side['side'] == 'CT') & 
            (utility_with_side['thrower_side'] == 'CT')
        ]
        
        if not ct_side_utility.empty:
            ct_utility = {
                'total': int(len(ct_side_utility)),
                'by_type': ct_side_utility['grenade_type'].value_counts().to_dict(),
                'avg_per_round': float(len(ct_side_utility) / len(ct_rounds))
            }
    
    return {
        'total_rounds': int(len(ct_rounds)),
        'wins': int(ct_wins),
        'losses': int(ct_losses),
        'win_rate': float(ct_win_rate),
        'planted_against': int(len(planted_rounds)),
        'retakes_won': int(retakes),
        'retake_rate': float(retake_rate),
        'retake_by_site': retake_by_site,
        'kills': ct_kills,
        'utility': ct_utility
    }
