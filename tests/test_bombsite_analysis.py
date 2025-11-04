"""
Test suite for bombsite hit analysis functionality
"""

from src.batch import process_demos_batch
from src.analysis import analyze_bombsite_hits, print_bombsite_analysis


def test_bombsite_analysis(result=None):
    """Test bombsite hit analysis"""
    print("\n" + "=" * 60)
    print("TEST: Bombsite Hit Analysis")
    print("=" * 60)
    
    if result is None:
        result = process_demos_batch('demos', validate_map=True)
    
    rounds_df = result['rounds']
    analysis = analyze_bombsite_hits(rounds_df)
    
    assert 'error' not in analysis, "Analysis should succeed"
    assert analysis['total_t_rounds'] > 0, "Should have T-side rounds"
    
    print_bombsite_analysis(analysis)
    
    print("\n[PASS] Bombsite analysis test")


if __name__ == "__main__":
    test_bombsite_analysis()

