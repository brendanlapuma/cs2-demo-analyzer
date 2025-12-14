"""
Strategy Analysis Module

Analyzes discovered strategy clusters and generates reports.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path


def analyze_strategy_clusters(rounds_df: pd.DataFrame,
                              side: str,
                              team_players: Optional[set] = None) -> Dict:
    """
    Analyze discovered strategy clusters.
    
    Args:
        rounds_df: DataFrame with rounds and strategy_cluster labels
        side: Side analyzed ('T' or 'CT')
        team_players: Set of player names if team-specific (optional)
        
    Returns:
        Dictionary with analysis of each strategy cluster
    """
    if 'strategy_cluster' not in rounds_df.columns:
        return {'error': 'No strategy clusters found in data'}
    
    # Filter for the specific side
    # In map-wide mode, rounds won't have side values (NaN), but the features were
    # already filtered by side during extraction, so we use all rounds
    if 'side' in rounds_df.columns and rounds_df['side'].notna().any():
        side_rounds = rounds_df[rounds_df['side'] == side].copy()
    else:
        side_rounds = rounds_df.copy()
    
    if side_rounds.empty:
        return {'error': f'No {side}-side rounds found'}
    
    # Get unique clusters (excluding noise -1)
    clusters = sorted([c for c in side_rounds['strategy_cluster'].unique() if c != -1])
    
    strategy_analysis = {}
    
    for cluster_id in clusters:
        cluster_rounds = side_rounds[side_rounds['strategy_cluster'] == cluster_id]
        
        if cluster_rounds.empty:
            continue
        
        # Basic stats
        total_rounds = len(cluster_rounds)
        # In map-wide mode, side column exists but has NaN values
        # Check if side column has actual values to determine mode
        if 'side' in cluster_rounds.columns and cluster_rounds['side'].notna().any():
            wins = (cluster_rounds['side'] == cluster_rounds['winner']).sum()
        else:
            wins = (cluster_rounds['winner'] == side).sum()
        win_rate = (wins / total_rounds * 100) if total_rounds > 0 else 0
        
        # Bombsite preference
        bombsite_counts = cluster_rounds['bombsite'].value_counts()
        most_common_site = bombsite_counts.index[0] if not bombsite_counts.empty else 'unknown'
        
        # Calculate percentage for each bombsite
        bombsite_distribution = {}
        for site, count in bombsite_counts.items():
            if site != 'not_planted':
                bombsite_distribution[site] = {
                    'count': int(count),
                    'percentage': float(count / total_rounds * 100)
                }
        
        strategy_analysis[f'Strategy_{cluster_id}'] = {
            'cluster_id': int(cluster_id),
            'frequency': int(total_rounds),
            'percentage_of_rounds': float(total_rounds / len(side_rounds) * 100),
            'wins': int(wins),
            'losses': int(total_rounds - wins),
            'win_rate': float(win_rate),
            'bombsite_primary': most_common_site,
            'bombsite_distribution': bombsite_distribution,
            'round_numbers': cluster_rounds['round_num'].tolist()
        }
    
    # Analyze noise rounds (unclustered)
    noise_rounds = side_rounds[side_rounds['strategy_cluster'] == -1]
    if not noise_rounds.empty:
        # In map-wide mode, side column exists but has NaN values
        if 'side' in noise_rounds.columns and noise_rounds['side'].notna().any():
            noise_wins = (noise_rounds['side'] == noise_rounds['winner']).sum()
        else:
            noise_wins = (noise_rounds['winner'] == side).sum()
        strategy_analysis['Unclustered'] = {
            'cluster_id': -1,
            'frequency': int(len(noise_rounds)),
            'percentage_of_rounds': float(len(noise_rounds) / len(side_rounds) * 100),
            'wins': int(noise_wins),
            'losses': int(len(noise_rounds) - noise_wins),
            'win_rate': float((noise_wins / len(noise_rounds) * 100) if len(noise_rounds) > 0 else 0),
            'note': 'Rounds that did not match any discovered strategy pattern'
        }
    
    return strategy_analysis


def generate_strategy_report(strategy_analysis: Dict,
                             side: str,
                             output_path: Optional[Path] = None) -> str:
    """
    Generate human-readable strategy report.
    
    Args:
        strategy_analysis: Dictionary from analyze_strategy_clusters
        side: Side analyzed ('T' or 'CT')
        output_path: Optional path to write report (if None, returns string)
        
    Returns:
        Formatted report string
    """
    if 'error' in strategy_analysis:
        return f"Error: {strategy_analysis['error']}"
    
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append(f"DISCOVERED STRATEGIES - {side} SIDE")
    report_lines.append("=" * 80)
    
    # Summary
    num_strategies = len([k for k in strategy_analysis.keys() if k != 'Unclustered'])
    report_lines.append(f"\nDiscovered {num_strategies} distinct strategy pattern(s)\n")
    
    # Strategy details
    for strategy_name in sorted(strategy_analysis.keys()):
        if strategy_name == 'Unclustered':
            continue
            
        stats = strategy_analysis[strategy_name]
        
        report_lines.append("-" * 80)
        report_lines.append(f"{strategy_name}")
        report_lines.append("-" * 80)
        report_lines.append(f"Usage: {stats['frequency']} rounds ({stats['percentage_of_rounds']:.1f}%)")
        report_lines.append(f"Record: {stats['wins']}W - {stats['losses']}L")
        report_lines.append(f"Win Rate: {stats['win_rate']:.1f}%")
        
        if stats['bombsite_distribution']:
            report_lines.append(f"\nBombsite Distribution:")
            for site, site_stats in sorted(stats['bombsite_distribution'].items(),
                                          key=lambda x: x[1]['count'], reverse=True):
                report_lines.append(f"  {site}: {site_stats['count']} rounds ({site_stats['percentage']:.1f}%)")
        
        report_lines.append("")
    
    # Unclustered rounds
    if 'Unclustered' in strategy_analysis:
        unclustered = strategy_analysis['Unclustered']
        report_lines.append("-" * 80)
        report_lines.append("Unclustered Rounds")
        report_lines.append("-" * 80)
        report_lines.append(f"Rounds: {unclustered['frequency']} ({unclustered['percentage_of_rounds']:.1f}%)")
        report_lines.append(f"Record: {unclustered['wins']}W - {unclustered['losses']}L")
        report_lines.append(f"Win Rate: {unclustered['win_rate']:.1f}%")
        report_lines.append(f"Note: {unclustered['note']}")
        report_lines.append("")
    
    report_lines.append("=" * 80)
    
    report_text = "\n".join(report_lines)
    
    # Write to file if path provided
    if output_path:
        with open(output_path, 'w') as f:
            f.write(report_text)
    
    return report_text


def compare_strategies(rounds_df: pd.DataFrame,
                      side: str,
                      metric: str = 'win_rate') -> pd.DataFrame:
    """
    Compare strategies by a specific metric.
    
    Args:
        rounds_df: DataFrame with strategy clusters
        side: Side to analyze
        metric: Metric to compare ('win_rate', 'frequency', etc.)
        
    Returns:
        DataFrame with strategies sorted by metric
    """
    analysis = analyze_strategy_clusters(rounds_df, side)
    
    if 'error' in analysis:
        return pd.DataFrame()
    
    # Convert to DataFrame for easy comparison
    comparison_data = []
    for strategy_name, stats in analysis.items():
        if strategy_name != 'Unclustered':
            comparison_data.append({
                'strategy': strategy_name,
                'cluster_id': stats['cluster_id'],
                'frequency': stats['frequency'],
                'win_rate': stats['win_rate'],
                'wins': stats['wins'],
                'losses': stats['losses']
            })
    
    df = pd.DataFrame(comparison_data)
    
    if not df.empty and metric in df.columns:
        df = df.sort_values(by=metric, ascending=False)
    
    return df
