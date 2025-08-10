# /*
# * RecipeGen™ - AI-Powered Culinary Video & Recipe Generation Platform
# * © Copyright By Abraham Chachamovits
# * RecipeGen™ is a trademark of Abraham Chachamovits
# * 
# * File: spoonacular_fetcher.py
# */

import requests
import json
import time
from typing import List, Dict

class SpoonacularFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.spoonacular.com"
        
    def search_recipes(self, cuisine: str, ingredients: List[str], number: int = 100):
        """Search recipes by cuisine and ingredients"""
        endpoint = f"{self.base_url}/recipes/complexSearch"
        
        params = {
            'apiKey': self.api_key,
            'cuisine': cuisine,
            'includeIngredients': ','.join(ingredients),
            'number': number,  # Get up to 100 per request
            'addRecipeInformation': True,
            'fillIngredients': True
        }
        
        response = requests.get(endpoint, params=params)
        return response.json()
    
    def is_quality_recipe(self, recipe: Dict) -> bool:
        """Filter out bad recipes - FIXED for search results"""
        
        # Must have a good rating
        if recipe.get('spoonacularScore', 0) < 70:  # 70+ out of 100
            return False
        
        # Lower the likes requirement - many good recipes have few likes
        if recipe.get('aggregateLikes', 0) < 1:  # Changed from 10 to 1
            return False
        
        # Can't check instructions in search results - will check later
        # Remove the instructions check!
        
        # Must have reasonable cooking time
        ready_in = recipe.get('readyInMinutes', 999)
        if ready_in > 180:  # Skip 3+ hour recipes
            return False
        
        # Must have ingredients (search results have this)
        if len(recipe.get('extendedIngredients', [])) < 3:
            return False
        
        return True
    
    # Add these methods to the SpoonacularFetcher class:

    def get_recipe_details(self, recipe_id: int) -> Dict:
        """Get full recipe details including instructions"""
        endpoint = f"{self.base_url}/recipes/{recipe_id}/information"
        
        params = {
            'apiKey': self.api_key,
            'includeNutrition': False  # Save API points
        }
        
        response = requests.get(endpoint, params=params)
        return response.json()

    def convert_to_recipegen_format(self, spoon_recipe: Dict) -> Dict:
        """Convert Spoonacular format to RecipeGen format"""
        
        # Extract ingredients
        ingredients = []
        for ing in spoon_recipe.get('extendedIngredients', []):
            ingredients.append({
                "name": ing.get('name', ''),
                "amount": f"{ing.get('amount', '')} {ing.get('unit', '')}",
                "slug": ing.get('name', '').lower().replace(' ', '-')
            })
        
        # Parse instructions into steps
        steps = []
        instructions = spoon_recipe.get('instructions', '')
        
        # Also check for analyzedInstructions which is cleaner
        if spoon_recipe.get('analyzedInstructions'):
            # Use the cleaner analyzed format if available
            for instruction_group in spoon_recipe['analyzedInstructions']:
                for step in instruction_group.get('steps', []):
                    steps.append({
                        "step": step['number'],
                        "instruction": step['step'],
                        "time": 5,  # Default
                        "tip": ""
                    })
        elif instructions:
            # Fall back to cleaning the HTML instructions
            import re
            # Remove HTML tags
            instructions = re.sub(r'<[^>]+>', '. ', instructions)  # Replace tags with periods
            instructions = re.sub(r'\.+', '.', instructions)  # Clean multiple periods
            instructions = re.sub(r'\s+', ' ', instructions)  # Clean extra spaces
            instructions = instructions.strip()
            
            # Split by sentences or numbered steps
            raw_steps = []
            
            # Try to split by numbered patterns first (1., 2., etc)
            numbered_pattern = re.findall(r'(\d+[\.)]\s*[^.]+\.)', instructions)
            if numbered_pattern:
                raw_steps = numbered_pattern
            else:
                # Fall back to sentence splitting
                raw_steps = [s.strip() for s in instructions.split('. ') if s.strip() and len(s.strip()) > 10]
            
            for idx, step in enumerate(raw_steps, 1):
                # Clean step text
                step = re.sub(r'^\d+[\.)]\s*', '', step)  # Remove leading numbers
                step = step.strip()
                if step and len(step.split()) >= 3:  # Only add meaningful steps
                    steps.append({
                        "step": idx,
                        "instruction": step,
                        "time": 5,  # Default
                        "tip": ""
                    })
        
        # Determine dish type from recipe data
        dish_type = self.guess_dish_type(spoon_recipe)
        
        return {
            "recipe_id": f"spoon-{spoon_recipe['id']}",
            "title": spoon_recipe['title'],
            "cuisine": spoon_recipe.get('cuisines', ['international'])[0].lower() if spoon_recipe.get('cuisines') else 'international',
            "dish_type": dish_type,
            "difficulty": 2 if spoon_recipe.get('readyInMinutes', 30) < 45 else 3,
            "prep_time": spoon_recipe.get('preparationMinutes', 15),
            "cook_time": spoon_recipe.get('cookingMinutes', 30),
            "servings": spoon_recipe.get('servings', 4),
            "source": "Spoonacular",
            "source_url": spoon_recipe.get('sourceUrl', ''),
            "image_url": spoon_recipe.get('image', ''),
            "all_ingredients": ingredients,
            "required_ingredients": [ing['slug'] for ing in ingredients[:3]],
            "steps": steps,
            "techniques": [],
            "chef_secrets": "",
            "rating": spoon_recipe.get('spoonacularScore', 0) / 20  # Convert to 5-star scale
        }

    def guess_dish_type(self, recipe: Dict) -> str:
        """Guess dish type from recipe title and tags"""
        title = recipe.get('title', '').lower()
        dish_types = recipe.get('dishTypes', [])
        
        # Check explicit dish types first
        for dtype in dish_types:
            if 'soup' in dtype: return 'soup'
            if 'salad' in dtype: return 'salad'
            if 'pasta' in dtype: return 'pasta'
            if 'curry' in dtype: return 'curry'
            if 'stir fry' in dtype or 'stir-fry' in dtype: return 'stir-fry'
            if 'sandwich' in dtype: return 'sandwich'
            if 'wrap' in dtype: return 'wrap'
            if 'bowl' in dtype: return 'bowl'
        
        # Check title
        if 'pie' in title or 'casserole' in title or 'bake' in title:
            return 'baked-dish'
        elif 'soup' in title or 'stew' in title:
            return 'soup'
        elif 'salad' in title:
            return 'salad'
        elif 'pasta' in title:
            return 'pasta'
        elif 'curry' in title:
            return 'curry'
        elif 'stir fry' in title or 'stir-fry' in title:
            return 'stir-fry'
        
        return 'unknown'

# ADD YOUR KEY HERE:
API_KEY = "900ff67536964e419f2584505480b7fa"

# Test the fetcher
if __name__ == "__main__":
    fetcher = SpoonacularFetcher(API_KEY)
    print("🔍 Testing Spoonacular API...")
    
    # Test search for Italian beef recipes
    results = fetcher.search_recipes("italian", ["beef"], number=5)
    
    if 'results' in results:
        print(f"✅ Found {len(results['results'])} recipes!")
        for recipe in results['results']:
            print(f"- {recipe['title']} (Score: {recipe.get('spoonacularScore', 0)})")
    else:
        print("❌ Error:", results)