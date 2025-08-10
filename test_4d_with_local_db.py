"""
Test 4D Recipe Matcher with LOCAL DATABASE
Let's see the speed difference!
"""

import time
from recipe_matcher_4d import recipe_matcher_4d

print("=== Testing 4D Recipe Matcher with LOCAL DATABASE ===\n")

# Test cases
test_cases = [
    # Should find in local DB (from TheMealDB download)
    {
        'name': 'Mexican Chicken (should be in local DB)',
        'cuisine': 'mexican',
        'ingredients': ['chicken'],
        'dish_type': 'any'
    },
    # Malaysian/Indonesian style (from your request!)
    {
        'name': 'Malaysian Beef (Indonesian-style)',
        'cuisine': 'malaysian',
        'ingredients': ['beef'],
        'dish_type': 'any'
    },
    # Should find in local DB
    {
        'name': 'Italian Pasta',
        'cuisine': 'italian',
        'ingredients': ['pasta'],
        'dish_type': 'pasta'
    },
    # Edge case - might need APIs
    {
        'name': 'Ethiopian with plantain (your test case!)',
        'cuisine': 'ethiopian',
        'ingredients': ['plantain'],
        'dish_type': 'any'
    },
    # Should find British in local DB
    {
        'name': 'British Beef Pie',
        'cuisine': 'british',
        'ingredients': ['beef'],
        'dish_type': 'baked-dish'
    }
]

for test in test_cases:
    print(f"\n{'='*60}")
    print(f"TEST: {test['name']}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    result = recipe_matcher_4d.find_recipe(
        test['cuisine'],
        test['ingredients'],
        test['dish_type']
    )
    
    elapsed = time.time() - start_time
    
    if isinstance(result, dict) and result.get('type') == 'no_match':
        print(f"❌ No match found")
        print(f"Reason: {result['search_summary']['reason']}")
        print(f"Alternatives offered: {len(result['alternatives'])}")
        for alt in result['alternatives']:
            print(f"  - {alt['cuisine']} {alt['dish_type']}: {alt['reason']}")
    else:
        print(f"✅ FOUND: {result['title']}")
        print(f"Source: {result.get('source', 'unknown')}")
        print(f"Cuisine: {result['cuisine']}")
        print(f"Dish Type: {result.get('dish_type', 'N/A')}")
        if result.get('partial_match'):
            print(f"⚠️  Partial match: {result.get('matched_ingredients')}/{len(test['ingredients'])} ingredients")
    
    print(f"\n⏱️  Search time: {elapsed:.2f} seconds")

# Show database statistics
print(f"\n\n{'='*60}")
print("DATABASE STATISTICS")
print(f"{'='*60}")

import sqlite3
conn = sqlite3.connect('D:/RecipeGen_Database/processed/recipegen_master.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM recipes")
total = cursor.fetchone()[0]
print(f"Total recipes: {total}")

cursor.execute("SELECT cuisine, COUNT(*) as count FROM recipes GROUP BY cuisine ORDER BY count DESC LIMIT 10")
print("\nTop 10 cuisines:")
for cuisine, count in cursor.fetchall():
    print(f"  {cuisine}: {count} recipes")

cursor.execute("SELECT COUNT(DISTINCT ingredient_slug) FROM recipe_ingredients")
ingredients = cursor.fetchone()[0]
print(f"\nUnique ingredients indexed: {ingredients}")

conn.close()