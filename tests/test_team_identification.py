"""
Test suite for team identification functionality
"""

from src.team_identification import identify_team_from_demos


def test_team_identification():
    """Test team identification functionality"""
    print("\n" + "=" * 60)
    print("TEST: Team Identification")
    print("=" * 60)
    
    team_info = identify_team_from_demos("demos", min_players=4)
    
    print(f"\nIdentified Team: {team_info['team_name']}")
    print(f"Team Players ({len(team_info['team_players'])}):")
    for player in sorted(team_info['team_players']):
        print(f"  - {player}")
    print(f"Analyzed {team_info['demo_count']} demo(s)")
    
    assert len(team_info['team_players']) >= 4, "Should identify at least 4 players"
    print("\n[PASS] Team identification test")
    return team_info


if __name__ == "__main__":
    test_team_identification()

