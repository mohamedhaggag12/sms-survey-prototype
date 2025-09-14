#!/usr/bin/env python3
"""
Test script to verify SMS response parsing functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the parsing function from app.py
from app import parse_survey_response

def test_parsing():
    """Test various SMS response formats"""
    
    test_cases = [
        {
            "input": "8 7 9 Had a really productive day at work and felt accomplished",
            "expected": (8, 7, 9, "Had a really productive day at work and felt accomplished")
        },
        {
            "input": "5 6 4 Feeling a bit down today, work was stressful",
            "expected": (5, 6, 4, "Feeling a bit down today work was stressful")
        },
        {
            "input": "10 9 8 Amazing day! Got promoted and spent time with family",
            "expected": (10, 9, 8, "Amazing day Got promoted and spent time with family")
        },
        {
            "input": "7,8,6 Good day overall",
            "expected": (7, 8, 6, "Good day overall")
        },
        {
            "input": "3 2 1",
            "expected": (3, 2, 1, "")
        },
        {
            "input": "Not a valid response",
            "expected": (None, None, None, None)
        },
        {
            "input": "8 7 Had only two numbers",
            "expected": (None, None, None, None)
        },
        {
            "input": "11 12 13 Numbers too high",
            "expected": (None, None, None, None)
        }
    ]
    
    print("🧪 Testing SMS Response Parsing")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        input_text = test["input"]
        expected = test["expected"]
        
        result = parse_survey_response(input_text)
        
        print(f"\nTest {i}: {input_text}")
        print(f"Expected: {expected}")
        print(f"Got:      {result}")
        
        if result == expected:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Response parsing is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the parsing logic.")

if __name__ == "__main__":
    test_parsing()
