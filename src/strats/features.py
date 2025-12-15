"""
Feature Extraction for Strategy Discovery

Extracts strategic features from round data including:
- Spatial features: Player positions in grid cells across map
- Utility features: Grenade usage patterns and locations
- Temporal features: Timing and pacing of executes
- Outcome features: Success rates and patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set


# Map coordinate ranges (approximate - will be determined from data)
# These will be updated dynamically based on actual position data
MAP_X_MIN, MAP_X_MAX = -3000, 3000
MAP_Y_MIN, MAP_Y_MAX = -3000, 3000
GRID_SIZE = 10  # 10x10 grid (reduced from 20x20 to reduce sparsity)


def positions_to_grid(positions_df: pd.DataFrame, 
                     x_min: float, x_max: float,
                     y_min: float, y_max: float,
                     grid_size: int = GRID_SIZE) -> np.ndarray:
    """
    Convert player positions to a grid-based heatmap.
    
    Args:
        positions_df: DataFrame with player positions (must have 'x' and 'y' columns)
        x_min, x_max: X coordinate range
        y_min, y_max: Y coordinate range
        grid_size: Size of grid (grid_size x grid_size)
        
    Returns:
        Flattened array of player counts per grid cell (grid_size^2 elements)
    """
    if positions_df.empty or 'x' not in positions_df.columns or 'y' not in positions_df.columns:
        return np.zeros(grid_size * grid_size)
    
    # Create 2D histogram
    hist, _, _ = np.histogram2d(
        positions_df['x'].values,
        positions_df['y'].values,
        bins=[grid_size, grid_size],
        range=[[x_min, x_max], [y_min, y_max]]
    )
    
    # Flatten to 1D array
    return hist.flatten()


def extract_strategy_features(round_num: int, 
                              rounds_df: pd.DataFrame,
                              positions_df: Optional[pd.DataFrame] = None,
                              utility_df: Optional[pd.DataFrame] = None,
                              kills_df: Optional[pd.DataFrame] = None,
                              team_players: Optional[Set[str]] = None,
                              side: Optional[str] = None,
                              map_bounds: Optional[tuple] = None) -> Dict:
    """
    Extract feature vector representing a round's strategic characteristics.
    
    Args:
        round_num: Round number to extract features for
        rounds_df: DataFrame with round data
        positions_df: DataFrame with player positions (optional)
        utility_df: DataFrame with utility events (optional)
        kills_df: DataFrame with kill events (optional)
        team_players: Set of player names for team-specific analysis (optional)
        side: Side to analyze ('T' or 'CT') for filtering player actions (optional)
        map_bounds: Tuple of (x_min, x_max, y_min, y_max) for consistent grid (optional)
        
    Returns:
        Dictionary of features representing the round's strategy
    """
    # Get round info
    round_info = rounds_df[rounds_df['round_num'] == round_num]
    if round_info.empty:
        return {}
    
    round_info = round_info.iloc[0]
    features = {}
    
    # Basic features
    features['round_num'] = round_num
    features['bombsite'] = 1 if round_info['bombsite'] == 'bombsite_a' else (2 if round_info['bombsite'] == 'bombsite_b' else 0)
    
    # Determine if the analyzed side won
    # If we have a 'side' column (team-specific), check if that side won
    # Otherwise (map-wide), check if the analyzing side won
    if 'side' in round_info.index and pd.notna(round_info['side']):
        features['won'] = 1 if (round_info['side'] == round_info['winner']) else 0
    elif side:
        features['won'] = 1 if (side == round_info['winner']) else 0
    else:
        features['won'] = 0
    
    # Grid-based spatial features from positions
    if positions_df is not None and not positions_df.empty:
        round_positions = positions_df[positions_df['round_num'] == round_num].copy()
        
        # Filter by side (in map-wide mode, filter by player side)
        if side and 'player_side' in round_positions.columns:
            round_positions = round_positions[round_positions['player_side'] == side]
        
        # Filter for team if specified
        if team_players:
            # Use 'player_name' column from positions
            if 'player_name' in round_positions.columns:
                round_positions = round_positions[round_positions['player_name'].isin(team_players)]
            elif 'name' in round_positions.columns:
                round_positions = round_positions[round_positions['name'].isin(team_players)]
        
        if not round_positions.empty and 'x' in round_positions.columns and 'y' in round_positions.columns:
            # Use provided map bounds or determine from current positions
            if map_bounds:
                x_min, x_max, y_min, y_max = map_bounds
            else:
                x_min, x_max = round_positions['x'].min() - 100, round_positions['x'].max() + 100
                y_min, y_max = round_positions['y'].min() - 100, round_positions['y'].max() + 100
            
            # Time column
            time_col = 'seconds_into_round' if 'seconds_into_round' in round_positions.columns else 'seconds'
            
            # Early positioning (first 15 seconds) - converted to 20x20 grid
            early_pos = round_positions[round_positions[time_col] <= 15]
            early_grid = positions_to_grid(early_pos, x_min, x_max, y_min, y_max, GRID_SIZE)
            for i, count in enumerate(early_grid):
                features[f'early_grid_{i}'] = count
            
            # Mid-round positioning (15-45 seconds) - converted to 20x20 grid
            mid_pos = round_positions[(round_positions[time_col] > 15) & (round_positions[time_col] <= 45)]
            mid_grid = positions_to_grid(mid_pos, x_min, x_max, y_min, y_max, GRID_SIZE)
            for i, count in enumerate(mid_grid):
                features[f'mid_grid_{i}'] = count
            
            # Late positioning (45+ seconds) - converted to 20x20 grid
            late_pos = round_positions[round_positions[time_col] > 45]
            late_grid = positions_to_grid(late_pos, x_min, x_max, y_min, y_max, GRID_SIZE)
            for i, count in enumerate(late_grid):
                features[f'late_grid_{i}'] = count
        else:
            # No position data - fill with zeros
            for i in range(GRID_SIZE * GRID_SIZE):
                features[f'early_grid_{i}'] = 0
                features[f'mid_grid_{i}'] = 0
                features[f'late_grid_{i}'] = 0
    else:
        # No position data - fill with zeros
        for i in range(GRID_SIZE * GRID_SIZE):
            features[f'early_grid_{i}'] = 0
            features[f'mid_grid_{i}'] = 0
            features[f'late_grid_{i}'] = 0
    
    # Utility features
    if utility_df is not None and not utility_df.empty:
        round_utility = utility_df[utility_df['round_num'] == round_num].copy()
        
        # Filter by side (in map-wide mode, filter by thrower side)
        if side and 'thrower_side' in round_utility.columns:
            round_utility = round_utility[round_utility['thrower_side'] == side]
        
        # Filter for team if specified
        if team_players:
            round_utility = round_utility[round_utility['thrower_name'].isin(team_players)]
        
        if not round_utility.empty:
            # Count by grenade type
            features['smoke_count'] = len(round_utility[round_utility['grenade_type'] == 'smoke'])
            features['flash_count'] = len(round_utility[round_utility['grenade_type'] == 'flash'])
            features['he_count'] = len(round_utility[round_utility['grenade_type'] == 'he'])
            features['molotov_count'] = len(round_utility[round_utility['grenade_type'] == 'molotov'])
            
            # Utility timing
            if not round_utility.empty:
                time_col_util = 'seconds_into_round' if 'seconds_into_round' in round_utility.columns else 'seconds'
                if time_col_util in round_utility.columns:
                    features['utility_avg_time'] = round_utility[time_col_util].mean()
                    features['utility_first_time'] = round_utility[time_col_util].min()
                else:
                    features['utility_avg_time'] = 0
                    features['utility_first_time'] = 0
            else:
                features['utility_avg_time'] = 0
                features['utility_first_time'] = 0
        else:
            features.update({
                'smoke_count': 0, 'flash_count': 0, 'he_count': 0, 'molotov_count': 0,
                'utility_avg_time': 0, 'utility_first_time': 0
            })
    else:
        features.update({
            'smoke_count': 0, 'flash_count': 0, 'he_count': 0, 'molotov_count': 0,
            'utility_avg_time': 0, 'utility_first_time': 0
        })
    
    # Kill timing features
    if kills_df is not None and not kills_df.empty:
        round_kills = kills_df[kills_df['round_num'] == round_num].copy()
        
        # Filter by side (in map-wide mode, filter by attacker side)
        if side and 'attacker_side' in round_kills.columns:
            round_kills = round_kills[round_kills['attacker_side'] == side]
        
        # Filter for team if specified
        if team_players:
            round_kills = round_kills[round_kills['attacker_name'].isin(team_players)]
        
        if not round_kills.empty:
            time_col_kills = 'seconds_into_round' if 'seconds_into_round' in round_kills.columns else 'seconds'
            if time_col_kills in round_kills.columns:
                features['first_kill_time'] = round_kills[time_col_kills].min()
                features['kills_before_30s'] = len(round_kills[round_kills[time_col_kills] <= 30])
            else:
                features['first_kill_time'] = 0
                features['kills_before_30s'] = 0
        else:
            features['first_kill_time'] = 0
            features['kills_before_30s'] = 0
    else:
        features['first_kill_time'] = 0
        features['kills_before_30s'] = 0
    
    return features


def build_feature_matrix(rounds_df: pd.DataFrame,
                        positions_df: Optional[pd.DataFrame] = None,
                        utility_df: Optional[pd.DataFrame] = None,
                        kills_df: Optional[pd.DataFrame] = None,
                        side: Optional[str] = None,
                        team_players: Optional[Set[str]] = None) -> pd.DataFrame:
    """
    Build feature matrix for all rounds.
    
    Args:
        rounds_df: DataFrame with round data
        positions_df: DataFrame with player positions (optional)
        utility_df: DataFrame with utility events (optional)
        kills_df: DataFrame with kill events (optional)
        side: Side to analyze ('T' or 'CT') - filters player actions by side (optional)
        team_players: Set of player names for team-specific analysis (optional)
        
    Returns:
        DataFrame where each row is a round and columns are features
    """
    # In team-specific mode (when 'side' column has data), filter rounds by side
    # In map-wide mode, analyze all rounds but filter player actions by side
    has_side_data = 'side' in rounds_df.columns and rounds_df['side'].notna().any()
    
    if has_side_data:
        # Team-specific mode: only analyze rounds where the team played the specified side
        if side:
            filtered_rounds = rounds_df[rounds_df['side'] == side].copy()
        else:
            filtered_rounds = rounds_df.copy()
    else:
        # Map-wide mode: analyze all rounds (we'll filter player actions by side in feature extraction)
        filtered_rounds = rounds_df.copy()
    
    if filtered_rounds.empty:
        return pd.DataFrame()
    
    # Compute global map bounds from all position data for consistent grid
    map_bounds = None
    if positions_df is not None and not positions_df.empty:
        # Filter positions by side if specified
        pos_for_bounds = positions_df.copy()
        if side and 'side' in pos_for_bounds.columns:
            pos_for_bounds = pos_for_bounds[pos_for_bounds['side'] == side]
        
        if not pos_for_bounds.empty and 'x' in pos_for_bounds.columns and 'y' in pos_for_bounds.columns:
            x_min = pos_for_bounds['x'].min() - 100
            x_max = pos_for_bounds['x'].max() + 100
            y_min = pos_for_bounds['y'].min() - 100
            y_max = pos_for_bounds['y'].max() + 100
            map_bounds = (x_min, x_max, y_min, y_max)
            print(f"  Map bounds: X[{x_min:.0f}, {x_max:.0f}], Y[{y_min:.0f}, {y_max:.0f}]")
    
    # Extract features for each round
    # Note: Need to identify rounds uniquely by both round_num and match_file
    # since multiple demos will have overlapping round numbers
    features_list = []
    for idx, round_row in filtered_rounds.iterrows():
        round_num = round_row['round_num']
        match_file = round_row.get('match_file', None)
        
        # Filter data for this specific round and demo
        if match_file and 'match_file' in rounds_df.columns:
            round_mask = (rounds_df['round_num'] == round_num) & (rounds_df['match_file'] == match_file)
            # Also filter positions/utility/kills by match_file to avoid mixing data from different demos
            if positions_df is not None and 'match_file' in positions_df.columns:
                round_positions = positions_df[(positions_df['round_num'] == round_num) & (positions_df['match_file'] == match_file)]
            else:
                round_positions = positions_df[positions_df['round_num'] == round_num] if positions_df is not None else None
            
            if utility_df is not None and 'match_file' in utility_df.columns:
                round_utility = utility_df[(utility_df['round_num'] == round_num) & (utility_df['match_file'] == match_file)]
            else:
                round_utility = utility_df[utility_df['round_num'] == round_num] if utility_df is not None else None
            
            if kills_df is not None and 'match_file' in kills_df.columns:
                round_kills = kills_df[(kills_df['round_num'] == round_num) & (kills_df['match_file'] == match_file)]
            else:
                round_kills = kills_df[kills_df['round_num'] == round_num] if kills_df is not None else None
        else:
            round_mask = rounds_df['round_num'] == round_num
            round_positions = positions_df[positions_df['round_num'] == round_num] if positions_df is not None else None
            round_utility = utility_df[utility_df['round_num'] == round_num] if utility_df is not None else None
            round_kills = kills_df[kills_df['round_num'] == round_num] if kills_df is not None else None
            
        features = extract_strategy_features(
            round_num,
            rounds_df[round_mask],
            round_positions,
            round_utility,
            round_kills,
            team_players,
            side,  # Pass side to filter player actions
            map_bounds  # Pass global map bounds for consistent grid
        )
        if features:
            # Add match_file to features to maintain uniqueness
            if match_file:
                features['match_file'] = match_file
            features_list.append(features)
    
    if not features_list:
        return pd.DataFrame()
    
    from pprint import pprint
    if features_list:
        print("Feature columns:", list(features_list[0].keys()))
    
    return pd.DataFrame(features_list)
