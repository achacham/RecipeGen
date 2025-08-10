# fetch_all_recipes.py
"""
Spoonacular Recipe Fetcher for RecipeGen
=======================================
This script fetches high-quality recipes from the Spoonacular API
for all cuisines defined in RecipeGen's ingredients.json.

Output: recipes_spoonacular.json
API: Spoonacular (https://spoonacular.com/food-api)
Rate Limit: 150 requests/day (free tier)

Author: RecipeGen Team
Date: August 2025
"""

import json
import time
from spoonacular_fetcher import SpoonacularFetcher, API_KEY

def load_my_cuisines():
    """Load all cuisines from ingredients.json"""
    with open('data/ingredients.json', 'r') as f:
        ingredients = json.load(f)
    
    cuisines = set()
    for ingredient in ingredients:
        for cuisine in ingredient.get('cuisine', []):
            cuisines.add(cuisine)
    
    return sorted(cuisines)

def fetch_recipes_for_all_cuisines():
    """Fetch quality recipes for all cuisines from Spoonacular API"""
    fetcher = SpoonacularFetcher(API_KEY)
    all_recipes = []
    
    cuisines = load_my_cuisines()
    print(f"📋 Found {len(cuisines)} cuisines to fetch recipes for!")
    
    # Common ingredients to search with
    common_ingredients = ['beef', 'chicken', 'rice', 'pasta', 'vegetables']
    
    for cuisine in cuisines[:10]:  # Start with first 10 cuisines
        print(f"\n🌍 Fetching {cuisine.upper()} recipes...")
        
        for ingredient in common_ingredients[:2]:  # Start with beef & chicken
            print(f"  🔍 Searching {cuisine} + {ingredient}...")
            
            try:
                # Search for recipes
                results = fetcher.search_recipes(cuisine, [ingredient], number=20)
                
                if 'results' in results:
                    recipes = results['results']
                    quality_recipes = [r for r in recipes if fetcher.is_quality_recipe(r)]
                    
                    print(f"  ✅ Found {len(quality_recipes)} quality recipes (out of {len(recipes)})")
                    
                    # Get full details for quality recipes
                    for recipe in quality_recipes[:5]:  # Limit to save API points
                        time.sleep(0.5)  # Be nice to API
                        
                        details = fetcher.get_recipe_details(recipe['id'])
                        if 'id' in details:
                            converted = fetcher.convert_to_recipegen_format(details)
                            all_recipes.append(converted)
                            print(f"    📖 Added: {converted['title']}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    # Save to new database
    output = {
        "version": "2.0",
        "source": "Spoonacular",
        "fetch_date": time.strftime("%Y-%m-%d"),
        "total_recipes": len(all_recipes),
        "recipes": all_recipes
    }
    
    with open('recipes_spoonacular.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 SUCCESS! Fetched {len(all_recipes)} quality recipes!")
    print(f"📁 Saved to recipes_spoonacular.json")
    
    # Show summary
    cuisine_counts = {}
    for recipe in all_recipes:
        c = recipe['cuisine']
        cuisine_counts[c] = cuisine_counts.get(c, 0) + 1
    
    print("\n📊 Recipes by cuisine:")
    for cuisine, count in sorted(cuisine_counts.items()):
        print(f"  {cuisine}: {count} recipes")

if __name__ == "__main__":
    print("🚀 Starting Spoonacular recipe fetch!")
    print("⚠️  This will use API points. Free tier = 150/day")
    print("Press Ctrl+C to stop anytime\n")
    
    fetch_recipes_for_all_cuisines()