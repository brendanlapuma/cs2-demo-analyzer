"""
CS2 Demo Analyzer - Data Extraction Module

This package contains functions for extracting specific data from CS2 demo files.
All extractor functions are re-exported here for backwards compatibility.
"""

from src.extractors.rounds import extract_round_data
from src.extractors.utility import extract_utility_data
from src.extractors.positions import extract_player_positions
from src.extractors.kills import extract_kill_events

__all__ = [
    'extract_round_data',
    'extract_utility_data',
    'extract_player_positions',
    'extract_kill_events'
]

