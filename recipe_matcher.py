import json
from typing import List, Dict, Optional
from pathlib import Path

class RecipeMatcher:
    """Matches user selections to real recipes from our database"""
    
    def __init__(self):
        self.recipe_db_path = Path(__file__).parent / "recipes_db.json"
        self.recipes = self._load_recipes()
    
    def _load_recipes(self) -> List[Dict]:
        """Load recipes from database"""
        try:
            with open(self.recipe_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('recipes', [])
        except FileNotFoundError:
            print("⚠️ Recipe database not found. Run recipe_fetcher.py first!")
            return []
        except json.JSONDecodeError:
            print("⚠️ Recipe database corrupted.")
            return []
    
    def find_recipe(self, cuisine: str, ingredients: List[str], dish_type: str) -> Optional[Dict]:
        """Find best matching recipe based on user selection"""
        print(f"🔍 Searching for: {cuisine} {dish_type} with {ingredients}")
        
        # Normalize inputs
        cuisine = cuisine.lower().strip()
        dish_type = dish_type.lower().strip()
        ingredient_slugs = [ing.lower().strip() for ing in ingredients]
        
        # Score each recipe
        best_match = None
        best_score = 0
        
        for recipe in self.recipes:
            score = 0
            
            # Cuisine match (highest priority)
            if recipe.get('cuisine', '').lower() == cuisine:
                score += 100
            
            # Dish type match (high priority)
            recipe_dish_type = (recipe.get('dish_type') or '').lower()
            if recipe_dish_type == dish_type:
                score += 50
            elif recipe_dish_type == 'unknown' or recipe_dish_type is None:
                score += 10  # Partial credit for unknown types
            
            # Ingredient matches
            recipe_ingredients = []
            for ing in recipe.get('all_ingredients', []):
                recipe_ingredients.append(ing.get('slug', '').lower())
            
            # Count matching ingredients
            matching_ingredients = 0
            for user_ing in ingredient_slugs:
                if user_ing in recipe_ingredients:
                    matching_ingredients += 1
                    score += 20
            
            # Bonus for having most/all user ingredients
            if matching_ingredients == len(ingredient_slugs):
                score += 50  # Has all requested ingredients
            
            print(f"  Recipe: {recipe.get('title')} | Score: {score}")
            
            if score > best_score:
                best_score = score
                best_match = recipe
        
        if best_match:
            print(f"✅ Best match: {best_match.get('title')} (Score: {best_score})")
        else:
            print("❌ No matching recipe found")
            
        return best_match
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict]:
        """Get specific recipe by ID"""
        for recipe in self.recipes:
            if recipe.get('recipe_id') == recipe_id:
                return recipe
        return None

# Singleton instance
recipe_matcher = RecipeMatcher()
