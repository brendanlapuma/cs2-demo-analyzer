"""
Strategy Discovery Module

This package contains tools for discovering and analyzing team strategies
using unsupervised machine learning techniques.

Main components:
- features: Extract strategic features from round data
- clustering: Discover strategy patterns using DBSCAN
- analysis: Analyze discovered strategies and generate reports
- visualization: Visualize strategy clusters and patterns
"""

from .features import extract_strategy_features, build_feature_matrix
from .clustering import discover_strategies, cluster_strategies
from .analysis import analyze_strategy_clusters, generate_strategy_report
from .visualization import plot_strategy_clusters, plot_feature_importance, plot_cluster_statistics

__all__ = [
    'extract_strategy_features',
    'build_feature_matrix',
    'discover_strategies',
    'cluster_strategies',
    'analyze_strategy_clusters',
    'generate_strategy_report',
    'plot_strategy_clusters',
    'plot_feature_importance',
    'plot_cluster_statistics',
]
