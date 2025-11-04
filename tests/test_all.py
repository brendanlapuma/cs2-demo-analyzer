"""
Comprehensive test suite for CS2 Demo Analyzer

Run with: python -m tests.test_all

This module imports and runs all individual test modules.
"""

from tests.test_team_identification import test_team_identification
from tests.test_side_determination import test_side_determination
from tests.test_batch_processing import test_batch_processing
from tests.test_bombsite_analysis import test_bombsite_analysis


def main():
    """Run all tests"""
    print("=" * 60)
    print("CS2 Demo Analyzer - Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Team identification
        team_info = test_team_identification()
        
        # Test 2: Side determination
        test_side_determination(team_info)
        
        # Test 3: Batch processing (pass team_players to avoid re-identification)
        result = test_batch_processing(team_players=team_info['team_players'])
        
        # Test 4: Bombsite analysis
        test_bombsite_analysis(result)
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[FAIL] Test assertion failed: {e}")
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

