# test_parser_with_spoonacular.py
from spoonacular_fetcher import SpoonacularFetcher, API_KEY
from recipe_parser import wise_parser

def test_diverse_cuisines():
    """Test the parser with different cuisine types"""
    fetcher = SpoonacularFetcher(API_KEY)
    
    # Test different cuisines and dish types
    test_cases = [
        ("italian", ["pasta"], "pasta dishes"),
        ("indian", ["chicken"], "curries"),
        ("mexican", ["beef"], "tacos/burritos"),
        ("thai", ["shrimp"], "stir-fries"),
        ("french", ["butter"], "sauces"),
        ("japanese", ["rice"], "sushi/rice dishes"),
        ("american", ["cheese"], "comfort food")
    ]
    
    for cuisine, ingredients, description in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing {cuisine.upper()} {description}")
        print('='*60)
        
        # Search for recipes
        results = fetcher.search_recipes(cuisine, ingredients, number=3)
        
        if 'results' in results and results['results']:
            for recipe_summary in results['results'][:2]:  # Test first 2
                # Get full recipe details
                recipe_id = recipe_summary['id']
                full_recipe = fetcher.get_recipe_details(recipe_id)
                
                # Convert to RecipeGen format
                formatted_recipe = fetcher.convert_to_recipegen_format(full_recipe)
                
                print(f"\n📖 Recipe: {formatted_recipe['title']}")
                print(f"   Type: {formatted_recipe['dish_type']}")
                
                # Extract hero moments using your fuzzy tree parser
                hero_moments = wise_parser.extract_hero_moments(formatted_recipe)
                
                print("   🎬 Extracted Moments:")
                if hero_moments:
                    for i, moment in enumerate(hero_moments, 1):
                        print(f"      {i}. {moment}")
                else:
                    print("      ❌ No moments extracted!")
                    
                # Show fuzzy weights for reference
                print(f"   ⚙️  Current weights: {wise_parser.FUZZY_WEIGHTS}")

if __name__ == "__main__":
    test_diverse_cuisines()