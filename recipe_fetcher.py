import requests
import json
from typing import List, Dict, Optional
import time

class TheMealDBFetcher:
    """Fetches real recipes from TheMealDB API"""
    
    def __init__(self):
        self.base_url = "https://www.themealdb.com/api/json/v1/1"
        self.recipes_db = []
        
    def search_by_ingredient(self, ingredient: str) -> List[Dict]:
        """Search recipes by main ingredient"""
        print(f"🔍 Searching TheMealDB for recipes with {ingredient}...")
        
        url = f"{self.base_url}/filter.php?i={ingredient}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            meals = data.get('meals') or []  # Handle None case
            print(f"✅ Found {len(meals)} recipes with {ingredient}")
            return meals
        else:
            print(f"❌ Error searching for {ingredient}")
            return []
    
    def get_recipe_details(self, meal_id: str) -> Optional[Dict]:
        """Get full recipe details by ID"""
        url = f"{self.base_url}/lookup.php?i={meal_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            meals = data.get('meals', [])
            if meals:
                return meals[0]
        return None
    
    def determine_dish_type(self, meal: Dict) -> str:
        """Determine dish type ONLY from explicit keywords in title"""
        title = meal.get('strMeal', '').lower()
        
        # Map of keywords to dish types - this is DATA, not hardcoding
        dish_type_keywords = {
            'baked-dish': ['pie', 'casserole', 'bake', 'roast'],
            'soup': ['soup', 'stew', 'broth'],
            'salad': ['salad'],
            'sandwich': ['sandwich', 'burger'],
            'pasta': ['pasta', 'spaghetti', 'lasagne', 'linguine', 'penne'],
            'curry': ['curry'],
            'stir-fry': ['stir fry', 'stir-fry'],
            'wrap': ['wrap', 'burrito'],
            'skewer': ['skewer', 'kebab'],
            'risotto': ['risotto'],
            'bowl': ['bowl']
        }
        
        # Check title against keywords
        for dish_type, keywords in dish_type_keywords.items():
            if any(keyword in title for keyword in keywords):
                return dish_type
        
        # Cannot determine - return None or 'unknown'
        return None  # Let the system decide what to do

    def convert_to_recipegen_format(self, meal: Dict) -> Dict:
        """Convert TheMealDB format to our RecipeGen format"""
        
        # Extract ingredients and measurements
        ingredients = []
        for i in range(1, 21):  # TheMealDB has up to 20 ingredients
            ing = meal.get(f'strIngredient{i}', '').strip()
            measure = meal.get(f'strMeasure{i}', '').strip()
            if ing:
                ingredients.append({
                    "name": ing,
                    "amount": measure,
                    "slug": ing.lower().replace(' ', '-')
                })
        
        # Parse instructions into steps
        instructions = meal.get('strInstructions', '')
        steps = []
        if instructions:
            # Split by periods or newlines to create steps
            raw_steps = [s.strip() for s in instructions.replace('\n', '. ').split('. ') if s.strip()]
            for idx, step in enumerate(raw_steps, 1):
                steps.append({
                    "step": idx,
                    "instruction": step,
                    "time": 5,  # Default time, we'll improve this later
                    "tip": ""
                })
        
        # Determine cuisine from area
        # Updated area_to_cuisine mapping based on YOUR ingredients.json
        area_to_cuisine = {
            "African": "african",
            "American": "american",
            "Austrian": "austrian",
            "Brazilian": "brazilian",
            "British": "british",
            "Burmese": "burmese",
            "Cambodian": "cambodian",
            "Canadian": "canadian",
            "Caribbean": "caribbean",
            "Chinese": "chinese",
            "Croatian": "croatian",
            "Cuban": "cuban",
            "Danish": "danish",
            "Dutch": "dutch",
            "Eastern European": "eastern european",
            "Egyptian": "egyptian",
            "Finnish": "finnish",
            "French": "french",
            "Greek": "greek",
            "Hungarian": "hungarian",
            "Indian": "indian",
            "Indonesian": "indonesian",
            "Irish": "irish",
            "Italian": "italian",
            "Jamaican": "jamaican",
            "Japanese": "japanese",
            "Jewish": "jewish",
            "Korean": "korean",
            "Laotian": "laotian",
            "Malaysian": "malaysian",
            "Mediterranean": "mediterranean",
            "Mexican": "mexican",
            "Middle Eastern": "middle eastern",
            "Moroccan": "moroccan",
            "Nigerian": "nigerian",
            "Pakistani": "pakistani",
            "Persian": "persian",
            "Polish": "polish",
            "Portuguese": "portuguese",
            "Puerto Rican": "puerto rican",
            "Romanian": "romanian",
            "Russian": "russian",
            "Scandinavian": "scandinavian",
            "Singaporean": "singaporean",
            "Southeast Asian": "southeast asian",
            "Spanish": "spanish",
            "Swiss": "swiss",
            "Thai": "thai",
            "Turkish": "turkish",
            "Vietnamese": "vietnamese",
            "West African": "west african"
    }
        
        cuisine = area_to_cuisine.get(meal.get('strArea', ''), 'international')
        
        # Determine dish type from category
        category_to_dish_type = {
            "Beef": "stir-fry",
            "Chicken": "baked-dish",
            "Pasta": "pasta",
            "Seafood": "stir-fry",
            "Vegetarian": "stir-fry",
            "Breakfast": "baked-dish",
            "Dessert": "dessert",
            "Soup": "soup",
            "Starter": "salad",
            "Side": "bowl"
        }
        
        dish_type = self.determine_dish_type(meal)
        
        # Build recipe object
        recipe = {
            "recipe_id": f"mealdb-{meal['idMeal']}",
            "title": meal['strMeal'],
            "cuisine": cuisine,
            "dish_type": dish_type,
            "difficulty": 2,  # Default medium difficulty
            "prep_time": 15,
            "cook_time": 30,
            "servings": 4,
            "source": "TheMealDB",
            "source_url": meal.get('strSource', ''),
            "video_url": meal.get('strYoutube', ''),
            "thumbnail": meal['strMealThumb'],
            "category": meal.get('strCategory', ''),
            "all_ingredients": ingredients,
            "required_ingredients": [ing['slug'] for ing in ingredients[:3]],  # First 3 as required
            "steps": steps,
            "techniques": [],  # We'll extract these later
            "chef_secrets": "",
            "rating": 4.5  # Default good rating
        }
        
        return recipe
    
    def fetch_recipes_for_ingredient(self, ingredient: str, limit: int = 5) -> List[Dict]:
        """Fetch and convert recipes for a specific ingredient"""
        recipes = []
        meals = self.search_by_ingredient(ingredient)
        
        for meal in meals[:limit]:
            print(f"📖 Fetching details for: {meal['strMeal']}")
            time.sleep(0.5)  # Be nice to their API
            
            details = self.get_recipe_details(meal['idMeal'])
            if details:
                recipe = self.convert_to_recipegen_format(details)
                recipes.append(recipe)
                print(f"✅ Converted: {recipe['title']}")
        
        return recipes
    
    def fetch_recipes_for_recipegen(self, ingredients: List[str] = ['beef', 'chicken', 'pasta']) -> Dict:
        """Fetch recipes for common RecipeGen ingredients"""
        all_recipes = []
        
        for ingredient in ingredients:
            recipes = self.fetch_recipes_for_ingredient(ingredient, limit=3)
            all_recipes.extend(recipes)
            print(f"📊 Total recipes so far: {len(all_recipes)}")
        
        # Save to file
        output = {
            "version": "1.0",
            "source": "TheMealDB",
            "fetch_date": time.strftime("%Y-%m-%d"),
            "total_recipes": len(all_recipes),
            "recipes": all_recipes
        }
        
        with open('recipes_db.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 SUCCESS! Fetched {len(all_recipes)} real recipes!")
        print(f"📁 Saved to recipes_db.json")
        
        return output


# Test the fetcher
if __name__ == "__main__":
    fetcher = TheMealDBFetcher()
    
    # Test with a single ingredient first
    print("🧪 Testing with beef recipes...")
    beef_recipes = fetcher.fetch_recipes_for_ingredient("beef", limit=2)
    
    if beef_recipes:
        print(f"\n📋 Sample recipe structure:")
        print(json.dumps(beef_recipes[0], indent=2))
    
    # Uncomment to fetch full database
    print("\n🚀 Fetching full recipe database...")
    fetcher.fetch_recipes_for_recipegen(['beef', 'chicken', 'fish', 'pasta', 'rice'])