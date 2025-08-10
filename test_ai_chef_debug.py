# test_ai_chef_debug.py
"""
Debug test to understand why JSON is being truncated
"""

from ai_chef_generator import AIChefGenerator
import json

print("AI Chef Debug Test")
print("=" * 60)

chef = AIChefGenerator()

# Test a simple case that's failing
test_cases = [
    ("ethiopian", "stir-fry", ["plantain", "onions"]),
    ("indian", "curry", ["chickpeas", "spinach", "tomatoes", "potatoes"])
]

for cuisine, dish_type, ingredients in test_cases:
    print(f"\nTesting: {cuisine} {dish_type} with {ingredients}")
    print("-" * 40)
    
    recipe = chef.generate_recipe(cuisine, dish_type, ingredients)
    
    # Show the actual recipe content
    recipe_json = json.dumps(recipe, indent=2)
    print(f"Recipe length: {len(recipe_json)} characters")
    print(f"Title: {recipe.get('title', 'FAILED')}")
    
    if recipe.get('title') != f'Simple {cuisine.title()} {dish_type.title()}':
        print("✅ Generated real recipe")
    else:
        print("❌ Using fallback")