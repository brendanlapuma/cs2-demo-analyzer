"""
CS2 Demo Analyzer - Analysis Functions

This module contains functions for analyzing team tendencies and patterns:
- T-side analysis (bombsite hits, pistol rounds, entry frags)
- CT-side analysis (site stacks, pushes)
- Utility analysis
"""

import pandas as pd
from typing import Dict, Optional


def analyze_bombsite_hits(rounds_df: pd.DataFrame) -> Dict:
    """
    Analyze bombsite hit patterns for T-side rounds.
    
    Task 4.1: Bombsite Hit Analysis
    - Count bombsite plants per site (A vs B)
    - Calculate percentage distribution
    - Calculate win rate per bombsite
    - Identify most frequently hit bombsite
    
    Args:
        rounds_df: DataFrame with round data including 'side', 'bombsite', 'winner' columns
        
    Returns:
        Dictionary with bombsite hit statistics
    """
    if rounds_df.empty:
        return {
            'error': 'No round data provided'
        }
    
    # Filter for T-side rounds
    # If 'side' column is populated (team-specific analysis), filter by side == 'T'
    # If 'side' column is None/null (general analysis), analyze all rounds from T-side perspective
    if rounds_df['side'].notna().any():
        # Team-specific mode: Filter for rounds where the target team played T-side
        t_rounds = rounds_df[rounds_df['side'] == 'T'].copy()
        analysis_mode = 'team_specific'
    else:
        # General mode: Consider all rounds (both teams' T-side play)
        # We'll analyze bombsite plants regardless of which team planted
        t_rounds = rounds_df.copy()
        analysis_mode = 'general'
    
    if t_rounds.empty:
        return {
            'error': 'No T-side rounds found' if analysis_mode == 'team_specific' else 'No rounds found',
            'total_t_rounds': 0
        }
    
    # Filter rounds where bomb was planted
    planted_rounds = t_rounds[t_rounds['bombsite'] != 'not_planted'].copy()
    
    # Count bombsite hits
    bombsite_counts = planted_rounds['bombsite'].value_counts().to_dict()
    
    # Calculate percentages
    total_plants = len(planted_rounds)
    bombsite_percentages = {}
    if total_plants > 0:
        for site, count in bombsite_counts.items():
            bombsite_percentages[site] = (count / total_plants) * 100
    
    # Calculate win rate per bombsite
    bombsite_wins = {}
    bombsite_win_rates = {}
    
    for site in bombsite_counts.keys():
        site_rounds = planted_rounds[planted_rounds['bombsite'] == site]
        if analysis_mode == 'team_specific':
            # Team-specific: Count wins where target team (playing T) won
            wins = (site_rounds['winner'] == 'T').sum()
        else:
            # General: In general mode, count wins for whichever team planted
            # Since we're analyzing from T-perspective, count T wins for all plants
            wins = (site_rounds['winner'] == 'T').sum()
        bombsite_wins[site] = wins
        bombsite_win_rates[site] = (wins / len(site_rounds) * 100) if len(site_rounds) > 0 else 0
    
    # Identify most frequently hit bombsite
    most_hit_site = max(bombsite_counts.items(), key=lambda x: x[1])[0] if bombsite_counts else None
    
    # Overall T-side win rate
    if analysis_mode == 'team_specific':
        # Team-specific: T-side rounds for the target team only
        t_wins = (t_rounds['winner'] == 'T').sum()
        t_win_rate = (t_wins / len(t_rounds) * 100) if len(t_rounds) > 0 else 0
    else:
        # General: Count all T-side wins across all rounds
        t_wins = (t_rounds['winner'] == 'T').sum()
        t_win_rate = (t_wins / len(t_rounds) * 100) if len(t_rounds) > 0 else 0
    
    return {
        'analysis_mode': analysis_mode,
        'total_t_rounds': len(t_rounds),
        'total_plants': total_plants,
        'plant_rate': (total_plants / len(t_rounds) * 100) if len(t_rounds) > 0 else 0,
        'bombsite_counts': bombsite_counts,
        'bombsite_percentages': bombsite_percentages,
        'bombsite_wins': bombsite_wins,
        'bombsite_win_rates': bombsite_win_rates,
        'most_hit_site': most_hit_site,
        'overall_t_win_rate': t_win_rate,
        't_wins': t_wins,
        't_losses': len(t_rounds) - t_wins
    }


def print_bombsite_analysis(results: Dict):
    """Print bombsite hit analysis results in a readable format."""
    if 'error' in results:
        print(f"Error: {results['error']}")
        return
    
    print("\n" + "=" * 60)
    print("BOMBSITE HIT ANALYSIS (T-Side)")
    if results.get('analysis_mode') == 'team_specific':
        print("Mode: Team-Specific Analysis (Target Team's T-Side Rounds Only)")
    else:
        print("Mode: General Analysis (All T-Side Rounds)")
    print("=" * 60)
    
    print(f"\nTotal T-Side Rounds: {results['total_t_rounds']}")
    print(f"Total Bombsite Plants: {results['total_plants']}")
    print(f"Plant Rate: {results['plant_rate']:.1f}%")
    print(f"Overall T-Side Win Rate: {results['overall_t_win_rate']:.1f}% ({results['t_wins']}W-{results['t_losses']}L)")
    
    if results['bombsite_counts']:
        print(f"\nBombsite Distribution:")
        print("-" * 60)
        print(f"{'Site':<15} {'Plants':<10} {'Percentage':<12} {'Wins':<8} {'Win Rate':<10}")
        print("-" * 60)
        
        for site, count in sorted(results['bombsite_counts'].items(), key=lambda x: x[1], reverse=True):
            pct = results['bombsite_percentages'].get(site, 0)
            wins = results['bombsite_wins'].get(site, 0)
            win_rate = results['bombsite_win_rates'].get(site, 0)
            
            print(f"{site:<15} {count:<10} {pct:<12.1f}% {wins:<8} {win_rate:<10.1f}%")
        
        print(f"\nMost Frequently Hit Bombsite: {results['most_hit_site']}")
    else:
        print("\nNo bombsite plants found in T-side rounds")

