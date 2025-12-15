"""
Strategy Discovery Tool

Command-line interface for discovering team strategies from demo files.

Usage:
    python strategy_analyzer.py --map inferno --side T
    python strategy_analyzer.py --map nuke --side CT --team "player1,player2,player3,player4,player5"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors import extract_round_data, extract_utility_data, extract_player_positions, extract_kill_events
from src.team_identification import identify_all_teams
from src.strats import (discover_strategies, analyze_strategy_clusters, generate_strategy_report,
                       plot_strategy_clusters, plot_feature_importance, plot_cluster_statistics,
                       generate_strategy_profiles)
from awpy import Demo


def load_map_data(map_name: str, team_players: set = None):
    """
    Load and combine data from all demos for a specific map.
    
    Args:
        map_name: Name of the map folder
        team_players: Optional set of player names for team-specific analysis
        
    Returns:
        Tuple of (rounds_df, positions_df, utility_df, kills_df, demo_count)
    """
    demos_folder = Path("demos") / map_name
    
    if not demos_folder.exists():
        print(f"Error: {demos_folder} does not exist")
        return None, None, None, None, 0
    
    demo_files = list(demos_folder.glob("*.dem"))
    
    if not demo_files:
        print(f"Error: No demo files found in {demos_folder}")
        return None, None, None, None, 0
    
    print(f"Loading {len(demo_files)} demo(s) from {map_name}...")
    
    all_rounds = []
    all_positions = []
    all_utility = []
    all_kills = []
    
    for idx, demo_file in enumerate(demo_files, 1):
        try:
            print(f"  [{idx}/{len(demo_files)}] {demo_file.name}...", end=" ")
            
            demo = Demo(str(demo_file))
            demo.parse(player_props=['X', 'Y', 'Z'])
            
            # Extract data
            rounds_df = extract_round_data(
                demo_path=str(demo_file),
                demo_obj=demo,
                team_players=team_players
            )
            
            positions_df = extract_player_positions(
                demo_path=str(demo_file),
                demo_obj=demo,
                sample_interval=10
            )
            
            utility_df = extract_utility_data(
                demo_path=str(demo_file),
                demo_obj=demo
            )
            
            kills_df = extract_kill_events(
                demo_path=str(demo_file),
                demo_obj=demo
            )
            
            # Collect data
            if rounds_df is not None and not rounds_df.empty:
                all_rounds.append(rounds_df)
            if positions_df is not None and not positions_df.empty:
                all_positions.append(positions_df)
            if utility_df is not None and not utility_df.empty:
                all_utility.append(utility_df)
            if kills_df is not None and not kills_df.empty:
                all_kills.append(kills_df)
            
            print("✓")
            del demo
            
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    # Combine all data
    combined_rounds = pd.concat(all_rounds, ignore_index=True) if all_rounds else pd.DataFrame()
    combined_positions = pd.concat(all_positions, ignore_index=True) if all_positions else pd.DataFrame()
    combined_utility = pd.concat(all_utility, ignore_index=True) if all_utility else pd.DataFrame()
    combined_kills = pd.concat(all_kills, ignore_index=True) if all_kills else pd.DataFrame()
    
    print(f"\nLoaded {len(combined_rounds)} rounds, {len(combined_positions)} positions, "
          f"{len(combined_utility)} utility events, {len(combined_kills)} kills")
    
    return combined_rounds, combined_positions, combined_utility, combined_kills, len(demo_files)


def main():
    parser = argparse.ArgumentParser(description='Discover team strategies from CS2 demos')
    parser.add_argument('--map', required=True, help='Map name (folder in demos/)')
    parser.add_argument('--side', required=True, choices=['T', 'CT'], help='Side to analyze')
    parser.add_argument('--team', help='Comma-separated player names for team-specific analysis')
    parser.add_argument('--eps', type=float, default=0.5, help='DBSCAN epsilon parameter')
    parser.add_argument('--min-samples', type=int, default=2, help='DBSCAN min_samples parameter')
    parser.add_argument('--output-dir', default='output', help='Output directory for reports')
    
    args = parser.parse_args()
    
    # Clear output directory
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("CS2 STRATEGY DISCOVERY TOOL")
    print("=" * 80)
    print(f"Map: {args.map}")
    print(f"Side: {args.side}")
    
    # Parse team players if provided
    team_players = None
    if args.team:
        team_players = set(p.strip() for p in args.team.split(','))
        print(f"Team: {', '.join(sorted(team_players))}")
    else:
        print("Mode: Map-wide analysis (all teams)")
    
    print()
    
    # Load data
    rounds_df, positions_df, utility_df, kills_df, demo_count = load_map_data(
        args.map,
        team_players
    )
    
    if rounds_df is None or rounds_df.empty:
        print("Error: No data loaded")
        return
    
    # Discover strategies
    print(f"\nDiscovering {args.side}-side strategies...")
    print(f"  DBSCAN parameters: eps={args.eps}, min_samples={args.min_samples}")
    
    rounds_with_strategies, metadata = discover_strategies(
        rounds_df,
        positions_df,
        utility_df,
        kills_df,
        side=args.side,
        team_players=team_players,
        eps=args.eps,
        min_samples=args.min_samples
    )
    
    if 'error' in metadata:
        print(f"Error: {metadata['error']}")
        return
    
    print(f"\n✓ Discovered {metadata['num_strategies']} strategy pattern(s)")
    print(f"  - Clustered rounds: {metadata['num_rounds'] - metadata['num_noise']}")
    print(f"  - Unclustered rounds: {metadata['num_noise']}")
    
    # Analyze strategies
    print(f"\nAnalyzing strategies...")
    strategy_analysis = analyze_strategy_clusters(
        rounds_with_strategies,
        args.side,
        team_players
    )
    
    # Generate report
    report_text = generate_strategy_report(strategy_analysis, args.side)
    print("\n" + report_text)
    
    # Save outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    team_suffix = "_team" if team_players else "_mapwide"
    base_name = f"{args.map}_{args.side}{team_suffix}_strategies_{timestamp}"
    
    # Save text report
    report_path = output_dir / f"{base_name}.txt"
    with open(report_path, 'w') as f:
        f.write(report_text)
    print(f"\n✓ Saved text report: {report_path}")
    
    # Save JSON data (exclude non-serializable metadata like feature_matrix, labels)
    json_metadata = {k: v for k, v in metadata.items() 
                     if k not in ['feature_matrix', 'labels', 'feature_names']}
    
    json_data = {
        'map': args.map,
        'side': args.side,
        'team_specific': team_players is not None,
        'team_players': sorted(list(team_players)) if team_players else None,
        'demos_analyzed': demo_count,
        'metadata': json_metadata,
        'strategies': strategy_analysis
    }
    
    # Convert numpy/pandas types to Python native types for JSON serialization
    def convert_types(obj):
        """Recursively convert numpy/pandas types to Python native types"""
        import numpy as np
        if isinstance(obj, dict):
            return {key: convert_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (pd.DataFrame, pd.Series)):
            return None  # Skip DataFrames/Series
        elif pd.api.types.is_scalar(obj) and pd.isna(obj):
            return None
        else:
            return obj
    
    json_data = convert_types(json_data)
    
    json_path = output_dir / f"{base_name}.json"
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"✓ Saved JSON data: {json_path}")
    
    # Save CSV with round labels
    csv_path = output_dir / f"{base_name}_rounds.csv"
    rounds_with_strategies.to_csv(csv_path, index=False)
    print(f"✓ Saved labeled rounds: {csv_path}")
    
    # Generate visualizations
    print(f"\nGenerating visualizations...")
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    
    # Plot cluster visualization (PCA)
    pca_path = output_dir / f"{base_name}_clusters_pca.png"
    plot_strategy_clusters(
        metadata['feature_matrix'],
        metadata['labels'],
        rounds_with_strategies,
        method='pca',
        output_path=pca_path,
        side=args.side,
        title_suffix=f" (eps={args.eps}, min_samples={args.min_samples})"
    )
    
    # Plot feature importance
    feature_importance_path = output_dir / f"{base_name}_feature_importance.png"
    plot_feature_importance(
        metadata['feature_matrix'],
        metadata['feature_names'],
        metadata['labels'],
        output_path=feature_importance_path
    )
    
    # Plot cluster statistics
    stats_path = output_dir / f"{base_name}_statistics.png"
    plot_cluster_statistics(
        rounds_with_strategies,
        args.side,
        output_path=stats_path
    )
    
    # Generate strategy profiles (directories with heatmaps and descriptions)
    generate_strategy_profiles(
        rounds_with_strategies,
        metadata['feature_matrix'],
        metadata['feature_names'],
        metadata['labels'],
        strategy_analysis,
        args.side,
        output_dir,
        args.map
    )
    
    import matplotlib.pyplot as plt
    plt.close('all')  # Clean up
    
    print("\n" + "=" * 80)
    print("Strategy discovery complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
