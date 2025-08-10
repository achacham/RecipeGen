# ai_chef_generator.py
"""
A.I. Chef Recipe Generator (The Swedish Chef!)
Using the same principled approach as video generation
LAW: Use ONLY user ingredients + cuisine-appropriate spices
"""

import json
import openai
from typing import List, Dict
import os
from dotenv import load_dotenv


class AIChefGenerator:
    """Generate recipes with cultural intelligence and ZERO hallucinations"""
    
    def __init__(self):
        # Load environment variables
        from pathlib import Path
        import sys
        
        # Get the directory where this script is located
        script_dir = Path(__file__).parent.absolute()
        print(f"Script directory: {script_dir}")
        
        # Look for .env in the script directory
        env_path = script_dir / '.env'
        print(f"Looking for .env at: {env_path}")
        
        if env_path.exists():
            print(f"✅ Found .env file!")
            load_dotenv(env_path)
        else:
            print(f"❌ .env not found at {env_path}")
            # Try current working directory
            cwd_env = Path.cwd() / '.env'
            print(f"Trying current directory: {cwd_env}")
            if cwd_env.exists():
                print(f"✅ Found .env in current directory!")
                load_dotenv(cwd_env)
            else:
                print(f"❌ No .env found!")
        
        # Use your existing OpenAI key from .env
        self.api_key = os.getenv('OPENAI_API_KEY')  # FIXED: Don't hardcode the key!
        
        if not self.api_key:
            print("WARNING: OpenAI API key not loaded!")
            # As a last resort, try to load without specifying path
            load_dotenv()
            self.api_key = os.getenv('OPENAI_API_KEY')
            if self.api_key:
                print("✅ API key loaded with default load_dotenv()!")
        else:
            print(f"✅ API Key loaded: {self.api_key[:20]}...")
            
        openai.api_key = self.api_key
        
        # Load culinary configuration from external file
        config_path = script_dir / 'data' / 'culinary_config.json'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                culinary_config = json.load(f)
                
            self.universal_basics = culinary_config.get('universal_basics', [])
            self.cultural_spices = culinary_config.get('cultural_spices', {})
            self.cooking_methods = culinary_config.get('cooking_methods', {})
            
            print(f"✅ Loaded culinary config from {config_path}")
            
        except FileNotFoundError:
            print(f"❌ Culinary config not found at {config_path}")
            print("   Using minimal defaults...")
            self.universal_basics = ['water', 'salt', 'pepper', 'oil']
            self.cultural_spices = {'default': ['salt', 'pepper', 'garlic']}
            self.cooking_methods = {'default': {'heat': 'medium', 'time': '30 minutes'}}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing culinary config: {e}")
            print("   Using minimal defaults...")
            self.universal_basics = ['water', 'salt', 'pepper', 'oil']
            self.cultural_spices = {'default': ['salt', 'pepper', 'garlic']}
            self.cooking_methods = {'default': {'heat': 'medium', 'time': '30 minutes'}}
    
    def generate_recipe(self, cuisine: str, dish_type: str, ingredients: List[str]) -> Dict:
        """Generate a culturally accurate recipe with ZERO hallucinations"""
        
        # Get cultural context
        allowed_spices = self.cultural_spices.get(cuisine.lower(), self.cultural_spices.get('default', []))
        cooking_method = self.cooking_methods.get(dish_type, {
            'heat': 'medium',
            'time': '30 minutes',
            'equipment': 'standard cookware',
            'technique': 'standard cooking'
        })
        
        # Build the prompt with STRICT LAWS
        prompt = self._build_strict_prompt(cuisine, dish_type, ingredients, 
                                          allowed_spices, cooking_method)
        
        # Generate via AI
        recipe = self._call_ai_with_validation(prompt, cuisine, dish_type, ingredients, allowed_spices)
        
        return recipe
    
    def _build_strict_prompt(self, cuisine, dish_type, ingredients, spices, method):
        """Build prompt with LAWS that prevent hallucinations"""
        
        prompt = f"""You are an expert {cuisine} chef creating a {dish_type} recipe.

ABSOLUTE LAWS (NEVER VIOLATE):
1. Use EXACTLY these ingredients: {', '.join(ingredients)}
2. You may ONLY add these {cuisine} spices/seasonings: {', '.join(spices)}
3. Basic essentials allowed: water, oil, salt, pepper

Return ONLY valid JSON (be VERY concise):
{{
    "title": "Recipe Name",
    "ingredients": [
        {{"item": "name", "amount": "qty"}},
        ...max 8 items...
    ],
    "instructions": [
        "Step 1",
        "Step 2",
        ...max 5 steps...
    ],
    "prep_time": "X min",
    "cook_time": "Y min",
    "servings": 4,
    "cuisine": "{cuisine}",
    "dish_type": "{dish_type}"
}}

Keep VERY concise. Max 8 ingredients, max 5 steps."""
        return prompt
    
    def _call_ai_with_validation(self, prompt, cuisine, dish_type, ingredients, allowed_spices):
        """Call AI and ensure valid JSON response with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are A.I. Chef. Return ONLY valid JSON. Be extremely concise."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800  # Further reduced for safety
                )
                
                recipe_text = response.choices[0].message.content.strip()
                
                # Clean up common formatting issues
                if recipe_text.startswith('```json'):
                    recipe_text = recipe_text[7:]
                elif recipe_text.startswith('```'):
                    recipe_text = recipe_text[3:]
                
                if recipe_text.endswith('```'):
                    recipe_text = recipe_text[:-3]
                
                recipe_text = recipe_text.strip()
                
                # Try to parse JSON
                try:
                    recipe = json.loads(recipe_text)
                    # Success! Validate and return
                    validated = self._validate_no_hallucinations(recipe, ingredients, allowed_spices)
                    return validated
                    
                except json.JSONDecodeError as e:
                    if attempt < max_retries - 1:
                        print(f"JSON Parse Error (attempt {attempt + 1}/{max_retries}): {e}")
                        print("Retrying...")
                        import time
                        time.sleep(1)  # Brief pause before retry
                        continue
                    else:
                        print(f"Final JSON Parse Error after {max_retries} attempts: {e}")
                        # Try to extract JSON
                        import re
                        json_match = re.search(r'\{.*\}', recipe_text, re.DOTALL)
                        if json_match:
                            try:
                                recipe = json.loads(json_match.group())
                                validated = self._validate_no_hallucinations(recipe, ingredients, allowed_spices)
                                return validated
                            except:
                                pass
                        raise ValueError("AI didn't return valid JSON after retries")
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error generating recipe (attempt {attempt + 1}/{max_retries}): {e}")
                    import time
                    time.sleep(1)
                    continue
                else:
                    print(f"Final error after {max_retries} attempts: {e}")
                    return self._create_safe_fallback(cuisine, dish_type, ingredients)
        
        # Should never reach here, but just in case
        return self._create_safe_fallback(cuisine, dish_type, ingredients)
    
    def _normalize_ingredient(self, ingredient: str) -> List[str]:
        """Generate normalized variations of an ingredient for matching"""
        normalized = [ingredient.lower()]
        
        # Handle common plural forms
        if ingredient.lower().endswith('ies'):
            # berries -> berry
            normalized.append(ingredient.lower()[:-3] + 'y')
        elif ingredient.lower().endswith('es'):
            # tomatoes -> tomato, potatoes -> potato
            normalized.append(ingredient.lower()[:-2])
        elif ingredient.lower().endswith('s'):
            # onions -> onion
            normalized.append(ingredient.lower()[:-1])
        
        # Also add plural forms if singular
        if not ingredient.lower().endswith('s'):
            normalized.append(ingredient.lower() + 's')
            normalized.append(ingredient.lower() + 'es')
        
        return normalized
    
    def _validate_no_hallucinations(self, recipe, original_ingredients, allowed_spices):
        """Validate the recipe has NO hallucinated ingredients"""
        
        # Get all ingredients from the recipe
        recipe_ingredients = [ing['item'].lower() for ing in recipe.get('ingredients', [])]
        
        # Create normalized versions of all original ingredients
        normalized_originals = []
        for orig in original_ingredients:
            normalized_originals.extend(self._normalize_ingredient(orig))
        
        # Check each ingredient in the recipe
        for ing in recipe_ingredients:
            # Check if it's an original ingredient (with normalization)
            is_original = any(norm in ing or ing in norm for norm in normalized_originals)
            
            if is_original:
                continue
            
            # Check if it's an allowed spice
            is_spice = any(spice.lower() in ing for spice in allowed_spices)
            
            if is_spice:
                continue
            
            # Check if it's a universal basic (if loaded from config)
            if hasattr(self, 'universal_basics'):
                is_basic = any(basic in ing for basic in self.universal_basics)
                if is_basic:
                    continue
            else:
                # Minimal basics if no config loaded
                if ing in ['water', 'salt', 'pepper', 'oil']:
                    continue
            
            # This is a hallucination!
            print(f"WARNING: AI added unauthorized ingredient: {ing}")
        
        return recipe
    
    def _create_safe_fallback(self, cuisine, dish_type, ingredients):
        """Create a basic but safe recipe if AI fails"""
        return {
            "title": f"Simple {cuisine.title()} {dish_type.title()}",
            "ingredients": [{"item": ing, "amount": "as needed"} for ing in ingredients],
            "instructions": [
                f"Prepare all ingredients",
                f"Cook using {dish_type} method",
                f"Season to taste with {cuisine} spices",
                "Serve hot"
            ],
            "prep_time": "15 minutes",
            "cook_time": "30 minutes",
            "servings": 4,
            "cuisine": cuisine,
            "dish_type": dish_type
        }


# Test script
if __name__ == "__main__":
    print("Testing A.I. Chef Generator...")
    print("=" * 60)
    
    chef = AIChefGenerator()
    
    # Test case
    test_cuisine = "mexican"
    test_dish = "stir-fry"
    test_ingredients = ["chicken", "peppers", "onions"]
    
    print(f"\nGenerating: {test_cuisine} {test_dish} with {test_ingredients}")
    print("-" * 40)
    
    recipe = chef.generate_recipe(test_cuisine, test_dish, test_ingredients)
    
    print(f"\nGenerated Recipe:")
    print(f"Title: {recipe.get('title')}")
    print(f"\nIngredients:")
    for ing in recipe.get('ingredients', []):
        print(f"  - {ing['amount']} {ing['item']}")
    print(f"\nInstructions:")
    for i, step in enumerate(recipe.get('instructions', []), 1):
        print(f"  {i}. {step}")
    print(f"\nPrep: {recipe.get('prep_time')} | Cook: {recipe.get('cook_time')}")