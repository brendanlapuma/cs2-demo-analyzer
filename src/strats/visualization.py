"""
Strategy Visualization Module

Visualizes discovered strategy clusters using dimensionality reduction.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from pathlib import Path
from typing import Optional, Tuple


def plot_strategy_clusters(feature_matrix: np.ndarray,
                           labels: np.ndarray,
                           rounds_df: pd.DataFrame,
                           method: str = 'pca',
                           output_path: Optional[Path] = None,
                           side: str = 'T',
                           title_suffix: str = '') -> Tuple[plt.Figure, plt.Axes]:
    """
    Visualize strategy clusters in 2D using dimensionality reduction.
    
    Args:
        feature_matrix: Feature matrix (samples x features)
        labels: Cluster labels for each sample
        rounds_df: DataFrame with round information (for coloring by win/loss)
        method: Dimensionality reduction method ('pca' or 'tsne')
        output_path: Path to save the plot (optional)
        side: Side being analyzed ('T' or 'CT')
        title_suffix: Additional text for the title
        
    Returns:
        Tuple of (figure, axes) objects
    """
    # Verify dimensions match
    if len(rounds_df) != len(feature_matrix):
        raise ValueError(f"Dimension mismatch: rounds_df has {len(rounds_df)} rows "
                        f"but feature_matrix has {len(feature_matrix)} rows")
    
    if len(labels) != len(feature_matrix):
        raise ValueError(f"Dimension mismatch: labels has {len(labels)} elements "
                        f"but feature_matrix has {len(feature_matrix)} rows")
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(feature_matrix)
    
    # Reduce to 2D
    if method.lower() == 'tsne':
        reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(feature_matrix) - 1))
        features_2d = reducer.fit_transform(features_scaled)
        method_name = 't-SNE'
    else:  # pca
        reducer = PCA(n_components=2, random_state=42)
        features_2d = reducer.fit_transform(features_scaled)
        method_name = 'PCA'
        explained_var = reducer.explained_variance_ratio_
        print(f"PCA explained variance: {explained_var[0]:.2%} (PC1), {explained_var[1]:.2%} (PC2), Total: {sum(explained_var):.2%}")
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Color by cluster
    ax1 = axes[0]
    unique_labels = np.unique(labels)
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))
    
    for label, color in zip(unique_labels, colors):
        if label == -1:
            # Noise points (unclustered)
            mask = labels == label
            ax1.scatter(features_2d[mask, 0], features_2d[mask, 1],
                       c='gray', marker='x', s=100, alpha=0.6,
                       label='Unclustered', edgecolors='black', linewidths=1)
        else:
            mask = labels == label
            ax1.scatter(features_2d[mask, 0], features_2d[mask, 1],
                       c=[color], marker='o', s=150, alpha=0.7,
                       label=f'Strategy_{label}', edgecolors='black', linewidths=1)
    
    ax1.set_xlabel(f'{method_name} Component 1', fontsize=12)
    ax1.set_ylabel(f'{method_name} Component 2', fontsize=12)
    ax1.set_title(f'Strategy Clusters - {side} Side{title_suffix}\nColored by Cluster', fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Color by win/loss
    ax2 = axes[1]
    
    # Get win/loss information
    wins = rounds_df['winner'].values == side
    
    # Plot losses first (so wins appear on top)
    loss_mask = ~wins
    if loss_mask.any():
        ax2.scatter(features_2d[loss_mask, 0], features_2d[loss_mask, 1],
                   c='red', marker='o', s=150, alpha=0.6,
                   label='Loss', edgecolors='darkred', linewidths=1)
    
    # Plot wins
    win_mask = wins
    if win_mask.any():
        ax2.scatter(features_2d[win_mask, 0], features_2d[win_mask, 1],
                   c='green', marker='o', s=150, alpha=0.7,
                   label='Win', edgecolors='darkgreen', linewidths=1)
    
    # Overlay cluster boundaries with light lines
    for label in unique_labels:
        if label != -1:
            mask = labels == label
            if mask.sum() > 1:
                from matplotlib.patches import Ellipse
                from scipy.stats import chi2
                
                points = features_2d[mask]
                mean = points.mean(axis=0)
                cov = np.cov(points.T)
                
                # Calculate eigenvalues and eigenvectors
                eigenvalues, eigenvectors = np.linalg.eigh(cov)
                order = eigenvalues.argsort()[::-1]
                eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
                
                # Calculate ellipse parameters (2 standard deviations)
                theta = np.degrees(np.arctan2(*eigenvectors[:, 0][::-1]))
                width, height = 2 * np.sqrt(eigenvalues) * 2  # 2 std devs
                
                ellipse = Ellipse(xy=mean, width=width, height=height,
                                angle=theta, facecolor='none',
                                edgecolor='blue', linewidth=2, linestyle='--', alpha=0.5)
                ax2.add_patch(ellipse)
    
    ax2.set_xlabel(f'{method_name} Component 1', fontsize=12)
    ax2.set_ylabel(f'{method_name} Component 2', fontsize=12)
    ax2.set_title(f'Strategy Clusters - {side} Side{title_suffix}\nColored by Outcome', fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save if path provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved cluster visualization: {output_path}")
    
    return fig, axes


def plot_feature_importance(feature_matrix: np.ndarray,
                            feature_names: list,
                            labels: np.ndarray,
                            output_path: Optional[Path] = None,
                            top_n: int = 15) -> plt.Figure:
    """
    Plot feature importance for distinguishing clusters using PCA loadings.
    
    Args:
        feature_matrix: Feature matrix (samples x features)
        feature_names: Names of features
        labels: Cluster labels
        output_path: Path to save the plot (optional)
        top_n: Number of top features to display
        
    Returns:
        Figure object
    """
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(feature_matrix)
    
    # Fit PCA
    pca = PCA(n_components=min(10, len(feature_names)))
    pca.fit(features_scaled)
    
    # Get loadings (components)
    loadings = pca.components_
    
    # Calculate feature importance as sum of absolute loadings weighted by explained variance
    feature_importance = np.abs(loadings).T @ pca.explained_variance_ratio_[:len(loadings)]
    
    # Get top features
    top_indices = np.argsort(feature_importance)[-top_n:]
    top_features = [feature_names[i] for i in top_indices]
    top_importance = feature_importance[top_indices]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))
    y_pos = np.arange(len(top_features))
    
    bars = ax.barh(y_pos, top_importance, color='steelblue', alpha=0.8, edgecolor='black')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_features)
    ax.set_xlabel('Feature Importance (PCA-weighted)', fontsize=12)
    ax.set_title(f'Top {top_n} Features for Strategy Differentiation', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, top_importance)):
        ax.text(val, i, f' {val:.3f}', va='center', fontsize=9)
    
    plt.tight_layout()
    
    # Save if path provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved feature importance plot: {output_path}")
    
    return fig


def plot_cluster_statistics(rounds_df: pd.DataFrame,
                            side: str,
                            output_path: Optional[Path] = None) -> plt.Figure:
    """
    Plot statistics about discovered clusters.
    
    Args:
        rounds_df: DataFrame with rounds and strategy_cluster labels
        side: Side being analyzed
        output_path: Path to save the plot
        
    Returns:
        Figure object
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Get cluster information
    clusters = rounds_df['strategy_cluster'].unique()
    clusters = sorted([c for c in clusters if c != -1])
    all_clusters = clusters + [-1]  # Add noise at the end
    
    # Prepare data
    cluster_labels = [f'Strategy_{c}' if c != -1 else 'Unclustered' for c in all_clusters]
    cluster_counts = [len(rounds_df[rounds_df['strategy_cluster'] == c]) for c in all_clusters]
    cluster_wins = [(rounds_df[rounds_df['strategy_cluster'] == c]['winner'] == side).sum() 
                   for c in all_clusters]
    cluster_win_rates = [(w / c * 100) if c > 0 else 0 
                        for w, c in zip(cluster_wins, cluster_counts)]
    
    # Plot 1: Cluster sizes
    ax1 = axes[0, 0]
    colors = ['steelblue' if c != -1 else 'gray' for c in all_clusters]
    bars1 = ax1.bar(cluster_labels, cluster_counts, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Number of Rounds', fontsize=11)
    ax1.set_title('Cluster Sizes', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    for bar, count in zip(bars1, cluster_counts):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontsize=10)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 2: Win rates
    ax2 = axes[0, 1]
    colors2 = ['green' if wr >= 50 else 'red' for wr in cluster_win_rates]
    bars2 = ax2.bar(cluster_labels, cluster_win_rates, color=colors2, alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Win Rate (%)', fontsize=11)
    ax2.set_title('Win Rates by Cluster', fontsize=12, fontweight='bold')
    ax2.axhline(y=50, color='black', linestyle='--', linewidth=1, alpha=0.5, label='50%')
    ax2.grid(axis='y', alpha=0.3)
    ax2.legend()
    for bar, wr in zip(bars2, cluster_win_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{wr:.1f}%', ha='center', va='bottom', fontsize=10)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 3: Bombsite distribution per cluster
    ax3 = axes[1, 0]
    bombsite_data = []
    for cluster in all_clusters:
        cluster_rounds = rounds_df[rounds_df['strategy_cluster'] == cluster]
        bombsites = cluster_rounds['bombsite'].value_counts()
        bombsite_data.append(bombsites)
    
    # Stack bar chart for bombsites
    all_bombsites = set()
    for bs_counts in bombsite_data:
        all_bombsites.update(bs_counts.index)
    all_bombsites = sorted(all_bombsites)
    
    x = np.arange(len(cluster_labels))
    width = 0.6
    bottom = np.zeros(len(cluster_labels))
    
    site_colors = {'bombsite_a': '#ff7f0e', 'bombsite_b': '#2ca02c', 
                  'not_planted': '#d62728', 'unknown': '#9467bd'}
    
    for bombsite in all_bombsites:
        heights = [bombsite_data[i].get(bombsite, 0) for i in range(len(all_clusters))]
        ax3.bar(x, heights, width, bottom=bottom, label=bombsite,
               color=site_colors.get(bombsite, 'gray'), alpha=0.8, edgecolor='black')
        bottom += heights
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(cluster_labels)
    ax3.set_ylabel('Number of Rounds', fontsize=11)
    ax3.set_title('Bombsite Distribution by Cluster', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(axis='y', alpha=0.3)
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 4: Strategy usage frequency by round number (aggregated across all matches)
    ax4 = axes[1, 1]
    
    # Calculate max round number to set x-axis
    max_round = rounds_df['round_num'].max()
    
    # For each cluster, count how many times it was used in each round number
    for cluster in all_clusters:
        cluster_rounds = rounds_df[rounds_df['strategy_cluster'] == cluster]
        # Count occurrences of each round number
        round_counts = cluster_rounds['round_num'].value_counts().sort_index()
        
        cluster_label = f'Strategy_{cluster}' if cluster != -1 else 'Unclustered'
        color = 'gray' if cluster == -1 else None
        
        # Plot as a line with markers showing the count for each round
        ax4.plot(round_counts.index, round_counts.values, 
                marker='o', label=cluster_label, alpha=0.7, 
                linewidth=2, markersize=6, color=color)
    
    ax4.set_xlabel('Round Number', fontsize=11)
    ax4.set_ylabel('Times Used', fontsize=11)
    ax4.set_title('Strategy Usage by Round Number\n(Aggregated Across All Matches)', fontsize=12, fontweight='bold')
    ax4.grid(alpha=0.3)
    ax4.legend(loc='best', fontsize=9)
    ax4.set_xlim(0, max_round + 1)
    
    plt.suptitle(f'{side}-Side Strategy Analysis', fontsize=16, fontweight='bold', y=1.00)
    plt.tight_layout()
    
    # Save if path provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved cluster statistics plot: {output_path}")
    
    return fig
