"""
Strategy Clustering Module

Uses DBSCAN clustering to discover strategic patterns from feature data.
Supports both map-wide analysis and team-specific analysis.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import Dict, Optional, Set, Tuple


def cluster_strategies(features_df: pd.DataFrame,
                      eps: float = 0.5,
                      min_samples: int = 2,
                      exclude_cols: Optional[list] = None) -> Tuple[np.ndarray, StandardScaler]:
    """
    Cluster rounds into strategic patterns using DBSCAN.
    
    Args:
        features_df: DataFrame with feature vectors for each round
        eps: DBSCAN epsilon parameter (max distance between samples)
        min_samples: Minimum samples in a neighborhood for a core point
        exclude_cols: Columns to exclude from clustering (e.g., 'round_num', 'won')
        
    Returns:
        Tuple of (cluster labels, fitted scaler)
    """
    if features_df.empty:
        return np.array([]), StandardScaler()
    
    # Columns to exclude from clustering
    if exclude_cols is None:
        exclude_cols = ['round_num', 'won', 'bombsite', 'match_file']
    
    # Select feature columns for clustering
    feature_cols = [col for col in features_df.columns if col not in exclude_cols]
    
    if not feature_cols:
        return np.array([-1] * len(features_df)), StandardScaler()
    
    # Extract feature matrix
    X = features_df[feature_cols].values
    
    # Handle NaN/inf values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # DBSCAN clustering
    clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
    clusters = clusterer.fit_predict(X_scaled)
    
    return clusters, scaler


def discover_strategies(rounds_df: pd.DataFrame,
                       positions_df: Optional[pd.DataFrame] = None,
                       utility_df: Optional[pd.DataFrame] = None,
                       kills_df: Optional[pd.DataFrame] = None,
                       side: str = 'T',
                       team_players: Optional[Set[str]] = None,
                       eps: float = 0.5,
                       min_samples: int = 2) -> Tuple[pd.DataFrame, Dict]:
    """
    Discover strategic patterns for a specific side.
    
    Args:
        rounds_df: DataFrame with round data
        positions_df: DataFrame with player positions (optional)
        utility_df: DataFrame with utility events (optional)
        kills_df: DataFrame with kill events (optional)
        side: Side to analyze ('T' or 'CT')
        team_players: Set of player names for team-specific analysis (optional)
        eps: DBSCAN epsilon parameter
        min_samples: Minimum samples per cluster
        
    Returns:
        Tuple of (rounds_df with strategy labels, clustering metadata)
    """
    from .features import build_feature_matrix
    
    # Build feature matrix
    features_df = build_feature_matrix(
        rounds_df,
        positions_df,
        utility_df,
        kills_df,
        side=side,
        team_players=team_players
    )
    
    if features_df.empty:
        return rounds_df, {
            'error': f'No {side}-side rounds found',
            'num_strategies': 0
        }
    
    # Cluster strategies
    clusters, scaler = cluster_strategies(features_df, eps=eps, min_samples=min_samples)
    
    # Add cluster labels to features
    features_df['strategy_cluster'] = clusters
    
    # Merge cluster labels back to rounds_df using both round_num and match_file for uniqueness
    rounds_with_clusters = rounds_df.copy()
    rounds_with_clusters['strategy_cluster'] = pd.NA
    
    # Map clusters back using both round_num and match_file to handle multiple demos
    if 'match_file' in features_df.columns and 'match_file' in rounds_with_clusters.columns:
        # Create unique mapping using both round_num and match_file
        for idx, row in features_df.iterrows():
            mask = (rounds_with_clusters['round_num'] == row['round_num']) & \
                   (rounds_with_clusters['match_file'] == row['match_file'])
            rounds_with_clusters.loc[mask, 'strategy_cluster'] = row['strategy_cluster']
    else:
        # Fallback: use round_num only (works for single demo)
        round_to_cluster = dict(zip(features_df['round_num'], features_df['strategy_cluster']))
        rounds_with_clusters['strategy_cluster'] = rounds_with_clusters['round_num'].map(round_to_cluster)
    
    # Calculate clustering metadata
    unique_clusters = set(clusters)
    num_strategies = len([c for c in unique_clusters if c != -1])  # Exclude noise (-1)
    num_noise = sum(clusters == -1)
    
    # Get feature matrix and names (excluding non-feature columns)
    feature_cols = [col for col in features_df.columns 
                   if col not in ['round_num', 'won', 'strategy_cluster', 'bombsite', 'match_file']]
    feature_matrix = features_df[feature_cols].values
    
    # Get the rounds that were actually clustered (have labels)
    clustered_rounds = rounds_with_clusters[rounds_with_clusters['strategy_cluster'].notna()].copy()
    
    metadata = {
        'side': side,
        'num_rounds': len(features_df),
        'num_strategies': num_strategies,
        'num_noise': num_noise,
        'team_specific': team_players is not None,
        'eps': eps,
        'min_samples': min_samples,
        'features_used': feature_cols,
        'feature_matrix': feature_matrix,
        'feature_names': feature_cols,
        'labels': clusters,
        'clustered_rounds_df': clustered_rounds  # Only rounds that were clustered
    }
    
    return rounds_with_clusters, metadata


def auto_tune_dbscan(features_df: pd.DataFrame,
                     eps_range: tuple = (0.3, 1.0),
                     min_samples_range: tuple = (2, 5),
                     target_clusters: int = 5) -> Tuple[float, int]:
    """
    Automatically tune DBSCAN parameters to find reasonable number of clusters.
    
    Args:
        features_df: DataFrame with feature vectors
        eps_range: Range of epsilon values to try (min, max)
        min_samples_range: Range of min_samples values to try (min, max)
        target_clusters: Desired number of clusters (will try to get close)
        
    Returns:
        Tuple of (best_eps, best_min_samples)
    """
    if features_df.empty:
        return 0.5, 2
    
    best_eps = eps_range[0]
    best_min_samples = min_samples_range[0]
    best_score = float('inf')
    
    # Try different parameter combinations
    eps_values = np.linspace(eps_range[0], eps_range[1], 5)
    min_samples_values = range(min_samples_range[0], min_samples_range[1] + 1)
    
    for eps in eps_values:
        for min_samples in min_samples_values:
            clusters, _ = cluster_strategies(features_df, eps=eps, min_samples=min_samples)
            
            unique_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
            
            # Score based on how close to target number of clusters
            score = abs(unique_clusters - target_clusters)
            
            if score < best_score:
                best_score = score
                best_eps = eps
                best_min_samples = min_samples
    
    return best_eps, best_min_samples
