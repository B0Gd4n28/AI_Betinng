# Test bot functionality without starting the actual bot
import sys
import os
from pathlib import Path

# Add the project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    
    try:
        from src.i18n import tr
        print("✅ i18n imported")
        
        from src.utils.leagues import TOP_N_FOR_UI, TOP_COMP_CODES
        print(f"✅ leagues imported, TOP_N_FOR_UI={TOP_N_FOR_UI}")
        
        from src.analytics.markets import seeded_shuffle_picks, top_market_picks_for_date
        print("✅ markets analytics imported")
        
        from src.ai.features_markets import extract_h2h_features
        print("✅ AI features imported")
        
        from src.fetchers.odds_api import parse_totals_prob, parse_btts_prob
        print("✅ enhanced odds API imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_translations():
    """Test new translation keys"""
    print("\n🌐 Testing translations...")
    
    try:
        from src.i18n import tr
        
        # Test new keys for all languages
        for lang in ["RO", "EN", "RU"]:
            app_name = tr(lang, "app_name")
            welcome_title = tr(lang, "welcome_title", emoji="🤖")
            markets_header = tr(lang, "markets_header", date="2025-09-25")
            
            print(f"✅ {lang}: {app_name}, welcome works, markets header works")
        
        return True
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

def test_markets_functionality():
    """Test markets module functionality"""
    print("\n📊 Testing markets functionality...")
    
    try:
        from src.analytics.markets import seeded_shuffle_picks, compute_parlay_metrics
        
        # Test user diversification
        sample_picks = [
            {"match": "Team A vs Team B", "p_est": 0.7, "odds": 1.5, "ev": 0.05},
            {"match": "Team C vs Team D", "p_est": 0.6, "odds": 1.8, "ev": 0.08},
            {"match": "Team E vs Team F", "p_est": 0.8, "odds": 1.3, "ev": 0.04},
        ]
        
        user1_picks = seeded_shuffle_picks(sample_picks, user_id=123, date_str="2025-09-25", take_n=2)
        user2_picks = seeded_shuffle_picks(sample_picks, user_id=456, date_str="2025-09-25", take_n=2)
        
        print(f"✅ User diversification: User1 got {len(user1_picks)} picks, User2 got {len(user2_picks)} picks")
        
        # Test parlay metrics
        sample_legs = [
            {"p_est": 0.7, "odds": 1.5},
            {"p_est": 0.6, "odds": 1.8},
        ]
        
        metrics = compute_parlay_metrics(sample_legs)
        print(f"✅ Parlay metrics: prob={metrics['combined_prob']}, odds={metrics['combined_odds']}, ev={metrics['ev']}")
        
        return True
    except Exception as e:
        print(f"❌ Markets test failed: {e}")
        return False

def test_ai_features():
    """Test AI features module"""
    print("\n🤖 Testing AI features...")
    
    try:
        from src.ai.features_markets import extract_h2h_features, create_feature_vector
        
        # Test feature extraction
        features = extract_h2h_features(event=None, home_form=2.1, away_form=1.8)
        
        print(f"✅ H2H features extracted: {len(features)} features")
        
        # Test feature vector creation
        vector = create_feature_vector(features)
        print(f"✅ Feature vector created: {len(vector)} dimensions")
        
        return True
    except Exception as e:
        print(f"❌ AI features test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing PariuSmart AI Bot Enhancements")
    print("=" * 50)
    
    all_tests_passed = True
    
    all_tests_passed &= test_imports()
    all_tests_passed &= test_translations()
    all_tests_passed &= test_markets_functionality()
    all_tests_passed &= test_ai_features()
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests PASSED! The bot enhancements are ready.")
        print("\n📋 Summary of new features:")
        print("• 🎯 Enhanced /today with top 2 picks + user diversification")
        print("• 📊 New /markets command for O/U 2.5 & BTTS")
        print("• 🚀 Rich welcome message with animation support")
        print("• ⚡ Improved /express with detailed leg metrics")
        print("• 🤖 AI scaffold for future ML model integration")
        print("• 🌐 Complete i18n support (RO/EN/RU)")
    else:
        print("❌ Some tests FAILED. Check the errors above.")
        sys.exit(1)