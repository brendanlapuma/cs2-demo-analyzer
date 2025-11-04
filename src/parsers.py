"""
CS2 Demo Analyzer - Basic Demo Parsing Utilities

This module contains functions for basic demo file parsing and information extraction.
"""

import os

try:
    from awpy import Demo
except ImportError as e:
    print(f"Error: awpy library not found: {e}")
    print("Please install with: pip install -r requirements.txt")
    raise


def parse_demo_basic(demo_path: str):
    """
    Parse a CS2 demo file and extract basic match information.
    
    Args:
        demo_path: Path to the .dem file
        
    Returns:
        Dictionary with basic match information or None if parsing fails
    """
    if not os.path.exists(demo_path):
        print(f"Error: Demo file not found: {demo_path}")
        return None
    
    try:
        # Create Demo object and parse
        demo = Demo(demo_path)
        
        # Parse header to get map name
        demo.parse_header()
        map_name = demo.header.get('map_name', 'Unknown') if hasattr(demo, 'header') and demo.header else 'Unknown'
        
        # Parse full demo to get events
        demo.parse()
        
        # Count rounds by counting round_end events (events are Polars DataFrames)
        total_rounds = 0
        if hasattr(demo, 'events') and isinstance(demo.events, dict):
            # Count round_end events (most accurate for complete rounds)
            if 'round_end' in demo.events:
                round_end_df = demo.events['round_end']
                # Check if it's a Polars DataFrame (has shape attribute)
                if hasattr(round_end_df, 'shape'):
                    total_rounds = round_end_df.shape[0]
                elif isinstance(round_end_df, list):
                    total_rounds = len(round_end_df)
            # Also check round_officially_ended as alternative
            if total_rounds == 0 and 'round_officially_ended' in demo.events:
                round_officially_ended_df = demo.events['round_officially_ended']
                if hasattr(round_officially_ended_df, 'shape'):
                    total_rounds = round_officially_ended_df.shape[0]
                elif isinstance(round_officially_ended_df, list):
                    total_rounds = len(round_officially_ended_df)
        
        # Extract basic information
        info = {
            'file': os.path.basename(demo_path),
            'map': map_name,
            'total_rounds': total_rounds,
            'ct_team': None,
            't_team': None,
        }
        
        # Try to extract server/team info from header
        if hasattr(demo, 'header') and demo.header:
            server_name = demo.header.get('server_name', '')
            info['server'] = server_name
        
        return info
        
    except Exception as e:
        print(f"Error parsing demo {demo_path}: {str(e)}")
        return None

