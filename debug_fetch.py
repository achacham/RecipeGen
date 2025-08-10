# debug_fetch.py
from spoonacular_fetcher import SpoonacularFetcher, API_KEY
import json

fetcher = SpoonacularFetcher(API_KEY)

print("STEP 1: Search for recipes")
results = fetcher.search_recipes("italian", ["beef"], number=5)

if 'results' not in results:
    print("ERROR: No results field")
    print(json.dumps(results, indent=2))
else:
    recipes = results['results']
    print(f"Found {len(recipes)} total recipes")
    
    print("\nSTEP 2: Check quality filter")
    quality_recipes = [r for r in recipes if fetcher.is_quality_recipe(r)]
    print(f"Found {len(quality_recipes)} quality recipes")
    
    if quality_recipes:
        print("\nSTEP 3: Get details for first recipe")
        first = quality_recipes[0]
        print(f"Getting details for: {first['title']} (ID: {first['id']})")
        
        details = fetcher.get_recipe_details(first['id'])
        print(f"Details response has keys: {list(details.keys())}")
        
        if 'id' in details:
            print("\nSTEP 4: Convert to RecipeGen format")
            converted = fetcher.convert_to_recipegen_format(details)
            print(f"Converted successfully: {converted['title']}")
        else:
            print("ERROR in details:")
            print(json.dumps(details, indent=2))