"""
Report Generation Module

Handles generation of scouting reports in multiple formats:
- Text reports: Human-readable formatted reports
- JSON reports: Machine-readable data export
- CSV exports: Raw data for further analysis
"""

from datetime import datetime
import json
from pathlib import Path


def generate_report_header(team_name, map_name, demo_count, team_players):
    """
    Generate formatted report header with team and map information.
    
    Args:
        team_name: Display name for the team
        map_name: Name of the map being analyzed
        demo_count: Number of demos analyzed
        team_players: Set of player names in the team
        
    Returns:
        Formatted header string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"""
{'=' * 80}
CS2 TEAM SCOUTING REPORT
{'=' * 80}

Generated: {timestamp}
Team: {team_name}
Map: {map_name}
Demos Analyzed: {demo_count}

Team Roster ({len(team_players)} players):
{', '.join(sorted(team_players))}

{'=' * 80}
"""
    return header


def write_text_report(output_path, team_name, map_name, demo_count, team_players,
                      t_side_analysis, ct_side_analysis, all_rounds_df, all_kills_df, 
                      all_utility_df, all_positions_df):
    """
    Write comprehensive team scouting report in text format.
    
    Args:
        output_path: Path to output file
        team_name: Display name for the team
        map_name: Name of the map
        demo_count: Number of demos analyzed
        team_players: Set of player names
        t_side_analysis: Dictionary of T-side statistics
        ct_side_analysis: Dictionary of CT-side statistics
        all_rounds_df: DataFrame with all round data
        all_kills_df: DataFrame with all kill events
        all_utility_df: DataFrame with all utility events
        all_positions_df: DataFrame with all position samples
    """
    with open(output_path, 'w') as f:
        # Header
        f.write(generate_report_header(team_name, map_name, demo_count, team_players))
        
        # T-Side Analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("T-SIDE ANALYSIS\n")
        f.write("=" * 80 + "\n")
        
        if t_side_analysis and 'error' not in t_side_analysis:
            f.write(f"\nTotal T-Side Rounds: {t_side_analysis['total_rounds']}\n")
            f.write(f"Record: {t_side_analysis['wins']}W - {t_side_analysis['losses']}L\n")
            f.write(f"Win Rate: {t_side_analysis['win_rate']:.1f}%\n")
            f.write(f"\nBomb Plants: {t_side_analysis['total_plants']}\n")
            f.write(f"Plant Rate: {t_side_analysis['plant_rate']:.1f}%\n")
            
            if t_side_analysis['bombsite_stats']:
                f.write("\nBombsite Preferences:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Site':<20} {'Plants':<10} {'% of Plants':<15} {'Wins':<10} {'Win Rate'}\n")
                f.write("-" * 80 + "\n")
                
                for site, stats in sorted(t_side_analysis['bombsite_stats'].items(), 
                                         key=lambda x: x[1]['plants'], reverse=True):
                    f.write(f"{site:<20} {stats['plants']:<10} {stats['percentage']:>6.1f}%{' ':<8} "
                           f"{stats['wins']:<10} {stats['win_rate']:>6.1f}%\n")
            
            if t_side_analysis['kills']:
                f.write("\nT-Side Fragging:\n")
                f.write(f"  Total Kills: {t_side_analysis['kills']['total']}\n")
                f.write(f"  Entry Frags: {t_side_analysis['kills']['entry_frags']}\n")
                f.write(f"  Headshot Rate: {t_side_analysis['kills']['headshot_rate']:.1f}%\n")
            
            if t_side_analysis['utility']:
                f.write("\nT-Side Utility Usage:\n")
                f.write(f"  Total Utility: {t_side_analysis['utility']['total']}\n")
                f.write(f"  Avg per Round: {t_side_analysis['utility']['avg_per_round']:.1f}\n")
                f.write("  By Type:\n")
                for nade_type, count in sorted(t_side_analysis['utility']['by_type'].items(),
                                              key=lambda x: x[1], reverse=True):
                    f.write(f"    - {nade_type}: {count}\n")
        else:
            f.write("\nNo T-side data available\n")
        
        # CT-Side Analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("CT-SIDE ANALYSIS\n")
        f.write("=" * 80 + "\n")
        
        if ct_side_analysis and 'error' not in ct_side_analysis:
            f.write(f"\nTotal CT-Side Rounds: {ct_side_analysis['total_rounds']}\n")
            f.write(f"Record: {ct_side_analysis['wins']}W - {ct_side_analysis['losses']}L\n")
            f.write(f"Win Rate: {ct_side_analysis['win_rate']:.1f}%\n")
            f.write(f"\nRounds with Bomb Plant: {ct_side_analysis['planted_against']}\n")
            f.write(f"Successful Retakes: {ct_side_analysis['retakes_won']}\n")
            f.write(f"Overall Retake Success Rate: {ct_side_analysis['retake_rate']:.1f}%\n")
            
            if ct_side_analysis['retake_by_site']:
                f.write("\nRetake Success by Bombsite:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Site':<20} {'Plants Against':<20} {'Retakes Won':<20} {'Success Rate'}\n")
                f.write("-" * 80 + "\n")
                
                for site, stats in sorted(ct_side_analysis['retake_by_site'].items(), 
                                         key=lambda x: x[1]['plants_against'], reverse=True):
                    f.write(f"{site:<20} {stats['plants_against']:<20} {stats['retakes_won']:<20} "
                           f"{stats['retake_rate']:>6.1f}%\n")
            
            if ct_side_analysis['kills']:
                f.write("\nCT-Side Fragging:\n")
                f.write(f"  Total Kills: {ct_side_analysis['kills']['total']}\n")
                f.write(f"  Entry Frags (CT aggression): {ct_side_analysis['kills']['entry_frags']}\n")
                f.write(f"  Headshot Rate: {ct_side_analysis['kills']['headshot_rate']:.1f}%\n")
            
            if ct_side_analysis['utility']:
                f.write("\nCT-Side Utility Usage:\n")
                f.write(f"  Total Utility: {ct_side_analysis['utility']['total']}\n")
                f.write(f"  Avg per Round: {ct_side_analysis['utility']['avg_per_round']:.1f}\n")
                f.write("  By Type:\n")
                for nade_type, count in sorted(ct_side_analysis['utility']['by_type'].items(),
                                              key=lambda x: x[1], reverse=True):
                    f.write(f"    - {nade_type}: {count}\n")
        else:
            f.write("\nNo CT-side data available\n")
        
        # Summary Statistics
        f.write("\n" + "=" * 80 + "\n")
        f.write("OVERALL STATISTICS\n")
        f.write("=" * 80 + "\n")
        f.write(f"\nTotal Rounds Analyzed: {len(all_rounds_df)}\n")
        f.write(f"Total Kills: {len(all_kills_df) if all_kills_df is not None else 0}\n")
        f.write(f"Total Utility Events: {len(all_utility_df) if all_utility_df is not None else 0}\n")
        f.write(f"Total Position Samples: {len(all_positions_df) if all_positions_df is not None else 0}\n")
        
        # Overall record
        if not all_rounds_df.empty:
            team_rounds = all_rounds_df[all_rounds_df['side'].notna()]
            if not team_rounds.empty:
                team_wins = ((team_rounds['side'] == 'T') & (team_rounds['winner'] == 'T')).sum() + \
                           ((team_rounds['side'] == 'CT') & (team_rounds['winner'] == 'CT')).sum()
                team_total = len(team_rounds)
                overall_win_rate = (team_wins / team_total * 100) if team_total > 0 else 0
                f.write(f"\nOverall Record: {team_wins}W - {team_total - team_wins}L\n")
                f.write(f"Overall Win Rate: {overall_win_rate:.1f}%\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF SCOUTING REPORT\n")
        f.write("=" * 80 + "\n")


def write_json_report(output_path, team_name, team_players, map_name, demo_count,
                      t_side_analysis, ct_side_analysis, all_rounds_df, all_kills_df,
                      all_utility_df, all_positions_df):
    """
    Write scouting report data in JSON format.
    
    Args:
        output_path: Path to output file
        team_name: Display name for the team
        team_players: Set of player names
        map_name: Name of the map
        demo_count: Number of demos analyzed
        t_side_analysis: Dictionary of T-side statistics
        ct_side_analysis: Dictionary of CT-side statistics
        all_rounds_df: DataFrame with all round data
        all_kills_df: DataFrame with all kill events
        all_utility_df: DataFrame with all utility events
        all_positions_df: DataFrame with all position samples
    """
    json_data = {
        'team': {
            'name': team_name,
            'players': sorted(list(team_players))
        },
        'map': map_name,
        'demos_analyzed': demo_count,
        'analysis': {
            't_side': t_side_analysis,
            'ct_side': ct_side_analysis
        },
        'statistics': {
            'total_rounds': int(len(all_rounds_df)),
            'total_kills': int(len(all_kills_df)) if all_kills_df is not None else 0,
            'total_utility': int(len(all_utility_df)) if all_utility_df is not None else 0,
            'total_positions': int(len(all_positions_df)) if all_positions_df is not None else 0
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(json_data, f, indent=2)


def write_csv_reports(output_dir, all_rounds_df, all_kills_df, all_utility_df, all_positions_df):
    """
    Export raw data to CSV files for external analysis.
    
    Args:
        output_dir: Directory path to write CSV files
        all_rounds_df: DataFrame with all round data
        all_kills_df: DataFrame with all kill events
        all_utility_df: DataFrame with all utility events
        all_positions_df: DataFrame with all position samples
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if all_rounds_df is not None and not all_rounds_df.empty:
        all_rounds_df.to_csv(output_dir / "rounds.csv", index=False)
    
    if all_kills_df is not None and not all_kills_df.empty:
        all_kills_df.to_csv(output_dir / "kills.csv", index=False)
    
    if all_utility_df is not None and not all_utility_df.empty:
        all_utility_df.to_csv(output_dir / "utility.csv", index=False)
    
    if all_positions_df is not None and not all_positions_df.empty:
        all_positions_df.to_csv(output_dir / "positions.csv", index=False)
