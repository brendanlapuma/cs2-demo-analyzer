"""
CS2 Demo Analyzer - Main Entry Point

Parses CS2 demo files and generates comprehensive team scouting reports.
Analyzes team tendencies on both T-side and CT-side for specific maps.

Usage:
    python analyzer.py

The script will:
1. Scan demos/ folder for map-specific subfolders
2. Identify teams that appear in multiple demos per map
3. Extract and analyze gameplay data for each team
4. Generate scouting reports in text, JSON, and CSV formats
"""

import sys
from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

# Import from modular structure
from src.parsers import parse_demo_basic
from src.extractors import extract_round_data, extract_utility_data, extract_player_positions, extract_kill_events
from src.team_identification import identify_all_teams
from src.analyzers import analyze_t_side, analyze_ct_side, write_text_report, write_json_report, write_csv_reports
from awpy import Demo


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
            write_json_report(
                json_path,
                team_name,
                team_players,
                map_name,
                demos_with_team,
                t_side_analysis,
                ct_side_analysis,
                combined_rounds,
                combined_kills if not combined_kills.empty else None,
                combined_utility if not combined_utility.empty else None,
                combined_positions if not combined_positions.empty else None
            )
            print(f"  JSON Data: {json_path.name}")
            
            # Export CSV files
            csv_dir = output_dir / f"{map_name}_{safe_team_name}_csv_{timestamp}"
            write_csv_reports(
                csv_dir,
                combined_rounds,
                combined_kills if not combined_kills.empty else None,
                combined_utility if not combined_utility.empty else None,
                combined_positions if not combined_positions.empty else None
            )
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
