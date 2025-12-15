"""
Strategy Profile Generation

Creates detailed profiles for each discovered strategy including:
- Heatmap visualizations of player positions
- Text descriptions of strategy characteristics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.image import imread
from pathlib import Path
from typing import Dict, Optional


def generate_strategy_profiles(rounds_df: pd.DataFrame,
                               feature_matrix: np.ndarray,
                               feature_names: list,
                               labels: np.ndarray,
                               strategy_analysis: Dict,
                               side: str,
                               output_dir: Path,
                               map_name: str):
    """
    Generate individual profile directories for each discovered strategy.
    
    Args:
        rounds_df: DataFrame with rounds and strategy_cluster labels
        feature_matrix: Feature matrix used for clustering
        feature_names: Names of features in feature_matrix
        labels: Cluster labels for each round
        strategy_analysis: Analysis results from analyze_strategy_clusters
        side: Side being analyzed ('T' or 'CT')
        output_dir: Base output directory
        map_name: Name of the map
    """
    # Get unique clusters (excluding noise -1)
    clusters = sorted([c for c in set(labels) if c != -1])
    
    if not clusters:
        print("No strategies to profile (all rounds unclustered)")
        return
    
    print(f"\nGenerating strategy profiles...")
    
    for cluster_id in clusters:
        strategy_name = f"Strategy_{cluster_id}"
        strategy_dir = output_dir / strategy_name
        strategy_dir.mkdir(exist_ok=True)
        
        # Get rounds belonging to this strategy
        cluster_mask = labels == cluster_id
        cluster_features = feature_matrix[cluster_mask]
        
        # Calculate average features for this strategy
        avg_features = cluster_features.mean(axis=0)
        
        # Extract grid features (single snapshot at 30 seconds)
        grid_size = 5  # 5x5 grid
        pos_grid = extract_grid_from_features(avg_features, feature_names, 'pos_grid', grid_size)
        
        # Debug: check if grid has any data
        grid_sum = pos_grid.sum()
        grid_max = pos_grid.max()
        print(f"    {strategy_name}: Grid sum={grid_sum:.2f}, max={grid_max:.2f}, non-zero cells={np.count_nonzero(pos_grid)}")
        
        # Generate heatmap
        generate_heatmap(pos_grid, strategy_dir / "positions_10s_after_freeze.png", 
                        f"{strategy_name} - Positions (10s after freeze)", side, map_name)
        
        # Generate text description
        description = generate_strategy_description(
            cluster_id, strategy_analysis, avg_features, feature_names,
            pos_grid, side
        )
        
        desc_path = strategy_dir / "description.txt"
        with open(desc_path, 'w') as f:
            f.write(description)
        
        print(f"  ✓ {strategy_name}")
    
    print(f"Saved {len(clusters)} strategy profiles to {output_dir}")


def extract_grid_from_features(features: np.ndarray, 
                               feature_names: list,
                               prefix: str,
                               grid_size: int) -> np.ndarray:
    """
    Extract grid features and reshape into 2D array.
    
    Args:
        features: Feature vector
        feature_names: Names of features
        prefix: Prefix for grid features (e.g., 'early_grid')
        grid_size: Size of grid (e.g., 5 for 5x5)
        
    Returns:
        2D numpy array representing the grid
    """
    grid_features = []
    for i in range(grid_size * grid_size):
        feature_name = f"{prefix}_{i}"
        if feature_name in feature_names:
            idx = feature_names.index(feature_name)
            grid_features.append(features[idx])
        else:
            grid_features.append(0.0)
    
    # Reshape to 2D grid
    grid = np.array(grid_features).reshape(grid_size, grid_size)
    return grid


def generate_heatmap(grid: np.ndarray,
                     output_path: Path,
                     title: str,
                     side: str,
                     map_name: str):
    """
    Generate a heatmap visualization of player positions overlaid on map image.
    
    Args:
        grid: 2D numpy array with position counts
        output_path: Path to save the heatmap
        title: Title for the plot
        side: Side being analyzed
        map_name: Name of the map
    """
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Try to load the map image
    map_image_path = Path('demos') / map_name / f"{map_name}.png"
    if map_image_path.exists():
        try:
            map_img = imread(map_image_path)
            ax.imshow(map_img, extent=[0, grid.shape[0], 0, grid.shape[1]], 
                     aspect='auto', zorder=0)
        except Exception as e:
            print(f"    Warning: Could not load map image {map_image_path}: {e}")
    
    # Create heatmap overlay with transparency
    # Normalize grid to 0-1 for better visualization
    if grid.max() > 0:
        grid_normalized = grid / grid.max()
    else:
        grid_normalized = grid
    
    # Create masked array to make zero values transparent
    masked_grid = np.ma.masked_where(grid_normalized == 0, grid_normalized)
    
    # Overlay heatmap with transparency
    im = ax.imshow(masked_grid.T, cmap='hot', interpolation='bilinear', 
                  origin='lower', alpha=0.6, zorder=1,
                  extent=[0, grid.shape[0], 0, grid.shape[1]])
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Relative Player Density', rotation=270, labelpad=20)
    
    # Add grid lines
    ax.set_xticks(np.arange(grid.shape[0] + 1))
    ax.set_yticks(np.arange(grid.shape[1] + 1))
    ax.grid(which='major', color='cyan', linestyle='-', linewidth=1.5, alpha=0.4, zorder=2)
    
    # Labels
    ax.set_xlabel('X Grid', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y Grid', fontsize=12, fontweight='bold')
    ax.set_title(f"{title}\n{map_name.capitalize()} - {side} Side", 
                fontsize=14, fontweight='bold', pad=15)
    
    # Add values in cells if grid has activity
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            value = grid[i, j]
            if value > 0.01:  # Show even small values (threshold lowered from implicit 0)
                # Use white text with black outline for visibility
                text = ax.text(i + 0.5, j + 0.5, f'{value:.2f}',  # Show 2 decimal places
                             ha='center', va='center', color='white', 
                             fontsize=10, fontweight='bold', zorder=3)
                text.set_path_effects([
                    path_effects.Stroke(linewidth=2, foreground='black'),
                    path_effects.Normal()
                ])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def generate_strategy_description(cluster_id: int,
                                  strategy_analysis: Dict,
                                  avg_features: np.ndarray,
                                  feature_names: list,
                                  pos_grid: np.ndarray,
                                  side: str) -> str:
    """
    Generate a text description of the strategy.
    
    Args:
        cluster_id: ID of the strategy cluster
        strategy_analysis: Analysis results for this strategy
        avg_features: Average feature values for this strategy
        feature_names: Names of features
        pos_grid: Position grid snapshot at 20 seconds
        side: Side being analyzed
        
    Returns:
        Text description string
    """
    strategy_name = f"Strategy_{cluster_id}"
    
    if strategy_name not in strategy_analysis:
        return f"{strategy_name}\n\nNo analysis data available."
    
    stats = strategy_analysis[strategy_name]
    
    # Build description
    lines = []
    lines.append("=" * 60)
    lines.append(f"{strategy_name}")
    lines.append("=" * 60)
    lines.append("")
    
    # Basic stats
    lines.append("OVERVIEW")
    lines.append("-" * 60)
    lines.append(f"Usage: {stats['frequency']} rounds ({stats['percentage_of_rounds']:.1f}%)")
    lines.append(f"Win Rate: {stats['win_rate']:.1f}% ({stats['wins']}W - {stats['losses']}L)")
    lines.append("")
    
    # Bombsite preference
    if 'bombsite_distribution' in stats:
        lines.append("BOMBSITE PREFERENCE")
        lines.append("-" * 60)
        bombsites = stats['bombsite_distribution']
        for site, data in sorted(bombsites.items(), key=lambda x: x[1]['count'], reverse=True):
            lines.append(f"  {site}: {data['count']} rounds ({data['percentage']:.1f}%)")
        lines.append("")
    
    # Utility usage
    lines.append("UTILITY USAGE")
    lines.append("-" * 60)
    utility_features = {
        'smoke_count': 'Smokes',
        'flash_count': 'Flashes',
        'he_count': 'HE Grenades',
        'molotov_count': 'Molotovs'
    }
    
    for feature, label in utility_features.items():
        if feature in feature_names:
            idx = feature_names.index(feature)
            count = avg_features[idx]
            lines.append(f"  {label}: {count:.1f} per round")
    
    if 'utility_avg_time' in feature_names:
        idx = feature_names.index('utility_avg_time')
        avg_time = avg_features[idx]
        lines.append(f"  Average throw time: {avg_time:.1f}s into round")
    
    if 'utility_first_time' in feature_names:
        idx = feature_names.index('utility_first_time')
        first_time = avg_features[idx]
        lines.append(f"  First utility: {first_time:.1f}s into round")
    
    lines.append("")
    
    # Kill timing
    lines.append("AGGRESSION PROFILE")
    lines.append("-" * 60)
    if 'first_kill_time' in feature_names:
        idx = feature_names.index('first_kill_time')
        first_kill = avg_features[idx]
        lines.append(f"  First kill: {first_kill:.1f}s into round")
    
    if 'kills_before_30s' in feature_names:
        idx = feature_names.index('kills_before_30s')
        early_kills = avg_features[idx]
        lines.append(f"  Kills before 30s: {early_kills:.1f} per round")
    
    lines.append("")
    
    # Position analysis
    lines.append("POSITIONING PATTERN (10s after freeze end)")
    lines.append("-" * 60)
    
    # Analyze grid concentration
    concentration = analyze_grid_concentration(pos_grid)
    lines.append(f"  {concentration}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def analyze_grid_concentration(grid: np.ndarray) -> str:
    """
    Analyze the concentration pattern of a position grid.
    
    Args:
        grid: 2D position grid
        
    Returns:
        Description string
    """
    total_count = grid.sum()
    
    if total_count == 0:
        return "No positioning data"
    
    # Find hotspot (cell with most activity)
    max_cell = grid.max()
    max_percent = (max_cell / total_count * 100) if total_count > 0 else 0
    
    # Calculate spread (how many cells have activity)
    active_cells = np.sum(grid > 0)
    total_cells = grid.size
    
    # Determine concentration level
    if active_cells <= 3:
        spread = "Very concentrated"
    elif active_cells <= 6:
        spread = "Concentrated"
    elif active_cells <= 12:
        spread = "Moderate spread"
    else:
        spread = "Wide spread"
    
    return f"{spread} ({active_cells}/{total_cells} cells active, hotspot {max_percent:.0f}%)"
