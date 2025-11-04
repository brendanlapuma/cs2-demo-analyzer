"""
Test suite for batch processing functionality
"""

from src.batch import process_demos_batch


def test_batch_processing(team_players=None):
    """Test batch processing functionality
    
    Args:
        team_players: Optional set of team players to avoid re-identification
    """
    print("\n" + "=" * 60)
    print("TEST: Batch Processing")
    print("=" * 60)
    
    result = process_demos_batch('demos', validate_map=True, team_players=team_players)
    
    assert result['rounds'] is not None and not result['rounds'].empty, "Should extract rounds"
    
    rounds_df = result['rounds']
    print(f"\nExtracted {len(rounds_df)} rounds")
    print(f"T-side: {len(rounds_df[rounds_df['side'] == 'T'])}")
    print(f"CT-side: {len(rounds_df[rounds_df['side'] == 'CT'])}")
    
    print("\n[PASS] Batch processing test")
    return result


if __name__ == "__main__":
    test_batch_processing()

