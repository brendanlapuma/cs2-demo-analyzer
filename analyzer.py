"""
CS2 Demo Analyzer
Main entry point for the CS2 demo analysis tool.
"""

import sys
from pathlib import Path

# Import from our modular structure
from src.parsers import parse_demo_basic
from src.extractors import extract_round_data, extract_utility_data, extract_player_positions, extract_kill_events


def main():
    """Main function to test demo parsing."""
    print("CS2 Demo Analyzer - Basic Parsing Test")
    print("=" * 50)
    
    # Check for demo files in demos folder
    demos_folder = Path("demos/inferno")
    
    if not demos_folder.exists():
        print(f"Warning: {demos_folder} folder does not exist")
        print("Creating demos folder...")
        demos_folder.mkdir(exist_ok=True)
    
    # Look for .dem files
    demo_files = list(demos_folder.glob("*.dem"))
    
    if not demo_files:
        print(f"\nNo .dem files found in {demos_folder}/")
        print("To test parsing, please:")
        print("1. Download a CS2 demo file (.dem)")
        print("2. Place it in the 'demos' folder")
        print("3. Run this script again")
        print("\nYou can download demos from:")
        print("- HLTV.org (pro matches)")
        print("- Your own CS2 matches (replay system)")
        print("- Third-party platforms (FACEIT, etc.)")
        return
    
    print(f"\nFound {len(demo_files)} demo file(s):")
    for demo_file in demo_files:
        print(f"  - {demo_file.name}")
    
    # Try to parse the first demo
    print(f"\nAttempting to parse: {demo_files[0].name}")
    info = parse_demo_basic(str(demo_files[0]))
    
    if info:
        print("\n[SUCCESS] Demo parsed successfully!")
        print("\nMatch Information:")
        print(f"  File: {info['file']}")
        print(f"  Map: {info['map']}")
        print(f"  Total Rounds: {info['total_rounds']}")
        if info.get('server'):
            print(f"  Server: {info['server']}")
        if info.get('ct_team'):
            print(f"  CT Team: {info['ct_team']}")
        if info.get('t_team'):
            print(f"  T Team: {info['t_team']}")
        
        # Test round data extraction
        print("\n" + "=" * 50)
        print("Testing Round Data Extraction (Task 2.1)")
        print("=" * 50)
        rounds_df = extract_round_data(str(demo_files[0]))
        
        if rounds_df is not None and not rounds_df.empty:
            print(f"\n[SUCCESS] Extracted {len(rounds_df)} rounds")
            print("\nFirst 5 rounds:")
            print(rounds_df.head().to_string())
            print(f"\nPistol rounds: {rounds_df['is_pistol'].sum()}")
            print(f"Rounds with bomb plants: {(rounds_df['bombsite'] != 'not_planted').sum()}")
        else:
            print("\n[WARNING] No round data extracted")
        
        # Test utility data extraction
        print("\n" + "=" * 50)
        print("Testing Utility Data Extraction (Task 2.2)")
        print("=" * 50)
        utility_df = extract_utility_data(str(demo_files[0]))
        
        if utility_df is not None and not utility_df.empty:
            print(f"\n[SUCCESS] Extracted {len(utility_df)} utility events")
            print("\nGrenade type distribution:")
            print(utility_df['grenade_type'].value_counts().to_string())
            print("\nFirst 5 utility events:")
            print(utility_df[['grenade_type', 'thrower_name', 'thrower_side', 'round_num', 'time_into_round']].head().to_string())
            print(f"\nUtility events with coordinates: {(utility_df[['x', 'y', 'z']].notna().all(axis=1)).sum()}")
        else:
            print("\n[WARNING] No utility data extracted")
        
        # Test player position data extraction
        print("\n" + "=" * 50)
        print("Testing Player Position Data Extraction (Task 2.3)")
        print("=" * 50)
        positions_df = extract_player_positions(str(demo_files[0]), sample_interval=10)
        
        if positions_df is not None and not positions_df.empty:
            print(f"\n[SUCCESS] Extracted {len(positions_df)} position records")
            print("\nPhase distribution:")
            print(positions_df['phase'].value_counts().to_string())
            print("\nFirst 5 position records:")
            print(positions_df[['player_name', 'player_side', 'round_num', 'phase', 'time_into_round']].head().to_string())
            print(f"\nPosition records with coordinates: {(positions_df[['x', 'y', 'z']].notna().all(axis=1)).sum()}")
            print(f"Unique players: {positions_df['player_name'].nunique()}")
        else:
            print("\n[WARNING] No position data extracted")
        
        # Test kill event data extraction
        print("\n" + "=" * 50)
        print("Testing Kill Event Data Extraction (Task 2.4)")
        print("=" * 50)
        kills_df = extract_kill_events(str(demo_files[0]))
        
        if kills_df is not None and not kills_df.empty:
            print(f"\n[SUCCESS] Extracted {len(kills_df)} kill events")
            print("\nEntry frags: {} ({:.1f}%)".format(
                kills_df['is_entry_frag'].sum(),
                (kills_df['is_entry_frag'].sum() / len(kills_df)) * 100
            ))
            print("\nHeadshots: {} ({:.1f}%)".format(
                kills_df['headshot'].sum(),
                (kills_df['headshot'].sum() / len(kills_df)) * 100
            ))
            print("\nFirst 5 kill events:")
            print(kills_df[['attacker_name', 'victim_name', 'weapon', 'round_num', 'time_into_round', 'is_entry_frag', 'headshot']].head().to_string())
            print(f"\nKill events with coordinates: {(kills_df[['x', 'y', 'z']].notna().all(axis=1)).sum()}")
        else:
            print("\n[WARNING] No kill event data extracted")
    else:
        print("\n[ERROR] Failed to parse demo file")
        print("\nTroubleshooting:")
        print("- Ensure the file is a valid CS2 (.dem) demo file")
        print("- Check that awpy library is installed correctly")
        print("- Verify the demo file is not corrupted")


if __name__ == "__main__":
    main()
