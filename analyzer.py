"""
CS2 Demo Analyzer
Main entry point for the CS2 demo analysis tool.
Parses demo files and generates comprehensive scouting reports for a specific team.
Analyzes team tendencies on both T-side and CT-side for a specific map.
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import shutil

# Import from our modular structure
from src.parsers import parse_demo_basic
from src.extractors import extract_round_data, extract_utility_data, extract_player_positions, extract_kill_events
from src.analysis import analyze_bombsite_hits, print_bombsite_analysis
from src.team_identification import identify_common_team, identify_all_teams
from awpy import Demo


def generate_report_header(team_name, map_name, demo_count, team_players):
    """Generate report header with team and map info."""
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


def analyze_ct_side(rounds_df, kills_df, utility_df):
    """Analyze CT-side tendencies."""
    if rounds_df.empty:
        return None
    
    ct_rounds = rounds_df[rounds_df['side'] == 'CT'].copy()
    
    if ct_rounds.empty:
        return {'error': 'No CT-side rounds found'}
    
    ct_wins = (ct_rounds['winner'] == 'CT').sum()
    ct_losses = len(ct_rounds) - ct_wins
    ct_win_rate = (ct_wins / len(ct_rounds) * 100) if len(ct_rounds) > 0 else 0
    
    # Retake success (rounds where bomb was planted but CT won)
    planted_rounds = ct_rounds[ct_rounds['bombsite'] != 'not_planted']
    retakes = (planted_rounds['winner'] == 'CT').sum()
    retake_rate = (retakes / len(planted_rounds) * 100) if len(planted_rounds) > 0 else 0
    
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
        'kills': ct_kills,
        'utility': ct_utility
    }


def analyze_t_side(rounds_df, kills_df, utility_df):
    """Analyze T-side tendencies including bombsite preferences."""
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


def write_text_report(output_path, team_name, map_name, demo_count, team_players,
                      t_side_analysis, ct_side_analysis, all_rounds_df, all_kills_df, 
                      all_utility_df, all_positions_df):
    """Write comprehensive team scouting report."""
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
                f.write(f"{'Site':<20} {'Plants':<12} {'% of Plants':<15} {'Wins':<10} {'Win Rate'}\n")
                f.write("-" * 80 + "\n")
                
                for site, stats in sorted(t_side_analysis['bombsite_stats'].items(), 
                                         key=lambda x: x[1]['plants'], reverse=True):
                    f.write(f"{site:<20} {stats['plants']:<12} {stats['percentage']:<15.1f}% "
                           f"{stats['wins']:<10} {stats['win_rate']:.1f}%\n")
            
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
            f.write(f"Retake Success Rate: {ct_side_analysis['retake_rate']:.1f}%\n")
            
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


def main():
    """Main function to parse demos and generate team scouting reports."""
    print("CS2 Team Scouting Report Generator")
    print("=" * 80)
    
    # Clear output directory at startup
    output_dir = Path("output")
    if output_dir.exists():
        # Keep .gitkeep file
        for item in output_dir.iterdir():
            if item.name != '.gitkeep':
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        print("Cleared output directory")
    else:
        output_dir.mkdir(exist_ok=True)
    
    # Check for demo folders
    demos_folder = Path("demos")
    
    if not demos_folder.exists():
        print(f"Error: {demos_folder} folder does not exist")
        print("Creating demos folder...")
        demos_folder.mkdir(exist_ok=True)
        print("\nPlease organize your demos by map in subfolders:")
        print("  demos/inferno/")
        print("  demos/nuke/")
        print("  demos/ancient/")
        print("  etc.")
        return
    
    # Find map-specific folders
    map_folders = [f for f in demos_folder.iterdir() if f.is_dir() and not f.name.startswith('.')]
    
    if not map_folders:
        print(f"\nNo map folders found in {demos_folder}/")
        print("Please organize your demos by map in subfolders:")
        print("  demos/inferno/")
        print("  demos/nuke/")
        print("  demos/ancient/")
        print("  etc.")
        return
    
    print(f"\nFound {len(map_folders)} map folder(s):")
    for folder in map_folders:
        demo_count = len(list(folder.glob("*.dem")))
        print(f"  - {folder.name}: {demo_count} demo(s)")
    
    # Process each map folder
    total_reports_generated = 0
    
    for map_folder in map_folders:
        map_name = map_folder.name
        demo_files = sorted(list(map_folder.glob("*.dem")))
        
        if not demo_files:
            print(f"\n[SKIP] No demos found in {map_folder.name}")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"Processing Map: {map_name.upper()}")
        print(f"Demo Files: {len(demo_files)}")
        print("=" * 80)
        
        # Step 1: Identify all teams that appear in multiple demos
        print(f"\nStep 1: Identifying teams across {len(demo_files)} demo(s)...")
        demo_paths = [str(f) for f in demo_files]
        all_teams = identify_all_teams(demo_paths, min_players=4, min_demos=2)
        
        if not all_teams:
            print(f"[WARNING] Could not identify any teams appearing in multiple demos")
            print("Each team must appear in at least 2 demos for analysis.")
            continue
        
        print(f"[SUCCESS] Identified {len(all_teams)} team(s) with multiple matches:")
        for idx, team in enumerate(all_teams, 1):
            team_name = ", ".join(sorted(list(team))[:5])
            if len(team) > 5:
                team_name += f" (+{len(team) - 5} more)"
            print(f"  Team {idx}: {team_name} ({len(team)} players)")
        
        # Step 2: Process each team separately
        for team_idx, team_players in enumerate(all_teams, 1):
            print(f"\n{'-' * 80}")
            print(f"Processing Team {team_idx}/{len(all_teams)}")
            print(f"-" * 80)
            
            team_name = ", ".join(sorted(list(team_players))[:5])
            if len(team_players) > 5:
                team_name += f" (+{len(team_players) - 5} more)"
            
            print(f"Team: {team_name}")
            print(f"Players: {', '.join(sorted(team_players))}")
            
            # Parse all demos and extract data with team context
            print(f"\nParsing demos and extracting data...")
            
            all_rounds = []
            all_kills = []
            all_utility = []
            all_positions = []
            demos_with_team = 0
            
            for idx, demo_file in enumerate(demo_files, 1):
                try:
                    # Parse demo with team context
                    demo = Demo(str(demo_file))
                    demo.parse(player_props=['X', 'Y', 'Z'])
                    
                    # Check if this team is in this demo
                    if hasattr(demo, 'ticks'):
                        ticks_df = demo.ticks.to_pandas()
                        first_round = ticks_df[ticks_df['round_num'] == 1]
                        demo_players = set(first_round['name'].unique())
                        
                        # Check if at least 4 players from our team are in this demo
                        overlap = team_players & demo_players
                        if len(overlap) < 4:
                            del demo
                            continue
                    
                    print(f"  [{demos_with_team + 1}] {demo_file.name}...")
                    demos_with_team += 1
                    
                    # Extract data with team identification
                    rounds_df = extract_round_data(
                        demo_path=str(demo_file),
                        demo_obj=demo,
                        team_players=team_players
                    )
                    
                    kills_df = extract_kill_events(demo_path=str(demo_file), demo_obj=demo)
                    utility_df = extract_utility_data(demo_path=str(demo_file), demo_obj=demo)
                    positions_df = extract_player_positions(
                        demo_path=str(demo_file),
                        demo_obj=demo,
                        sample_interval=10
                    )
                    
                    # Collect data
                    if rounds_df is not None and not rounds_df.empty:
                        all_rounds.append(rounds_df)
                    if kills_df is not None and not kills_df.empty:
                        all_kills.append(kills_df)
                    if utility_df is not None and not utility_df.empty:
                        all_utility.append(utility_df)
                    if positions_df is not None and not positions_df.empty:
                        all_positions.append(positions_df)
                    
                    # Cleanup
                    del demo
                    
                except Exception as e:
                    print(f"      [ERROR] Failed to parse {demo_file.name}: {e}")
                    continue
            
            if not all_rounds or demos_with_team < 2:
                print(f"[SKIP] Team only appears in {demos_with_team} demo(s), need at least 2")
                continue
            
            # Combine all data
            print(f"\nCombining data from {demos_with_team} demo(s)...")
            combined_rounds = pd.concat(all_rounds, ignore_index=True)
            combined_kills = pd.concat(all_kills, ignore_index=True) if all_kills else pd.DataFrame()
            combined_utility = pd.concat(all_utility, ignore_index=True) if all_utility else pd.DataFrame()
            combined_positions = pd.concat(all_positions, ignore_index=True) if all_positions else pd.DataFrame()
            
            print(f"  Total rounds: {len(combined_rounds)}")
            print(f"  Total kills: {len(combined_kills)}")
            print(f"  Total utility: {len(combined_utility)}")
            print(f"  Total positions: {len(combined_positions)}")
            
            # Check side distribution
            side_counts = combined_rounds['side'].value_counts()
            print(f"\n  Team played:")
            for side, count in side_counts.items():
                if pd.notna(side):
                    print(f"    {side}-side: {count} rounds")
            
            # Analyze tendencies
            print(f"\nAnalyzing team tendencies...")
            
            print("  - Analyzing T-side tendencies...")
            t_side_analysis = analyze_t_side(combined_rounds, combined_kills, combined_utility)
            
            print("  - Analyzing CT-side tendencies...")
            ct_side_analysis = analyze_ct_side(combined_rounds, combined_kills, combined_utility)
            
            # Generate reports
            print(f"\nGenerating scouting report...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create safe team name for filenames (use first 3 players)
            safe_team_name = "_".join(sorted(list(team_players))[:3]).replace(" ", "_")
            
            # Text report
            report_path = output_dir / f"{map_name}_{safe_team_name}_report_{timestamp}.txt"
            write_text_report(
                report_path,
                team_name,
                map_name,
                demos_with_team,
                team_players,
                t_side_analysis,
                ct_side_analysis,
                combined_rounds,
                combined_kills if not combined_kills.empty else None,
                combined_utility if not combined_utility.empty else None,
                combined_positions if not combined_positions.empty else None
            )
            print(f"  Text Report: {report_path.name}")
            
            # JSON report
            json_path = output_dir / f"{map_name}_{safe_team_name}_data_{timestamp}.json"
            json_data = {
                'team': {
                    'name': team_name,
                    'players': sorted(list(team_players))
                },
                'map': map_name,
                'demos_analyzed': demos_with_team,
                'analysis': {
                    't_side': t_side_analysis,
                    'ct_side': ct_side_analysis
                },
                'statistics': {
                    'total_rounds': int(len(combined_rounds)),
                    'total_kills': int(len(combined_kills)),
                    'total_utility': int(len(combined_utility)),
                    'total_positions': int(len(combined_positions))
                }
            }
            
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            print(f"  JSON Data: {json_path.name}")
            
            # Export CSV files
            csv_dir = output_dir / f"{map_name}_{safe_team_name}_csv_{timestamp}"
            csv_dir.mkdir(exist_ok=True)
            
            if not combined_rounds.empty:
                combined_rounds.to_csv(csv_dir / "rounds.csv", index=False)
            if not combined_kills.empty:
                combined_kills.to_csv(csv_dir / "kills.csv", index=False)
            if not combined_utility.empty:
                combined_utility.to_csv(csv_dir / "utility.csv", index=False)
            if not combined_positions.empty:
                combined_positions.to_csv(csv_dir / "positions.csv", index=False)
            
            print(f"  CSV Files: {csv_dir.name}/")
            
            print(f"\n[SUCCESS] Scouting report complete!")
            total_reports_generated += 1
            
            # Print summary to console
            print(f"\n{'─' * 80}")
            print(f"SUMMARY: {team_name} on {map_name}")
            print("─" * 80)
            
            if t_side_analysis and 'error' not in t_side_analysis:
                print(f"\nT-Side: {t_side_analysis['wins']}W-{t_side_analysis['losses']}L ({t_side_analysis['win_rate']:.1f}%)")
                print(f"  Plant Rate: {t_side_analysis['plant_rate']:.1f}%")
                if t_side_analysis['bombsite_stats']:
                    print("  Bombsite Preference:")
                    for site, stats in sorted(t_side_analysis['bombsite_stats'].items(),
                                             key=lambda x: x[1]['plants'], reverse=True):
                        print(f"    {site}: {stats['plants']} plants ({stats['percentage']:.1f}%), {stats['win_rate']:.1f}% win rate")
            
            if ct_side_analysis and 'error' not in ct_side_analysis:
                print(f"\nCT-Side: {ct_side_analysis['wins']}W-{ct_side_analysis['losses']}L ({ct_side_analysis['win_rate']:.1f}%)")
                print(f"  Retake Success: {ct_side_analysis['retake_rate']:.1f}%")
    
    print(f"\n{'=' * 80}")
    print(f"Analysis Complete!")
    print(f"Generated {total_reports_generated} scouting report(s)")
    print(f"Output directory: {output_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
