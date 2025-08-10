# test_spoonacular.py
from spoonacular_fetcher import SpoonacularFetcher, API_KEY

# Test what we're getting
fetcher = SpoonacularFetcher(API_KEY)

# Get one recipe to examine
results = fetcher.search_recipes("american", ["beef"], number=1)

if 'results' in results and results['results']:
    recipe = results['results'][0]
    print("RAW RECIPE DATA:")
    print(f"Title: {recipe.get('title')}")
    print(f"Score: {recipe.get('spoonacularScore')}")
    print(f"Likes: {recipe.get('aggregateLikes')}")
    print(f"Instructions: {recipe.get('instructions', 'NO INSTRUCTIONS')}")
    print(f"Ready in: {recipe.get('readyInMinutes')} minutes")
    print(f"Ingredients: {len(recipe.get('extendedIngredients', []))}")
    
    print("\n\nFULL DATA:")
    import json
    print(json.dumps(recipe, indent=2))