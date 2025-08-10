# test_4d_health_check.py
"""
Complete 4D Logic Health Check
Tests the actual cascade through all 4 levels
"""

import json
import time
from recipe_matcher_4d import RecipeMatcher4D

def run_4d_health_check():
    """Test the complete 4D cascade logic"""
    
    print("=" * 70)
    print("4D CASCADE LOGIC HEALTH CHECK")
    print("=" * 70)
    print("\nTesting how recipes flow through the 4 levels:")
    print("Level 1: Country (exact match)")
    print("Level 2: Region (broader area)")
    print("Level 3: Sister Countries (cultural similarity)")
    print("Level 4: Fallback (A.I. Chef)")
    print("=" * 70)
    
    # Initialize the matcher
    matcher = RecipeMatcher4D()
    matcher.enable_video = False  # Set it as an attribute after initialization
    
    # Test cases designed to trigger each level
    test_cases = [
        # Should hit Level 1 (Local database - exact country match)
        {
            "name": "Mexican Chicken (Level 1)",
            "cuisine": "mexican",
            "dish_type": "any",
            "ingredients": ["chicken"],
            "expected_level": 1,
            "expected_behavior": "Should find instantly in local database"
        },
        
        # Should hit Level 2 (API search - country exists but not in local)
        {
            "name": "Thai Green Curry (Level 2)",
            "cuisine": "thai",
            "dish_type": "curry",
            "ingredients": ["coconut_milk", "chicken"],
            "expected_level": 2,
            "expected_behavior": "Should search APIs for Thai recipes"
        },
        
        # Should hit Level 3 (Sister country mapping)
        {
            "name": "Taiwanese Pork (Level 3)",
            "cuisine": "taiwanese",
            "dish_type": "any",
            "ingredients": ["pork"],
            "expected_level": 3,
            "expected_behavior": "Should map to Chinese (sister country)"
        },
        
        # Should hit Level 4 (A.I. Chef fallback)
        {
            "name": "Ethiopian Plantain Stir-Fry (Level 4)",
            "cuisine": "ethiopian",
            "dish_type": "stir-fry",
            "ingredients": ["plantain", "onions"],
            "expected_level": 4,
            "expected_behavior": "Should generate with A.I. Chef"
        },
        
        # Additional edge cases
        {
            "name": "Mongolian Pasta (Level 3 or 4)",
            "cuisine": "mongolian",
            "dish_type": "pasta",
            "ingredients": ["pasta", "beef"],
            "expected_level": 3,
            "expected_behavior": "Should try Asian sisters or fallback"
        },
        
        {
            "name": "French Baked Chicken (Level 1 or 2)",
            "cuisine": "french",
            "dish_type": "baked-dish",
            "ingredients": ["chicken", "potatoes"],
            "expected_level": 2,
            "expected_behavior": "Should find in database or API"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{len(test_cases)}] {test['name']}")
        print("-" * 50)
        print(f"Input: {test['cuisine']} {test['dish_type']} with {test['ingredients']}")
        print(f"Expected: {test['expected_behavior']}")
        
        start_time = time.time()
        
        # Run the actual 4D matcher
        recipe = matcher.find_recipe(
            cuisine=test['cuisine'],
            dish_type=test['dish_type'],
            ingredients=test['ingredients']
        )
        
        elapsed = time.time() - start_time
        
        # Determine which level actually handled it
        if recipe:
            actual_level = determine_level(recipe, elapsed)
            
            print(f"Result: Level {actual_level} - {recipe.get('title', 'Unknown')}")
            print(f"Time: {elapsed:.2f} seconds")
            
            success = actual_level == test['expected_level']
            status = "✅ PASS" if success else f"❌ FAIL (expected Level {test['expected_level']})"
            print(f"Status: {status}")
            
            results.append({
                "test": test['name'],
                "expected_level": test['expected_level'],
                "actual_level": actual_level,
                "success": success,
                "time": elapsed,
                "recipe_title": recipe.get('title', 'Unknown')
            })
        else:
            print(f"Result: ❌ NO RECIPE FOUND")
            results.append({
                "test": test['name'],
                "expected_level": test['expected_level'],
                "actual_level": None,
                "success": False,
                "time": elapsed,
                "recipe_title": None
            })
    
    # Print summary
    print("\n" + "=" * 70)
    print("HEALTH CHECK SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    
    print(f"\nOverall: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    
    # Analyze by level
    for level in range(1, 5):
        level_tests = [r for r in results if r['expected_level'] == level]
        if level_tests:
            level_passed = sum(1 for r in level_tests if r['success'])
            print(f"\nLevel {level} Performance:")
            print(f"  Tests: {len(level_tests)}")
            print(f"  Passed: {level_passed}")
            print(f"  Success Rate: {100*level_passed/len(level_tests):.1f}%")
            
            for r in level_tests:
                status = "✅" if r['success'] else "❌"
                actual = f"Level {r['actual_level']}" if r['actual_level'] else "FAILED"
                print(f"    {status} {r['test']}: {actual} ({r['time']:.2f}s)")
    
    # Performance analysis
    print("\n" + "=" * 70)
    print("PERFORMANCE ANALYSIS")
    print("=" * 70)
    
    level_1_times = [r['time'] for r in results if r['actual_level'] == 1]
    level_2_times = [r['time'] for r in results if r['actual_level'] == 2]
    level_3_times = [r['time'] for r in results if r['actual_level'] == 3]
    level_4_times = [r['time'] for r in results if r['actual_level'] == 4]
    
    if level_1_times:
        print(f"Level 1 (Database): avg {sum(level_1_times)/len(level_1_times):.2f}s")
    if level_2_times:
        print(f"Level 2 (API): avg {sum(level_2_times)/len(level_2_times):.2f}s")
    if level_3_times:
        print(f"Level 3 (Sister): avg {sum(level_3_times)/len(level_3_times):.2f}s")
    if level_4_times:
        print(f"Level 4 (A.I. Chef): avg {sum(level_4_times)/len(level_4_times):.2f}s")
    
    # Save detailed report
    with open('4d_health_check_report.json', 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "success_rate": f"{100*passed/total:.1f}%"
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: 4d_health_check_report.json")
    
    return results

def determine_level(recipe, elapsed_time):
    """Determine which level likely generated the recipe based on timing and content"""
    # Level 1: Very fast (< 0.5s), from database
    if elapsed_time < 0.5:
        return 1
    # Level 4: Has A.I. Chef characteristics
    elif "Simple" in recipe.get('title', '') or elapsed_time > 2.0:
        return 4
    # Level 2-3: Medium speed, from API
    else:
        return 2

if __name__ == "__main__":
    results = run_4d_health_check()