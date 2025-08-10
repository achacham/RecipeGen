# test_4d_comprehensive.py
"""
Comprehensive 4D Recipe Matcher Testing Suite
Tests the FULL logic chain with video generation DISABLED
"""

import json
import time
from pathlib import Path
from recipe_matcher_4d import RecipeMatcher4D

class ComprehensiveRecipeTester:
    def __init__(self):
        """Initialize tester with VIDEO GENERATION DISABLED"""
        print("🔧 Initializing Comprehensive Recipe Tester...")
        print("🎬 VIDEO GENERATION: DISABLED (saving money!)")
        
        # Load ingredients.json to verify country coverage
        ingredients_path = Path(__file__).parent / "data" / "ingredients.json"
        with open(ingredients_path, 'r', encoding='utf-8') as f:
            self.ingredients_data = json.load(f)
        
        # Initialize the 4D matcher
        self.matcher = RecipeMatcher4D()
        
        # DISABLE video generation temporarily
        self.matcher.enable_video = False
        
        print(f"✅ Loaded cuisines from ingredients.json")
        print(f"📚 Local database: {self.matcher.local_db_available}")
        print("-" * 60)
    
    def run_test_case(self, test_name: str, cuisine: str, dish_type: str, ingredients: list):
        """Run a single test case and report results"""
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        print(f"Cuisine: {cuisine}")
        print(f"Dish Type: {dish_type}")
        print(f"Ingredients: {ingredients}")
        print("-" * 40)
        
        start_time = time.time()
        
        # Run the 4D search
        result = self.matcher.find_recipe(
            cuisine=cuisine,
            dish_type=dish_type,
            ingredients=ingredients
        )
        
        elapsed = time.time() - start_time
        
        # Analyze results
        if result and result.get('title'):
            print(f"✅ SUCCESS: {result['title']}")
            print(f"   Source: {result.get('source', 'unknown')}")
            print(f"   Level reached: {self._determine_level(result)}")
            if result.get('partial_match'):
                print(f"   ⚠️  Partial match: {result.get('matched_ingredients', 0)}/{len(ingredients)} ingredients")
        else:
            print(f"❌ FAILED: Fell back to essential recipe")
            if result and result.get('alternatives'):
                print(f"   Alternatives offered: {len(result['alternatives'])}")
        
        print(f"⏱️  Time: {elapsed:.2f} seconds")
        
        return result
    
    def _determine_level(self, result):
        """Determine which 4D level found the recipe"""
        source = result.get('source', '')
        if source == 'local_database':
            return "Level 1 (Local DB)"
        elif source.lower() in ['spoonacular', 'themealdb', 'edamam', 'tasty', 'mycookbook']:
            return "Level 2 (Direct API)"
        elif result.get('sister_country'):
            return "Level 3 (Sister Country)"
        else:
            return "Level 4 (Fallback)"
    
    def run_comprehensive_tests(self):
        """Run all test categories"""
        print("\n" + "="*60)
        print("COMPREHENSIVE 4D RECIPE MATCHER TESTING")
        print("="*60)
        
        test_cases = [
            # CATEGORY 1: Should work from Local DB
            ("Mexican Chicken - Local DB Hit", "mexican", "any", ["chicken"]),
            ("Italian Pasta - Local DB Hit", "italian", "pasta", ["pasta"]),
            ("British Beef - Local DB Hit", "british", "any", ["beef"]),
            
            # CATEGORY 2: Should work from APIs
            ("Thai Curry - API Search", "thai", "curry", ["coconut milk", "curry"]),
            ("Japanese Sushi - API Search", "japanese", "any", ["rice", "fish"]),
            ("Indian Curry - API Search", "indian", "curry", ["curry", "rice"]),
            
            # CATEGORY 3: Sister Country Mapping
            ("Singaporean (→Malaysian)", "singaporean", "any", ["noodles"]),
            ("Taiwanese (→Chinese)", "taiwanese", "any", ["pork"]),
            
            # CATEGORY 4: Difficult but should work
            ("Greek Seafood", "greek", "any", ["fish", "lemon"]),
            ("Spanish Paella", "spanish", "any", ["rice", "seafood"]),
            
            # CATEGORY 5: Expected fallbacks (rare combinations)
            ("Ethiopian Plantain - Fallback", "ethiopian", "any", ["plantain"]),
            ("Mongolian Pasta - Fallback", "mongolian", "pasta", ["pasta"]),
        ]
        
        results_summary = {
            'success': 0,
            'partial': 0,
            'fallback': 0,
            'by_level': {1: 0, 2: 0, 3: 0, 4: 0}
        }
        
        for test in test_cases:
            result = self.run_test_case(*test)
            
            # Track statistics
            if result and result.get('title'):
                if result.get('partial_match'):
                    results_summary['partial'] += 1
                else:
                    results_summary['success'] += 1
                
                # Track by level
                if result.get('source') == 'local_database':
                    results_summary['by_level'][1] += 1
                elif result.get('source') in ['spoonacular', 'themealdb', 'edamam', 'tasty', 'mycookbook']:
                    results_summary['by_level'][2] += 1
                elif result.get('sister_country'):
                    results_summary['by_level'][3] += 1
            else:
                results_summary['fallback'] += 1
                results_summary['by_level'][4] += 1
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total_tests = len(test_cases)
        success_rate = (results_summary['success'] / total_tests) * 100
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Full Success: {results_summary['success']} ({success_rate:.1f}%)")
        print(f"⚠️  Partial Match: {results_summary['partial']}")
        print(f"❌ Fallbacks: {results_summary['fallback']}")
        print("\nBy Level:")
        print(f"  Level 1 (Local DB): {results_summary['by_level'][1]}")
        print(f"  Level 2 (APIs): {results_summary['by_level'][2]}")
        print(f"  Level 3 (Sister): {results_summary['by_level'][3]}")
        print(f"  Level 4 (Fallback): {results_summary['by_level'][4]}")
        
        if success_rate >= 75:
            print("\n🎉 EXCELLENT! Fallbacks are now the exception, not the rule!")
        elif success_rate >= 60:
            print("\n✅ GOOD! Most recipes found, fallbacks minimized")
        else:
            print("\n⚠️  NEEDS WORK: Too many fallbacks still occurring")

if __name__ == "__main__":
    tester = ComprehensiveRecipeTester()
    tester.run_comprehensive_tests()