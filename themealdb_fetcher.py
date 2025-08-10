# themealdb_fetcher.py
import requests
import json
from typing import List, Dict, Optional

class TheMealDBFetcher:
    """
    Fetcher for TheMealDB API
    Simple, honest, no credit card nonsense!
    """
    def __init__(self, api_key: str = "1"):  # Default to test key
        self.api_key = api_key
        self.base_url = "https://www.themealdb.com/api/json/v1"
    
    def search_recipes(self, cuisine: str, ingredients: List[str], number: int = 10) -> Dict:
        """
        Search recipes - TheMealDB style
        Note: Less sophisticated than Spoonacular but HONEST!
        """
        print(f"      🍽️ TheMealDB searching for: {cuisine} with {ingredients}")

        # TheMealDB uses different cuisine names (e.g., "Canadian", "Chinese")
        cuisine_mapping = {
            'italian': 'Italian',
            'chinese': 'Chinese', 
            'japanese': 'Japanese',
            'french': 'French',
            'indian': 'Indian',
            'mexican': 'Mexican',
            'thai': 'Thai',
            'american': 'American',
            'british': 'British',
            'canadian': 'Canadian',
            'dutch': 'Dutch',
            'egyptian': 'Egyptian',
            'greek': 'Greek',
            'irish': 'Irish',
            'jamaican': 'Jamaican',
            'malaysian': 'Malaysian',
            'russian': 'Russian',
            'spanish': 'Spanish',
            'vietnamese': 'Vietnamese',
            # Add more as discovered
        }
        
        results = {'results': []}
        
        # Try searching by cuisine first
        themeal_cuisine = cuisine_mapping.get(cuisine.lower())
        if themeal_cuisine:
            print(f"      🍽️ Mapped {cuisine} → {themeal_cuisine}")
            endpoint = f"{self.base_url}/{self.api_key}/filter.php"
            params = {'a': themeal_cuisine}
            
            try:
                response = requests.get(endpoint, params=params)
                data = response.json()
                
                if data and 'meals' in data and data['meals']:
                    print(f"      🍽️ Found {len(data['meals'])} {themeal_cuisine} meals")
                    # TheMealDB returns simplified results, need to get full details
                    for meal in data['meals'][:number]:
                        # Check if any of our ingredients might be in this meal
                        meal_name_lower = meal['strMeal'].lower()
                        
                        # Simple ingredient matching in meal name
                        ingredient_match = any(ing.lower() in meal_name_lower for ing in ingredients)
                        
                        if ingredient_match or len(ingredients) == 0:
                            results['results'].append({
                                'id': meal['idMeal'],
                                'title': meal['strMeal'],
                                'image': meal['strMealThumb'],
                                'sourceUrl': f"https://www.themealdb.com/meal/{meal['idMeal']}"
                            })
                
            except Exception as e:
                print(f"❌ TheMealDB error: {e}")
        
        # If no cuisine results, try searching by main ingredient
        if not results['results'] and ingredients:
            main_ingredient = ingredients[0]
            endpoint = f"{self.base_url}/{self.api_key}/filter.php"
            params = {'i': main_ingredient}
            
            try:
                response = requests.get(endpoint, params=params)
                data = response.json()
                
                if data and 'meals' in data and data['meals']:
                    for meal in data['meals'][:number]:
                        results['results'].append({
                            'id': meal['idMeal'],
                            'title': meal['strMeal'],
                            'image': meal['strMealThumb'],
                            'sourceUrl': f"https://www.themealdb.com/meal/{meal['idMeal']}"
                        })
                        
            except Exception as e:
                print(f"❌ TheMealDB ingredient search error: {e}")
        
        return results
    
    def get_recipe_details(self, recipe_id: str) -> Dict:
        """Get full recipe details"""
        endpoint = f"{self.base_url}/{self.api_key}/lookup.php"
        params = {'i': recipe_id}
        
        response = requests.get(endpoint, params=params)
        data = response.json()
        
        if data and 'meals' in data and data['meals']:
            return data['meals'][0]
        return {}
    
    def is_quality_recipe(self, recipe: Dict) -> bool:
        """
        Check recipe quality
        TheMealDB doesn't have scores, so we just check basics
        """
        # Simple quality check - has title and ID
        return bool(recipe.get('id') and recipe.get('title'))
    
    def convert_to_recipegen_format(self, meal: Dict) -> Dict:
        """Convert TheMealDB format to RecipeGen format with INTELLIGENT conversion"""
        
        # Extract basic fields
        title = meal.get('strMeal', 'Unknown Recipe')
        instructions_text = meal.get('strInstructions', '')
        category = meal.get('strCategory', '')
        area = meal.get('strArea', '')
        
        # INTELLIGENTLY DETERMINE DISH TYPE
        dish_type = self._infer_dish_type(title, instructions_text, category)
        
        # Extract ingredients
        ingredients = []
        for i in range(1, 21):  # TheMealDB has up to 20 ingredients
            ing_name = (meal.get(f'strIngredient{i}') or '').strip()
            ing_measure = (meal.get(f'strMeasure{i}') or '').strip()
            
            if ing_name:
                ingredients.append({
                    'name': ing_name,
                    'amount': ing_measure if ing_measure else 'to taste',
                    'slug': ing_name.lower().replace(' ', '_')
                })
        
        # Convert instructions to structured format
        steps = []
        if instructions_text:
            import re
            # Split by line breaks or sentences
            sentences = re.split(r'(?:\r\n|\n|\. (?=[A-Z]))', instructions_text)
            
            for idx, sentence in enumerate(sentences, 1):
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:  # Skip fragments
                    steps.append({
                        'step': idx,
                        'instruction': sentence,
                        'time': 5,
                        'tip': ''
                    })
        
        # Estimate cooking times based on dish type
        prep_time, cook_time = self._estimate_cooking_times(dish_type, instructions_text)
        
        return {
            'recipe_id': f"mealdb-{meal.get('idMeal', 'unknown')}",
            'title': title,
            'cuisine': area.lower() if area else 'international',
            'cuisines': [area.lower()] if area else [],  # Add this for validation
            'dish_type': dish_type,  # Now properly inferred!
            'difficulty': 2,
            'prep_time': prep_time,
            'cook_time': cook_time,
            'total_time': prep_time + cook_time,
            'servings': 4,
            'source': 'TheMealDB',
            'source_url': meal.get('strSource', ''),
            'image_url': meal.get('strMealThumb', ''),
            'all_ingredients': ingredients,
            'ingredients': ingredients,  # Add both formats
            'required_ingredients': [ing['slug'] for ing in ingredients[:3]],
            'steps': steps,
            'instructions': steps,  # Add both formats
            'techniques': [],
            'chef_secrets': '',
            'rating': 4.0,
            'quality_score': 70
        }
    
    def _infer_dish_type(self, title: str, instructions: str, category: str) -> str:
        """Intelligently infer the actual cooking method/dish type"""
        
        title_lower = title.lower()
        instructions_lower = instructions.lower()
        
        # Check for specific dish types in order of specificity
        dish_type_patterns = {
            'stir-fry': ['stir-fry', 'stir fry', 'stirfry', 'kung pao', 'kung po', 'gong bao',
                         'chow mein', 'lo mein', 'pad thai', 'pad see ew', 'fried rice'],
            'curry': ['curry', 'korma', 'masala', 'vindaloo', 'tikka masala', 'panang', 'massaman'],
            'soup': ['soup', 'stew', 'broth', 'bisque', 'chowder', 'congee', 'pho', 'ramen', 'hotpot'],
            'baked-dish': ['baked', 'roasted', 'casserole', 'gratin', 'pie', 'lasagna', 'pot roast'],
            'pasta': ['pasta', 'spaghetti', 'penne', 'linguine', 'fettuccine', 'alfredo', 'carbonara', 'primavera'],
            'salad': ['salad', 'slaw', 'fresh', 'raw'],
            'grilled': ['grilled', 'grill', 'bbq', 'barbecue', 'charred', 'piri-piri'],
            'fried': ['fried chicken', 'deep-fried', 'crispy', 'tempura', 'karaage', 'katsu', 'kentucky fried'],
            'steamed': ['steamed', 'steam', 'dumpling', 'dim sum']
        }
        
        # First check title for clear indicators
        for dish_type, patterns in dish_type_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                return dish_type
        
        # Then check instructions for cooking methods
        instruction_indicators = {
            'stir-fry': ['sauté', 'saute', 'stir', 'toss', 'wok', 'high heat', 'quickly', 'stir-fry'],
            'baked-dish': ['oven', 'bake', 'degrees', 'preheat', 'roast', 'baking dish'],
            'soup': ['simmer', 'boil', 'stock', 'liquid', 'ladle', 'broth'],
            'grilled': ['grill', 'char', 'barbecue', 'flames', 'bbq'],
            'fried': ['deep fry', 'oil temperature', 'golden brown', 'crispy', 'fry'],
            'curry': ['simmer', 'sauce', 'gravy', 'coconut milk', 'curry'],
            'steamed': ['steam', 'steamer', 'bamboo']
        }
        
        # Count matches for each dish type
        scores = {}
        for dish_type, indicators in instruction_indicators.items():
            score = sum(1 for indicator in indicators if indicator in instructions_lower)
            if score > 0:
                scores[dish_type] = score
        
        # Return the dish type with highest score
        if scores:
            return max(scores, key=scores.get)
        
        # Fall back to category-based inference, but smarter
        category_lower = category.lower() if category else ''
        if 'dessert' in category_lower:
            return 'dessert'
        elif 'breakfast' in category_lower:
            return 'breakfast'
        elif 'side' in category_lower:
            return 'side-dish'
        else:
            return 'main-course'  # Generic fallback
    
    def _estimate_cooking_times(self, dish_type: str, instructions: str) -> tuple:
        """Estimate prep and cook times based on dish type and instructions"""
        
        # Default times by dish type
        time_estimates = {
            'stir-fry': (15, 15),     # Quick cooking
            'soup': (20, 40),          # Longer simmering
            'curry': (20, 30),         # Medium cooking
            'baked-dish': (20, 45),    # Oven time
            'pasta': (15, 20),         # Boiling + sauce
            'salad': (15, 0),          # No cooking
            'grilled': (15, 20),       # Grill time
            'fried': (20, 15),         # Prep + frying
            'steamed': (15, 20),       # Steam time
            'main-course': (20, 30),   # Generic
            'dessert': (30, 30),       # Baking usually
            'breakfast': (10, 15),     # Quick morning meals
            'side-dish': (10, 20)      # Sides are usually quicker
        }
        
        # Look for time indicators in instructions
        import re
        time_pattern = r'(\d+)\s*(minutes?|mins?|hours?|hrs?)'
        times_found = re.findall(time_pattern, instructions.lower())
        
        if times_found:
            total_time = 0
            for time_val, unit in times_found:
                minutes = int(time_val)
                if 'hour' in unit or 'hr' in unit:
                    minutes *= 60
                total_time += minutes
            
            # Reasonable distribution between prep and cook
            if total_time > 0:
                prep = min(30, total_time // 3)
                cook = total_time - prep
                return (prep, cook)
        
        # Use defaults for dish type
        return time_estimates.get(dish_type, (15, 30))

# Test it immediately!
if __name__ == "__main__":
    fetcher = TheMealDBFetcher()  # Uses test key "1"
    
    print("🍽️ Testing TheMealDB...")
    
    # Test search
    results = fetcher.search_recipes("chinese", ["chicken"], number=5)
    
    if results['results']:
        print(f"✅ Found {len(results['results'])} recipes!")
        
        # Get details for first recipe
        first = results['results'][0]
        details = fetcher.get_recipe_details(first['id'])
        formatted = fetcher.convert_to_recipegen_format(details)
        
        print(f"\n📖 {formatted['title']}")
        print(f"Dish Type: {formatted['dish_type']}")  # Now shows intelligent inference!
        print(f"Ingredients: {len(formatted['all_ingredients'])}")
        print(f"Steps: {len(formatted['steps'])}")
    else:
        print("❌ No recipes found")
        