"""
Test suite for side determination functionality
"""

from pathlib import Path
from awpy import Demo
from src.team_identification import identify_team_from_demos, determine_team_side_for_round


def test_side_determination(team_info=None):
    """Test side determination for rounds"""
    print("\n" + "=" * 60)
    print("TEST: Side Determination")
    print("=" * 60)
    
    if team_info is None:
        team_info = identify_team_from_demos("demos", min_players=4)
    
    demo_files = sorted(Path("demos").glob("*.dem"))
    if not demo_files:
        print("No demo files found")
        return
    
    demo = Demo(str(demo_files[0]))
    demo.parse_header()
    demo.parse(player_props=['X', 'Y', 'Z'])
    
    print(f"Testing: {demo_files[0].name}")
    print(f"Map: {demo.header.get('map_name', 'Unknown')}")
    
    rounds_df = demo.rounds.to_pandas()
    
    t_rounds = 0
    ct_rounds = 0
    
    for _, round_row in rounds_df.iterrows():
        round_num = round_row['round_num']
        team_side = determine_team_side_for_round(demo, round_num, team_info['team_players'])
        
        if team_side == 'T':
            t_rounds += 1
        elif team_side == 'CT':
            ct_rounds += 1
    
    print(f"\nT-side rounds: {t_rounds}")
    print(f"CT-side rounds: {ct_rounds}")
    print(f"Total rounds: {len(rounds_df)}")
    
    assert t_rounds > 0 and ct_rounds > 0, "Should have both T and CT rounds"
    print("\n[PASS] Side determination test")
    
    del demo


if __name__ == "__main__":
    test_side_determination()

