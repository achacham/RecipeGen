# /*
# * RecipeGen™ - AI-Powered Culinary Video & Recipe Generation Platform
# * © Copyright By Abraham Chachamovits
# * RecipeGen™ is a trademark of Abraham Chachamovits
# * 
# * File: recipe_matcher_4d.py
# * Purpose: 4D cascade recipe matching system with LOCAL DATABASE PRIORITY
# */

"""
4D Recipe Matching System with Local Database Priority
Now searches LOCAL database first, then falls back to APIs
LAW: We ALWAYS try to avoid the fallback recipe!
"""

import json
import sqlite3
from typing import List, Dict, Optional
from pathlib import Path
from recipe_matcher import recipe_matcher  # Your existing Level 1 matcher
from spoonacular_fetcher import SpoonacularFetcher, API_KEY
from themealdb_fetcher import TheMealDBFetcher
from ai_chef_generator import AIChefGenerator
from itertools import combinations
import time

def generate_protein_combinations(selected_proteins):
    """
    Generate protein combinations in decreasing order.
    Example: [beef, chicken, pork] -> [[beef,chicken,pork], [beef,chicken], [beef,pork], [chicken,pork], [beef], [chicken], [pork]]
    """
    if not selected_proteins:
        return []
    
    all_combinations = []
    # Start from all proteins, decrease to single proteins
    for size in range(len(selected_proteins), 0, -1):
        for combo in combinations(selected_proteins, size):
            all_combinations.append(list(combo))
    
    return all_combinations

class RecipeMatcher4D:
    """
    Implements 4D cascade with LOCAL DATABASE FIRST:
    Level 1: LOCAL RecipeGen database (NEW!)
    Level 2: Multiple APIs (Spoonacular, TheMealDB, etc.)
    Level 3: Sister countries (across LOCAL + APIs!)
    Level 4: Essential fallback (last resort)
    """
    
    def __init__(self):
        # Connect to LOCAL database
        self.db_path = "D:/RecipeGen_Database/processed/recipegen_master.db"
        self.local_db_available = self._check_local_db()
        
        # Enable WAL mode for better concurrency
        if self.local_db_available:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.close()
        
        # Initialize ALL API fetchers (for fallback)
        self.api_providers = {
            'spoonacular': {
                'fetcher': SpoonacularFetcher(API_KEY),
                'name': 'Spoonacular',
                'enabled': True,
                'priority': 1
            },
            'themealdb': {
                'fetcher': TheMealDBFetcher("1"),
                'name': 'TheMealDB',
                'enabled': True,
                'priority': 2
            }
        }
        
        # Sort providers by priority
        self.sorted_providers = sorted(
            [(k, v) for k, v in self.api_providers.items() if v['enabled']],
            key=lambda x: x[1]['priority']
        )
        
        # Load culinary regions
        self.regions_path = Path(__file__).parent / "data" / "culinary_regions.json"
        self.culinary_regions = self._load_culinary_regions()
        
        # Initialize A.I. Chef generator
        self.ai_chef = AIChefGenerator()

        # Load ingredients for cuisine compatibility
        self.ingredients_path = Path(__file__).parent / "data" / "ingredients.json"
        self.ingredients_data = self._load_ingredients_data()
        self.ingredient_cuisines = self._build_ingredient_cuisines()
        
        # SINGLE SOURCE OF TRUTH FOR PROTEINS
        # Build from ingredients.json - look for is_protein field or use default list
        self.PROTEINS = self._build_proteins_list()
        
        # SINGLE SOURCE OF TRUTH FOR MEAT PROTEINS (subset for vegetarian filtering)
        self.MEAT_PROTEINS = self._build_meat_proteins_list()
        
        # Get country to Spoonacular mapping
        self.country_to_spoonacular = self.culinary_regions.get('country_to_spoonacular', {})
        
        # Track sister countries tried
        self.sister_countries_tried = []
        
        print(f"🚀 4D Recipe Matcher initialized {'WITH LOCAL DATABASE' if self.local_db_available else 'WITHOUT local database'}")
        print(f"   📋 Loaded {len(self.PROTEINS)} protein types")

    def _load_ingredients_data(self) -> List[Dict]:
        """Load the full ingredients data"""
        try:
            with open(self.ingredients_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Ingredients database not found!")
            return []
    
    def _build_ingredient_cuisines(self) -> Dict[str, List[str]]:
        """Build cuisine compatibility lookup from ingredients data"""
        ingredient_cuisines = {}
        for ing in self.ingredients_data:
            ingredient_cuisines[ing['slug']] = ing.get('cuisine', [])
        return ingredient_cuisines
    
    def _build_proteins_list(self) -> List[str]:
        """
        Build proteins list from ingredients.json
        First checks for is_protein field, falls back to default list
        """
        proteins = []
        
        # Try to build from ingredients.json with is_protein field
        for ing in self.ingredients_data:
            if ing.get('is_protein', False):
                proteins.append(ing['slug'])
        
        # If no proteins found (is_protein not implemented yet), use comprehensive default
        if not proteins:
            proteins = [
                'chicken', 'beef', 'pork', 'lamb', 'fish', 'prawns', 'shrimp',
                'seafood', 'turkey', 'duck', 'salmon', 'tuna', 'crab', 'lobster',
                'anchovy', 'sardine', 'mackerel', 'trout', 'halibut', 'cod',
                'tilapia', 'catfish', 'bass', 'snapper', 'grouper', 'mahi-mahi',
                'swordfish', 'eel', 'octopus', 'squid', 'calamari', 'scallops',
                'mussels', 'clams', 'oysters', 'veal', 'venison', 'rabbit',
                'goat', 'mutton', 'quail', 'pheasant', 'goose', 'bacon',
                'ham', 'sausage', 'chorizo', 'prosciutto', 'pancetta'
            ]
        
        return proteins
    
    def _build_meat_proteins_list(self) -> List[str]:
        """
        Build list of meat proteins for vegetarian filtering
        This is a subset of all proteins, excluding eggs/dairy
        """
        # For now, return most common meats/fish
        # When is_protein is implemented, can add is_meat flag
        return [
            'chicken', 'beef', 'pork', 'lamb', 'fish', 'prawns', 'shrimp',
            'seafood', 'turkey', 'duck', 'salmon', 'tuna', 'anchovy',
            'sardine', 'mackerel', 'trout', 'halibut', 'cod', 'tilapia',
            'catfish', 'bass', 'snapper', 'veal', 'venison', 'rabbit',
            'goat', 'mutton', 'bacon', 'ham', 'sausage', 'chorizo',
            'prosciutto', 'pancetta', 'crab', 'lobster', 'octopus',
            'squid', 'calamari', 'scallops', 'mussels', 'clams', 'oysters'
        ]

    def _analyze_ingredient_cuisine_fit(self, ingredients: List[str]) -> List[Dict]:
        """
        Analyze which cuisines best match the given ingredients
        Returns list of cuisine suggestions with confidence scores
        """
        print(f"   🔍 DEBUG: Analyzing ingredients: {ingredients}")
        cuisine_scores = {}
        
        # Load from config file instead of hardcoding
        cuisine_indicators = self._load_cuisine_indicators()
        
        # Score each cuisine based on ingredient matches
        for cuisine, indicators in cuisine_indicators.items():
            score = 0
            matched_ingredients = []
            
            for ingredient in ingredients:
                ingredient_lower = ingredient.lower().replace('_', ' ').replace('-', ' ')
                for indicator in indicators:
                    indicator_lower = indicator.replace('_', ' ')
                    if indicator_lower in ingredient_lower or ingredient_lower in indicator_lower:
                        score += 1
                        matched_ingredients.append(ingredient)
                        break
            
            if score > 0:
                cuisine_scores[cuisine] = {
                    'score': score,
                    'matched': matched_ingredients
                }
        
        # Sort by score and create suggestions
        suggestions = []
        for cuisine, data in sorted(cuisine_scores.items(), key=lambda x: x[1]['score'], reverse=True):
            if data['score'] >= 2:  # Need at least 2 matching ingredients
                suggestions.append({
                    'cuisine': cuisine,
                    'confidence': min(0.95, 0.5 + (data['score'] * 0.15)),
                    'match_reason': f"{', '.join(data['matched'][:3])} are common in {cuisine.title()} cooking"
                })
        
        print(f"   🔍 DEBUG: Cuisine scores: {cuisine_scores}")
        print(f"   🔍 DEBUG: Suggestions generated: {suggestions}")
        return suggestions
    
    def _load_cuisine_indicators(self) -> Dict[str, List[str]]:
        """
        Load cuisine indicators from config file or culinary_config.json
        Falls back to defaults if not found
        """
        try:
            # Try to load from culinary_config.json
            config_path = Path(__file__).parent / "data" / "culinary_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('cuisine_indicators', self._get_default_cuisine_indicators())
        except:
            return self._get_default_cuisine_indicators()
    
    def _get_default_cuisine_indicators(self) -> Dict[str, List[str]]:
        """Default cuisine indicators as fallback"""
        return {
            'italian': ['tomato', 'basil', 'oregano', 'olive', 'garlic', 'pasta', 'parmesan', 'mozzarella'],
            'chinese': ['soy_sauce', 'ginger', 'garlic', 'sesame_oil', 'rice_wine', 'scallion', 'rice'],
            'mexican': ['chili_pepper', 'cilantro', 'lime', 'cumin', 'tomato', 'black_bean', 'corn'],
            'thai': ['lemongrass', 'coconut_milk', 'basil', 'lime', 'fish_sauce', 'chili_pepper', 'galangal'],
            'indian': ['cumin', 'turmeric', 'coriander', 'ginger', 'garlic', 'chili_pepper', 'garam_masala'],
            'french': ['butter', 'wine', 'cream', 'thyme', 'tarragon', 'shallot', 'dijon'],
            'japanese': ['soy_sauce', 'miso', 'sake', 'rice_wine', 'sesame', 'nori', 'wasabi'],
            'greek': ['olive', 'feta', 'oregano', 'lemon', 'tomato', 'cucumber', 'yogurt'],
            'spanish': ['olive', 'paprika', 'saffron', 'garlic', 'tomato', 'chorizo', 'sherry'],
            'middle_eastern': ['tahini', 'sumac', 'za_atar', 'pomegranate', 'mint', 'yogurt', 'chickpeas']
        }
    
    def _get_cuisine_typical_ingredients(self, cuisine: str) -> List[str]:
        """
        Get typical ingredients for a given cuisine from ingredients.json
        Returns list of ingredient slugs common to that cuisine
        """
        typical_ingredients = []
        
        # Find ingredients that are associated with this cuisine
        for ingredient_slug, allowed_cuisines in self.ingredient_cuisines.items():
            if allowed_cuisines and cuisine.lower() in [c.lower() for c in allowed_cuisines]:
                typical_ingredients.append(ingredient_slug)
        
        # If we found ingredients for this cuisine, return the first 8
        if typical_ingredients:
            return typical_ingredients[:8]
        
        # Try to find ingredients for related cuisines (e.g., 'nordic' for 'danish')
        region = self._get_region_for_country(cuisine.lower())
        if region:
            for country in region.get('countries', []):
                for ingredient_slug, allowed_cuisines in self.ingredient_cuisines.items():
                    if allowed_cuisines and country in [c.lower() for c in allowed_cuisines]:
                        typical_ingredients.append(ingredient_slug)
            
            if typical_ingredients:
                return list(set(typical_ingredients))[:8]  # Remove duplicates, return first 8
        
        # Default fallback ingredients
        return ['onion', 'garlic', 'tomato', 'olive_oil', 'salt']

    def _load_ingredient_families(self) -> Dict[str, Dict]:
        """Load ingredient family mappings for smart search"""
        try:
            families_path = Path(__file__).parent / "data" / "ingredient_families.json"
            with open(families_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default families if file doesn't exist
            return {
                'chicken': {
                    'includes': ['chicken', 'chicken_breast', 'chicken_thigh', 'chicken_wing', 
                                'chicken_leg', 'chicken_drumstick', 'whole_chicken'],
                    'search_behavior': 'inclusive'
                },
                'beef': {
                    'includes': ['beef', 'ground_beef', 'beef_steak', 'beef_roast', 
                                'beef_brisket', 'beef_ribs'],
                    'search_behavior': 'inclusive'
                }
            }

    def _check_local_db(self) -> bool:
        """Check if local database exists and is accessible"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM recipes")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"📚 Local database connected: {count} recipes available")
            return True
        except:
            print("⚠️ Local database not found - will use APIs only")
            return False
    
    def _search_local_database(self, cuisine: str, ingredients: List[str], dish_type: str) -> Optional[Dict]:
        """
        Search LOCAL RecipeGen database with SMART ingredient matching!
        Handles chicken → all chicken parts, but preserves specificity
        """
        if not self.local_db_available:
            return None
        
        # Load ingredient families for smart matching
        ingredient_families = self._load_ingredient_families()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Use centralized PROTEINS list
            requested_proteins = [ing for ing in ingredients if ing.lower() in self.PROTEINS]
            has_protein_request = len(requested_proteins) > 0
            
            # Generate protein combinations for progressive matching
            if has_protein_request and len(requested_proteins) > 1:
                protein_combinations = generate_protein_combinations(requested_proteins)
                print(f"   🥩 Multiple proteins requested: {requested_proteins}")
                print(f"   🔄 Will try combinations: {protein_combinations}")
            else:
                protein_combinations = [requested_proteins] if requested_proteins else []
            
            # Expand ingredients based on families
            expanded_ingredients = []
            for ingredient in ingredients:
                if ingredient in ingredient_families:
                    # This is a family search (e.g., "chicken" finds all parts)
                    family = ingredient_families[ingredient]
                    if family.get('search_behavior') == 'inclusive':
                        expanded_ingredients.extend(family['includes'])
                    else:
                        expanded_ingredients.append(ingredient)
                else:
                    # Regular ingredient
                    expanded_ingredients.append(ingredient)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_ingredients = []
            for ing in expanded_ingredients:
                if ing not in seen:
                    seen.add(ing)
                    unique_ingredients.append(ing)
            expanded_ingredients = unique_ingredients
            
            # First try exact match with cuisine and ingredients
            ingredient_conditions = []
            params = [cuisine.lower()]

            # Add dish type if specified AND not 'any'
            dish_type_condition = ""
            if dish_type and dish_type != 'any':
                dish_type_condition = "AND r.dish_type = ?"
                params.append(dish_type.lower())
            
            # Build query for expanded ingredients
            if expanded_ingredients:
                ingredient_conditions.append(f'''
                    EXISTS (
                        SELECT 1 FROM recipe_ingredients ri 
                        WHERE ri.recipe_id = r.id 
                        AND ri.ingredient_slug IN ({','.join(['?'] * len(expanded_ingredients))})
                    )
                ''')
                params.extend(expanded_ingredients)
            
                       
            # Build the full query
            query = f'''
                SELECT r.id, r.title, r.cuisine, r.dish_type, r.ingredients, 
                       r.instructions, r.prep_time, r.cook_time, r.servings,
                       r.source, r.image_url, r.quality_score
                FROM recipes r
                WHERE r.cuisine = ?
                {dish_type_condition}
                {"AND " + " AND ".join(ingredient_conditions) if ingredient_conditions else ""}
                ORDER BY r.quality_score DESC, r.times_served DESC
                LIMIT 10
            '''
            
            # Execute query and validate protein matches
            cursor.execute(query, params)
            temp_results = cursor.fetchall()

            # Right before the validation
            print(f"   🔍 Validating {len(temp_results)} recipes for protein match...", flush=True)
            
            # VALIDATE PROTEIN MATCH
            results = []
            if has_protein_request:
                # Try each protein combination in order (all → fewer → single)
                for protein_combo in protein_combinations:
                    combo_results = []
                    
                    for recipe_row in temp_results:
                        recipe_data = json.loads(recipe_row[4])  # ingredients column
                        recipe_ingredients_text = json.dumps(recipe_data).lower()
                        
                        # Check if ALL proteins in this combination are present
                        proteins_matched = sum(1 for protein in protein_combo 
                                             if protein in recipe_ingredients_text)
                        
                        if proteins_matched == len(protein_combo):
                            # Perfect match for this combination!
                            combo_results.append((recipe_row, len(protein_combo)))
                            print(f"   ✅ Found recipe with {protein_combo}: '{recipe_row[1]}'")
                    
                    if combo_results:
                        # Sort by protein match count (more proteins = better)
                        combo_results.sort(key=lambda x: x[1], reverse=True)
                        results = [row for row, count in combo_results]
                        print(f"   🎯 Using recipes with {len(protein_combo)} protein(s): {protein_combo}")
                        break  # Stop at first successful combination
                
                if not results and temp_results:
                    print(f"   ❌ No recipes found with requested protein combinations")
            else:
                # No protein specified - prefer vegetarian (use centralized MEAT_PROTEINS)
                for recipe_row in temp_results:
                    recipe_data = json.loads(recipe_row[4])
                    recipe_ingredients_text = json.dumps(recipe_data).lower()
                    
                    # Check if ANY meat protein is in this recipe
                    has_meat = any(meat in recipe_ingredients_text for meat in self.MEAT_PROTEINS)
                    
                    if not has_meat:
                        results.append(recipe_row)  # Vegetarian-friendly
                    else:
                        rejection_msg = f"   ❌ Rejected '{recipe_row[1]}' - contains meat (user selected no protein)"
                        print(rejection_msg, flush=True)
                        import sys
                        sys.stdout.flush()
            
            if results:
                # Convert to RecipeGen format
                best_recipe = results[0]  # Highest quality/most served
                recipe = {
                    'id': best_recipe[0],
                    'title': best_recipe[1],
                    'cuisine': best_recipe[2],
                    'dish_type': best_recipe[3],
                    'ingredients': json.loads(best_recipe[4]),
                    'instructions': json.loads(best_recipe[5]),
                    'prep_time': best_recipe[6],
                    'cook_time': best_recipe[7],
                    'servings': best_recipe[8],
                    'source': 'local_database',
                    'source_api': best_recipe[9],
                    'image_url': best_recipe[10],
                    'quality_score': best_recipe[11]
                }
                
                # Update times served
                cursor.execute(
                    "UPDATE recipes SET times_served = times_served + 1 WHERE id = ?",
                    (best_recipe[0],)
                )
                conn.commit()
                
                print(f"   ✅ Found in LOCAL database: {recipe['title']}")
                conn.close()
                return recipe
            
            # Try relaxed search - cuisine only with partial ingredient match
            # BUT STILL APPLY PROTEIN VALIDATION
            if not results and ingredients:
                cursor.execute('''
                    SELECT r.id, r.title, r.cuisine, r.dish_type, r.ingredients, 
                           r.instructions, r.prep_time, r.cook_time, r.servings,
                           r.source, r.image_url, r.quality_score,
                           COUNT(DISTINCT ri.ingredient_slug) as ingredient_matches
                    FROM recipes r
                    LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id 
                        AND ri.ingredient_slug IN ({})
                    WHERE r.cuisine = ?
                    {}
                    GROUP BY r.id
                    HAVING ingredient_matches > 0
                    ORDER BY ingredient_matches DESC, r.quality_score DESC
                    LIMIT 5
                '''.format(','.join(['?'] * len(expanded_ingredients)), dish_type_condition),
                    expanded_ingredients + [cuisine.lower()] + ([dish_type.lower()] if dish_type and dish_type != 'any' else [])
                )
                
                partial_matches = cursor.fetchall()
                
                # Apply progressive protein validation to partial matches
                validated_partial = []
                
                if has_protein_request:
                    # Try each protein combination for partial matches
                    for protein_combo in protein_combinations:
                        for match in partial_matches:
                            recipe_data = json.loads(match[4])
                            recipe_ingredients_text = json.dumps(recipe_data).lower()
                            
                            # Check if ALL proteins in this combination are present
                            proteins_matched = sum(1 for protein in protein_combo 
                                                 if protein in recipe_ingredients_text)
                            
                            if proteins_matched == len(protein_combo):
                                # Add with protein match count for sorting
                                validated_partial.append((match, len(protein_combo)))
                        
                        if validated_partial:
                            # Sort by protein count, then take just the matches
                            validated_partial.sort(key=lambda x: x[1], reverse=True)
                            validated_partial = [match for match, count in validated_partial]
                            print(f"   🎯 Partial matches found with {protein_combo}")
                            break
                else:
                    # Should not have meat (vegetarian preference) - use centralized list
                    for match in partial_matches:
                        recipe_data = json.loads(match[4])
                        recipe_ingredients_text = json.dumps(recipe_data).lower()
                        
                        has_meat = any(meat in recipe_ingredients_text for meat in self.MEAT_PROTEINS)
                        if not has_meat:
                            validated_partial.append(match)
                
                if validated_partial:
                    best_match = validated_partial[0]
                    recipe = {
                        'id': best_match[0],
                        'title': best_match[1],
                        'cuisine': best_match[2],
                        'dish_type': best_match[3],
                        'ingredients': json.loads(best_match[4]),
                        'instructions': json.loads(best_match[5]),
                        'prep_time': best_match[6],
                        'cook_time': best_match[7],
                        'servings': best_match[8],
                        'source': 'local_database',
                        'source_api': best_match[9],
                        'image_url': best_match[10],
                        'quality_score': best_match[11],
                        'partial_match': True,
                        'matched_ingredients': best_match[12]
                    }
                    
                    print(f"   ✅ Found partial match in LOCAL database: {recipe['title']} ({best_match[12]}/{len(ingredients)} ingredients)")
                    conn.close()
                    return recipe
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Error searching local database: {e}")
        
        return None
    
    def _load_culinary_regions(self) -> Dict:
        """Load culinary regions mapping"""
        try:
            with open(self.regions_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Culinary regions not found. Run culinary_regions_updater.py!")
            return {'regions': {}, 'country_to_spoonacular': {}}
    
    def _ingredients_compatible_with_country(self, ingredient_slugs: List[str], country: str) -> bool:
        """Check if ingredients can be used in this country's cuisine - BE LENIENT!"""
        if not self.ingredient_cuisines:
            return True
        
        incompatible_count = 0
        for ingredient in ingredient_slugs:
            if ingredient in self.ingredient_cuisines:
                allowed_countries = self.ingredient_cuisines[ingredient]
                if allowed_countries and len(allowed_countries) > 0 and country not in allowed_countries:
                    incompatible_count += 1
        
        # Allow if MOST ingredients work (not ALL)
        return incompatible_count < len(ingredient_slugs) / 2
    
    def _ingredients_compatible_with_spoonacular_cuisine(self, ingredient_slugs: List[str], spoon_cuisine: str) -> bool:
        """Check if ingredients work with a Spoonacular cuisine category"""
        # Find all countries that map to this Spoonacular cuisine
        countries_in_cuisine = []
        for country, cuisine in self.country_to_spoonacular.items():
            if cuisine == spoon_cuisine:
                countries_in_cuisine.append(country)
        
        # If ANY country in this cuisine can use all ingredients, it's compatible
        for country in countries_in_cuisine:
            if self._ingredients_compatible_with_country(ingredient_slugs, country):
                return True
        
        return False
    
    def _search_all_apis(self, cuisine_term: str, ingredients: List[str], 
                    dish_type: str = None,
                    search_type: str = "primary") -> Optional[Dict]:
        """
        Search across ALL enabled API providers
        Returns first good result found
        """
        print(f"\n   🌐 Searching across {len(self.sorted_providers)} API providers...")
        
        for provider_key, provider_info in self.sorted_providers:
            fetcher = provider_info['fetcher']
            provider_name = provider_info['name']
            
            print(f"\n      📡 Trying {provider_name}...")
            
            try:
                # Each fetcher implements search_recipes with same interface
                results = fetcher.search_recipes(cuisine_term, ingredients, number=10)
                
                if 'results' in results and results['results']:
                    print(f"         {provider_name} returned: {len(results['results'])} recipes")
                    
                    # Check each recipe for quality
                    for recipe_summary in results['results']:
                        if fetcher.is_quality_recipe(recipe_summary):
                            # Get full details and convert to RecipeGen format
                            full_recipe = fetcher.get_recipe_details(recipe_summary['id'])
                            
                            # CONVERT TO OUR RELIGION FIRST! 🙏
                            # Each provider's converter knows how to map their fields to ours
                            try:
                                formatted = fetcher.convert_to_recipegen_format(full_recipe)
                            except Exception as e:
                                print(f"      ⚠️ Conversion failed for '{recipe_summary.get('title', 'Unknown')}': {e}")
                                continue  # Skip malformed data

                            # Progressive protein matching using centralized lists
                            requested_proteins = [ing for ing in ingredients if ing.lower() in self.PROTEINS]
                            has_protein_request = len(requested_proteins) > 0
                            
                            # Check protein match
                            if has_protein_request:
                                # Multiple proteins - need progressive matching
                                if len(requested_proteins) > 1:
                                    protein_combinations = generate_protein_combinations(requested_proteins)
                                    recipe_ingredients = str(formatted.get('all_ingredients', [])).lower()
                                    
                                    # Find best protein match
                                    best_match_count = 0
                                    for protein_combo in protein_combinations:
                                        proteins_matched = sum(1 for protein in protein_combo 
                                                             if protein in recipe_ingredients)
                                        if proteins_matched == len(protein_combo) and len(protein_combo) > best_match_count:
                                            best_match_count = len(protein_combo)
                                            break  # Found a match at this level
                                    
                                    if best_match_count == 0:
                                        print(f"      ❌ Skipped '{formatted.get('title', 'Unknown')}' - no requested proteins found")
                                        continue
                                    elif best_match_count < len(requested_proteins):
                                        print(f"      ⚠️  '{formatted.get('title', 'Unknown')}' - partial protein match ({best_match_count}/{len(requested_proteins)})")
                                else:
                                    # Single protein - simple check
                                    recipe_ingredients = str(formatted.get('all_ingredients', [])).lower()
                                    if requested_proteins[0] not in recipe_ingredients:
                                        print(f"      ❌ Skipped '{formatted.get('title', 'Unknown')}' - missing {requested_proteins[0]}")
                                        continue
                            else:
                                # No protein requested - vegetarian preference using centralized list
                                recipe_ingredients = formatted.get('all_ingredients', [])
                                has_meat = any(meat in str(recipe_ingredients).lower() for meat in self.MEAT_PROTEINS)
                                
                                if has_meat:
                                    print(f"      ❌ Skipped '{formatted.get('title', 'Unknown')}' - contains meat/fish (vegetarian preference)")
                                    continue

                            # NOW verify dish type on OUR standardized structure
                            if dish_type and dish_type != 'any':
                                if not self._verify_dish_type_match(formatted, dish_type):
                                    print(f"      ❌ Skipped '{formatted.get('title', 'Unknown')}' - not a {dish_type}")
                                    continue  # Skip this recipe, try next one

                            # Validate cuisine match on OUR structure
                            recipe_cuisines = formatted.get('cuisines', [])
                            if not isinstance(recipe_cuisines, list):
                                recipe_cuisines = []
                        
                            recipe_cuisines_lower = [c.lower() for c in recipe_cuisines]
                            cuisine_term_lower = cuisine_term.lower()
    
                            # Check if the cuisine matches (be somewhat flexible)
                            if (cuisine_term_lower in recipe_cuisines_lower or 
                                any(cuisine_term_lower in c for c in recipe_cuisines_lower) or
                                len(recipe_cuisines) == 0):  # If no cuisine specified, accept it
                                print(f"      ✅ Found on {provider_name}: {formatted['title']}")
                                formatted['source_api'] = provider_name
                                return formatted
                            else:
                                print(f"      ❌ Skipped '{formatted['title']}' - cuisines {recipe_cuisines} don't match {cuisine_term}")
                    
            except Exception as e:
                import traceback
                print(f"         ⚠️ Error with {provider_name}: {str(e)}")
                print(f"         Full traceback: {traceback.format_exc()}")
                # Continue to next provider
        
        return None
    
    def _search_all_apis_with_verification(self, cuisine_term: str, ingredients: List[str], 
                                     required_dish_type: str) -> Optional[Dict]:
        """
        Search APIs and VERIFY the result matches the dish type!
        """
        print(f"\n   🎯 Searching for verified {required_dish_type} recipes...")
        
        for provider_key, provider_info in self.sorted_providers:
            fetcher = provider_info['fetcher']
            provider_name = provider_info['name']
            
            try:
                # Get MORE results to increase chance of finding correct dish type
                results = fetcher.search_recipes(cuisine_term, ingredients, number=20)
                
                if 'results' in results and results['results']:
                    print(f"         {provider_name} returned {len(results['results'])} to verify...")
                    
                    # Check EACH result for dish type match
                    for recipe_summary in results['results']:
                        if fetcher.is_quality_recipe(recipe_summary):
                            # Get full recipe to analyze
                            full_recipe = fetcher.get_recipe_details(recipe_summary['id'])
                            
                            # CONVERT FIRST!
                            try:
                                formatted = fetcher.convert_to_recipegen_format(full_recipe)
                            except Exception as e:
                                print(f"      ⚠️ Conversion failed for '{recipe_summary.get('title', 'Unknown')}': {e}")
                                continue
                            
                            # Progressive protein matching using centralized lists
                            requested_proteins = [ing for ing in ingredients if ing.lower() in self.PROTEINS]
                            has_protein_request = len(requested_proteins) > 0
                            
                            # Check protein match
                            if has_protein_request:
                                # Multiple proteins - need progressive matching
                                if len(requested_proteins) > 1:
                                    protein_combinations = generate_protein_combinations(requested_proteins)
                                    recipe_ingredients = str(formatted.get('all_ingredients', [])).lower()
                                    
                                    # Find best protein match
                                    best_match_count = 0
                                    for protein_combo in protein_combinations:
                                        proteins_matched = sum(1 for protein in protein_combo 
                                                             if protein in recipe_ingredients)
                                        if proteins_matched == len(protein_combo) and len(protein_combo) > best_match_count:
                                            best_match_count = len(protein_combo)
                                            break  # Found a match at this level
                                    
                                    if best_match_count == 0:
                                        print(f"      ❌ Skipped '{formatted.get('title', 'Unknown')}' - no requested proteins found")
                                        continue
                                    elif best_match_count < len(requested_proteins):
                                        print(f"      ⚠️  '{formatted.get('title', 'Unknown')}' - partial protein match ({best_match_count}/{len(requested_proteins)})")
                                else:
                                    # Single protein - simple check
                                    recipe_ingredients = str(formatted.get('all_ingredients', [])).lower()
                                    if requested_proteins[0] not in recipe_ingredients:
                                        print(f"      ❌ Skipped '{formatted.get('title', 'Unknown')}' - missing {requested_proteins[0]}")
                                        continue
                            else:
                                # No protein requested - vegetarian preference using centralized list
                                recipe_ingredients = formatted.get('all_ingredients', [])
                                has_meat = any(meat in str(recipe_ingredients).lower() for meat in self.MEAT_PROTEINS)
                                
                                if has_meat:
                                    print(f"      ❌ Skipped '{formatted.get('title', 'Unknown')}' - contains meat/fish (vegetarian preference)")
                                    continue

                            # NOW verify on OUR converted format
                            if self._verify_dish_type_match(formatted, required_dish_type):
                                print(f"      ✅ VERIFIED {required_dish_type}: {formatted['title']}")
                                formatted['source_api'] = provider_name
                                formatted['verified_dish_type'] = True
                                return formatted
                            else:
                                title = formatted.get('title', 'Unknown')
                                print(f"         ↳ Skipped '{title}' - not a {required_dish_type}")
                                                    
            except Exception as e:
                print(f"         ⚠️ Error with {provider_name}: {str(e)}")
                            
            return None
    
    def _verify_dish_type_match(self, recipe: Dict, required_dish_type: str) -> bool:
        """
        Intelligently verify if a recipe matches the required dish type
        """
        # TRUST THE CONVERTER! If it already set the correct dish_type, we're done!
        if recipe.get('dish_type') == required_dish_type:
            print(f"         ✅ Dish type already confirmed by converter: {recipe.get('dish_type')}")
            return True

        # Load dish type indicators from config or use defaults
        dish_type_indicators = self._load_dish_type_indicators()
        
        indicators = dish_type_indicators.get(required_dish_type, {})
        if not indicators:
            return True  # Unknown dish type, be permissive
        
        score = 0
        max_score = 0
        
        # Check title (most reliable indicator)
        title = recipe.get('title', '').lower()
        if any(word in title for word in indicators.get('title_words', [])):
            score += 4  # Strong indicator!
        max_score += 4
        
        # Check cooking time
        total_time = recipe.get('readyInMinutes', 0) or (recipe.get('cook_time', 0) or 0) + (recipe.get('prep_time', 0) or 0)
        if 'time_limit' in indicators and total_time > 0 and total_time <= indicators['time_limit']:
            score += 2
        if 'time_min' in indicators and total_time >= indicators['time_min']:
            score += 2
        if 'time_limit' in indicators or 'time_min' in indicators:
            max_score += 2
        
        # Check instructions (if available)
        instructions_text = ''
        if 'analyzedInstructions' in recipe:
            for instruction_set in recipe.get('analyzedInstructions', []):
                for step in instruction_set.get('steps', []):
                    instructions_text += ' ' + step.get('step', '')
        elif 'steps' in recipe:
            for step in recipe.get('steps', []):
                instructions_text += ' ' + step.get('instruction', '')
        
        instructions_lower = instructions_text.lower()
        
        if instructions_text:
            pattern_matches = sum(1 for pattern in indicators.get('instruction_patterns', []) 
                                 if pattern in instructions_lower)
            score += min(pattern_matches, 3)  # Cap at 3 points
            max_score += 3
            
            # Check equipment mentions
            equipment_matches = sum(1 for equip in indicators.get('equipment', [])
                                   if equip in instructions_lower)
            score += min(equipment_matches, 2)  # Cap at 2 points
            max_score += 2
        
        # Check ingredients (if specified)
        if 'ingredients' in indicators:
            recipe_ingredients = []
            if 'all_ingredients' in recipe:
                recipe_ingredients = [ing.get('slug', '').lower() for ing in recipe.get('all_ingredients', [])]
            elif 'ingredients' in recipe:
                recipe_ingredients = [ing.get('slug', '').lower() for ing in recipe.get('ingredients', [])]
            
            ingredient_matches = sum(1 for ing in indicators['ingredients'] 
                                   if any(ing in r_ing for r_ing in recipe_ingredients))
            if ingredient_matches > 0:
                score += 2
            max_score += 2
        
        # Calculate percentage match
        if max_score > 0:
            match_percentage = (score / max_score) * 100
            print(f"         ↳ Dish type match score: {score}/{max_score} ({match_percentage:.0f}%)")
            return match_percentage >= 60  # Need 60% confidence
        
        return False
    
    def _load_dish_type_indicators(self) -> Dict:
        """Load dish type indicators from config or use defaults"""
        try:
            config_path = Path(__file__).parent / "data" / "culinary_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('dish_type_indicators', self._get_default_dish_type_indicators())
        except:
            return self._get_default_dish_type_indicators()
    
    def _get_default_dish_type_indicators(self) -> Dict:
        """Default dish type indicators"""
        return {
            'stir-fry': {
                'title_words': ['stir-fry', 'stir-fried', 'wok', 'stirfry', 'fried'],
                'instruction_patterns': ['stir', 'wok', 'high heat', 'toss', 'quickly', 'saute'],
                'time_limit': 30,
                'equipment': ['wok', 'skillet', 'pan']
            },
            'baked-dish': {
                'title_words': ['baked', 'roasted', 'casserole', 'gratin', 'pie'],
                'instruction_patterns': ['oven', 'bake', 'roast', 'degrees', 'preheat', 'baking dish'],
                'time_min': 25,
                'equipment': ['oven', 'baking dish', 'casserole dish']
            },
            'curry': {
                'title_words': ['curry', 'korma', 'masala', 'vindaloo', 'tikka'],
                'instruction_patterns': ['simmer', 'sauce', 'gravy', 'spices', 'coconut milk', 'curry powder'],
                'ingredients': ['curry', 'turmeric', 'cumin', 'coriander', 'garam_masala'],
                'equipment': ['pot', 'pan', 'kadai']
            },
            'soup': {
                'title_words': ['soup', 'stew', 'broth', 'bisque', 'chowder', 'consomme'],
                'instruction_patterns': ['simmer', 'boil', 'broth', 'stock', 'ladle', 'liquid'],
                'time_min': 20,
                'equipment': ['pot', 'saucepan', 'stockpot']
            },
            'pasta': {
                'title_words': ['pasta', 'spaghetti', 'penne', 'linguine', 'fettuccine', 'noodles'],
                'instruction_patterns': ['boil', 'pasta', 'al dente', 'drain', 'sauce'],
                'ingredients': ['pasta', 'spaghetti', 'penne', 'noodles'],
                'equipment': ['pot', 'colander']
            },
            'salad': {
                'title_words': ['salad', 'slaw', 'fresh', 'raw'],
                'instruction_patterns': ['toss', 'mix', 'dress', 'combine', 'chill', 'refrigerate'],
                'time_limit': 20,
                'no_cooking': True
            },
            'wrap': {
                'title_words': ['wrap', 'burrito', 'tortilla', 'roll'],
                'instruction_patterns': ['wrap', 'roll', 'fold', 'tortilla'],
                'equipment': ['pan', 'griddle']
            },
            'sandwich': {
                'title_words': ['sandwich', 'burger', 'sub', 'hoagie', 'panini'],
                'instruction_patterns': ['layer', 'stack', 'bread', 'bun'],
                'equipment': ['grill', 'pan', 'toaster']
            }
        }
    
    def find_recipe(self, cuisine: str, ingredients: List[str], dish_type: str, chef_preference: str = 'traditional') -> Optional[Dict]:
        """
        4D Recipe Search with LOCAL DATABASE PRIORITY
        """
        print(f"\n🎯 4D RECIPE SEARCH: {cuisine} {dish_type} with {ingredients}")
        print(f"👨‍🍳 Chef preference: {chef_preference}")
        self.chef_preference = chef_preference
        cuisine_lower = cuisine.lower().strip()
        
        # Reset tracking
        self.sister_countries_tried = []
        
        # NEW LEVEL 1: Search LOCAL RecipeGen database FIRST!
        if self.local_db_available:
            print("📚 LEVEL 1: Searching LOCAL RecipeGen database...")
            local_recipe = self._search_local_database(cuisine_lower, ingredients, dish_type)
            
            if local_recipe:
                # Validate cuisine match
                recipe_cuisine = local_recipe.get('cuisine', '').lower().strip()
                if recipe_cuisine == cuisine_lower:
                    return local_recipe
                else:
                    print(f"❌ Cuisine mismatch: wanted '{cuisine}', got '{recipe_cuisine}' - continuing search")
        
        # LEVEL 2: Search ALL APIs with regional mapping
        print("\n🌍 LEVEL 2: Multi-API search with regional mapping...")

        # FIRST: Try exact cuisine name without mapping
        print(f"   Trying exact cuisine: '{cuisine}'")

        # Check if this cuisine is even supported by the APIs
        # If not directly supported, skip to mapping phase
        known_spoonacular_cuisines = ['african', 'american', 'british', 'cajun', 'caribbean', 'chinese', 
                                    'eastern european', 'european', 'french', 'german', 'greek', 
                                    'indian', 'irish', 'italian', 'japanese', 'jewish', 'korean', 
                                    'latin american', 'mediterranean', 'mexican', 'middle eastern', 
                                    'nordic', 'southern', 'spanish', 'thai', 'vietnamese']

        if cuisine.lower() in known_spoonacular_cuisines:
            exact_recipe = self._search_all_apis(cuisine, ingredients, dish_type, "primary")
            if exact_recipe:
                self._save_to_local_db(exact_recipe)
                return exact_recipe
        else:
            print(f"   ❌ '{cuisine}' not directly supported by APIs - skipping to mapping")

        # THEN: Try with Spoonacular mapping if exact didn't work
        spoon_cuisine = self.country_to_spoonacular.get(cuisine_lower)

        if spoon_cuisine and spoon_cuisine.lower() != cuisine_lower:
            if self._ingredients_compatible_with_country(ingredients, cuisine_lower):
                print(f"   ✓ Mapping '{cuisine}' → '{spoon_cuisine}'")
                print(f"   ✓ Ingredients compatible with {spoon_cuisine}")
                
                api_recipe = self._search_all_apis(spoon_cuisine, ingredients, dish_type, "primary")
                if api_recipe:
                    self._save_to_local_db(api_recipe)
                    return api_recipe
            else:
                print(f"   ❌ Ingredients not compatible with {spoon_cuisine} cuisine")
        else:
            print(f"   ❌ No different cuisine mapping found for '{cuisine}'")
        
        # LEVEL 3: Try sister countries across LOCAL DB + ALL APIs
        print("\n🌐 LEVEL 3: Searching sister countries...")
        region = self._get_region_for_country(cuisine_lower)
        
        if region:
            print(f"   ✓ Found region: {region.get('name', 'Unknown')}")
            sister_countries = [c for c in region.get('countries', []) if c != cuisine_lower]
            
            # Find compatible sisters
            compatible_sisters = []
            for sister in sister_countries:
                if self._ingredients_compatible_with_country(ingredients, sister):
                    compatible_sisters.append(sister)
            
            if compatible_sisters:
                print(f"   ✓ Compatible sister countries: {compatible_sisters[:5]}...")
                self.sister_countries_tried = compatible_sisters[:5]
                
                # Try each compatible sister in LOCAL DB first
                for sister in compatible_sisters:
                    # Try local database first
                    if self.local_db_available:
                        print(f"\n   🔄 Trying sister country in LOCAL DB: {sister}")
                        local_sister = self._search_local_database(sister, ingredients, dish_type)
                        if local_sister:
                            local_sister['note'] = f"Similar {sister.title()} recipe"
                            return local_sister
                    
                    # Then try APIs
                    sister_spoon = self.country_to_spoonacular.get(sister)
                    if sister_spoon:
                        print(f"   🔄 Trying sister country in APIs: {sister} ({sister_spoon})")
                        
                        api_recipe = self._search_all_apis(sister_spoon, ingredients, dish_type, "sister")
                        if api_recipe:
                            api_recipe['note'] = f"Similar {sister.title()} recipe"
                            self._save_to_local_db(api_recipe)
                            return api_recipe
            else:
                print(f"   ❌ No compatible sister countries found")
        else:
            print(f"   ❌ No regional mapping found for '{cuisine}'")
        
        # LEVEL 4: Generate REAL recipe with AI
        print(f"\n🤖 LEVEL 4: Generating REAL recipe with AI Chef...")
        
        # Build proper ingredient list for AI
        ingredient_names = []
        for ing in ingredients:
            # Get actual ingredient names from our data
            for ing_data in self.ingredients_data:
                if ing_data['slug'] == ing:
                    ingredient_names.append(ing_data['name'])
                    break
            else:
                # If not found in data, use the slug cleaned up
                ingredient_names.append(ing.replace('_', ' ').title())
        
        try:
            # AI Chef should ALWAYS generate something real
            ai_recipe = self.ai_chef.generate_recipe(cuisine, dish_type, ingredient_names)
            
            if ai_recipe and 'instructions' in ai_recipe and len(ai_recipe.get('instructions', [])) > 4:
                print(f"   ✅ AI Chef generated: {ai_recipe.get('title', 'AI Recipe')}")
                
                # Ensure all required fields
                ai_recipe['cuisine'] = cuisine
                ai_recipe['dish_type'] = dish_type
                ai_recipe['source'] = 'ai_chef'
                ai_recipe['source_api'] = 'AI Chef'
                
                # Save to database for future use
                self._save_to_local_db(ai_recipe)
                
                # Add alternatives for user
                ai_recipe['alternatives'] = self._generate_smart_alternatives(cuisine, dish_type, ingredients)
                
                return ai_recipe
                
        except Exception as e:
            print(f"   ❌ AI Chef error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # This should NEVER happen - AI should always work
        # But if it does, we MUST return something
        print("   🆘 CRITICAL: AI Chef failed - this should not happen!")
        print("   🆘 Check OpenAI API key and connection")
        
        # Return error state that main.py can handle
        return {
            'type': 'generation_failed',
            'error': 'AI Chef service unavailable',
            'cuisine': cuisine,
            'dish_type': dish_type,
            'ingredients': ingredients,
            'alternatives': self._generate_smart_alternatives(cuisine, dish_type, ingredients)
        }

    
    def _save_to_local_db(self, recipe: Dict):
        """Save API recipe to local database for future use"""
        if not self.local_db_available:
            return
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Generate unique ID FIRST
            import time
            if recipe.get('id'):
                recipe_id = f"{recipe.get('source_api', 'api')}_{recipe.get('id')}"
            else:
                # No ID from API, use title + timestamp to ensure uniqueness
                recipe_id = f"{recipe.get('source_api', 'api')}_{recipe['title'].replace(' ', '_').lower()}_{int(time.time())}"

            # THEN check if already exists
            cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
            if cursor.fetchone():
                conn.close()
                return  # Already in database
                                
            # Insert recipe
            cursor.execute('''
                INSERT INTO recipes (
                    id, title, cuisine, dish_type, ingredients, instructions,
                    prep_time, cook_time, total_time, servings,
                    source, source_id, source_url, image_url,
                    quality_score, is_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe_id,
                recipe.get('title'),
                recipe.get('cuisine', '').lower(),
                recipe.get('dish_type', '').lower(),
                json.dumps(recipe.get('ingredients', [])),
                json.dumps(recipe.get('instructions', [])),
                recipe.get('prep_time'),
                recipe.get('cook_time'),
                recipe.get('total_time'),
                recipe.get('servings'),
                recipe.get('source_api'),
                recipe.get('id'),
                recipe.get('source_url'),
                recipe.get('image_url'),
                recipe.get('quality_score', 60),
                recipe.get('verified_dish_type', False)
            ))
            
            # Insert ingredients for searching - INDENT THIS PROPERLY!
            for ing in recipe.get('ingredients', []):
                # Handle both formats: AI Chef uses 'item', APIs use 'name'/'slug'
                ingredient_name = ing.get('item') or ing.get('name', '')
                ingredient_slug = ing.get('slug', '')
                
                # If no slug, create one from the name
                if not ingredient_slug and ingredient_name:
                    ingredient_slug = ingredient_name.lower().replace(' ', '_')
                
                cursor.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_slug, ingredient_name, amount)
                    VALUES (?, ?, ?, ?)
                ''', (
                    recipe_id,
                    ingredient_slug,
                    ingredient_name,
                    ing.get('amount', '')
                ))
            
            conn.commit()
            conn.close()
            print(f"   💾 Saved to local database for future use!")
            
        except Exception as e:
            print(f"   ⚠️ Could not save to local database: {e}")
    
    def _determine_failure_reason(self, cuisine: str, dish_type: str, ingredients: List[str]) -> str:
        """Analyze why we couldn't find a match"""
        
        # Load common cooking methods by cuisine from culinary_regions.json
        cuisine_methods = self.culinary_regions.get('cuisine_cooking_methods', {})
        
        # Check if it's an unusual combination
        if cuisine in cuisine_methods:
            common_methods = cuisine_methods.get(cuisine, [])
            if dish_type not in common_methods:
                return f"{cuisine.title()} cuisine rarely uses {dish_type} cooking method"
        
        # Check for specific ingredient-method incompatibilities
        if dish_type == 'baked-dish' and any(ing in ['galangal', 'lemongrass', 'fish-sauce'] for ing in ingredients):
            return "Southeast Asian aromatics are typically used in stir-fries or curries, not baked dishes"
        
        if dish_type == 'dessert' and any(ing in ['fish-sauce', 'shrimp-paste', 'galangal'] for ing in ingredients):
            return "These savory ingredients are not typically used in desserts"
        
        # Default reason
        return f"No {cuisine.title()} {dish_type} recipes found with these specific ingredients"
    
    def _generate_smart_alternatives(self, cuisine: str, dish_type: str, ingredients: List[str]) -> List[Dict]:
        """
        Generate alternatives - but check LOCAL DB first, then verify with APIs!
        """
        
        verified_alternatives = []
        tested_combinations = set()
        
        print(f"\n🔍 Searching for REAL, VERIFIED alternatives...")
        
        # DYNAMIC: Get ACTUAL dish types that exist for this cuisine in our database!
        methods_to_try = []
        
        if self.local_db_available:
            try:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()
                
                # Find what dish types ACTUALLY exist for this cuisine
                cursor.execute('''
                    SELECT DISTINCT dish_type, COUNT(*) as recipe_count
                    FROM recipes 
                    WHERE cuisine = ? AND dish_type != ?
                    GROUP BY dish_type
                    ORDER BY recipe_count DESC
                    LIMIT 5
                ''', (cuisine.lower(), dish_type))
                
                actual_dish_types = cursor.fetchall()
                
                if actual_dish_types:
                    # Filter out generic/unhelpful dish types
                    useful_types = [row[0] for row in actual_dish_types 
                                   if row[0] not in ['side', 'miscellaneous', 'vegan', 'vegetarian', 'unknown']]
                    if useful_types:
                        methods_to_try = useful_types
                    else:
                        methods_to_try = ['soup', 'stew', 'roast', 'salad']
                    print(f"   📊 Found REAL {cuisine} dish types in database: {methods_to_try}")
                else:
                    # No recipes for this cuisine yet - try common universal types
                    methods_to_try = ['soup', 'stew', 'roast', 'salad']
                    print(f"   📊 No {cuisine} recipes in database yet, using universal dish types")
                
                conn.close()
                
            except Exception as e:
                print(f"   ⚠️ Could not query dish types: {e}")
                methods_to_try = ['soup', 'stew', 'roast', 'salad']
        else:
            # No database - use universal types
            methods_to_try = ['soup', 'stew', 'roast', 'salad']
        
        # Option 1: Try same cuisine, different methods - CHECK LOCAL DB FIRST!
        for alt_method in methods_to_try:
            combo_key = f"{cuisine}-{alt_method}"
            if combo_key not in tested_combinations:
                tested_combinations.add(combo_key)
                
                print(f"\n   🔄 Verifying: {cuisine} {alt_method}...")
                
                # Check local database first!
                if self.local_db_available:
                    local_result = self._search_local_database(cuisine, ingredients, alt_method)
                    if local_result:
                        verified_alternatives.append({
                            'cuisine': cuisine,
                            'dish_type': alt_method,
                            'ingredients': ingredients,
                            'reason': f"Popular {cuisine.title()} preparation style",
                            'confidence': 0.98,
                            'guaranteed': True,
                            'recipe_preview': local_result.get('title'),
                            'from_local_db': True
                        })
                        
                        if len(verified_alternatives) >= 3:
                            break
                        continue
                
                # If not in local DB, check APIs
                spoon_cuisine = self.country_to_spoonacular.get(cuisine.lower(), cuisine)
                result = self._search_all_apis_with_verification(
                    spoon_cuisine,
                    ingredients,
                    alt_method
                )
                
                if result:
                    verified_alternatives.append({
                        'cuisine': cuisine,
                        'dish_type': alt_method,
                        'ingredients': ingredients,
                        'reason': f"Popular {cuisine.title()} preparation style",
                        'confidence': 0.95,
                        'guaranteed': True,
                        'recipe_preview': result.get('title', f"{cuisine.title()} {alt_method}")
                    })
                    
                    if len(verified_alternatives) >= 3:
                        break
        
        # Option 2: If need more, try sister cuisines
        if len(verified_alternatives) < 3 and self.sister_countries_tried:
            for sister in self.sister_countries_tried[:2]:
                combo_key = f"{sister}-{dish_type}"
                if combo_key not in tested_combinations:
                    tested_combinations.add(combo_key)
                    
                    print(f"\n   🔄 Verifying: {sister} {dish_type}...")
                    
                    # Check local DB first
                    if self.local_db_available:
                        local_result = self._search_local_database(sister, ingredients, dish_type)
                        if local_result:
                            verified_alternatives.append({
                                'cuisine': sister,
                                'dish_type': dish_type,
                                'ingredients': ingredients,
                                'reason': f"Similar regional cuisine",
                                'confidence': 0.90,
                                'guaranteed': True,
                                'recipe_preview': local_result.get('title'),
                                'from_local_db': True
                            })
                            continue
                    
                    # Then check APIs
                    sister_spoon = self.country_to_spoonacular.get(sister, sister)
                    result = self._search_all_apis_with_verification(
                        sister_spoon,
                        ingredients,
                        dish_type
                    )
                    
                    if result:
                        verified_alternatives.append({
                            'cuisine': sister,
                            'dish_type': dish_type,
                            'ingredients': ingredients,
                            'reason': f"Similar regional cuisine",
                            'confidence': 0.85,
                            'guaranteed': True,
                            'recipe_preview': result.get('title', f"{sister.title()} {dish_type}")
                        })
        
        # If NO verified alternatives found, analyze WHY and suggest better options
        if not verified_alternatives:
            print("\n   ❌ No verified alternatives found in local DB or APIs")
            
            # Analyze ingredients to suggest better cuisine
            ingredient_cuisine_suggestions = self._analyze_ingredient_cuisine_fit(ingredients)

            # Check if the problem is cuisine-ingredient mismatch
            if ingredient_cuisine_suggestions and ingredient_cuisine_suggestions[0]['cuisine'] != cuisine:
                # Ingredients don't match the cuisine - suggest better cuisines
                for suggestion in ingredient_cuisine_suggestions[:3]:
                    # Get APPROPRIATE dish type for this cuisine from database
                    suggested_cuisine = suggestion['cuisine']
                    appropriate_dish_type = dish_type  # Default
                    
                    if self.local_db_available:
                        try:
                            conn = sqlite3.connect(self.db_path, timeout=10)
                            cursor = conn.cursor()
                            # Find most common dish type for this cuisine
                            cursor.execute('''
                                SELECT dish_type, COUNT(*) as count
                                FROM recipes 
                                WHERE cuisine = ? AND dish_type IS NOT NULL
                                GROUP BY dish_type
                                ORDER BY count DESC
                                LIMIT 1
                            ''', (suggested_cuisine.lower(),))
                            result = cursor.fetchone()
                            if result and result[0] not in ['side', 'miscellaneous', 'vegan', 'vegetarian']:
                                appropriate_dish_type = result[0]
                            conn.close()
                        except:
                            pass
                    
                    verified_alternatives.append({
                        'cuisine': suggestion['cuisine'],
                        'dish_type': appropriate_dish_type,
                        'ingredients': ingredients,
                        'reason': f"Your ingredients match {suggestion['cuisine'].title()} cuisine better ({suggestion['match_reason']})",
                        'confidence': suggestion['confidence'],
                        'is_suggestion': True
                    })
            
            # If still no alternatives, suggest ingredient changes
            if not verified_alternatives:
                compatible_ingredients = self._get_cuisine_typical_ingredients(cuisine)
                if compatible_ingredients:
                    verified_alternatives.append({
                        'cuisine': cuisine,
                        'dish_type': dish_type,
                        'ingredients': compatible_ingredients[:5],  # Suggest 5 typical ingredients
                        'reason': f"Try {cuisine.title()} cuisine with traditional ingredients",
                        'confidence': 0.8,
                        'is_suggestion': True
                    })
            
            # Final fallback
            if not verified_alternatives:
                return [{
                    'cuisine': cuisine,
                    'dish_type': 'simple',
                    'ingredients': ingredients,
                    'reason': "We'll create a custom recipe just for you",
                    'confidence': 1.0,
                    'is_essential': True
                    }]
        
        print(f"\n   ✅ Found {len(verified_alternatives)} VERIFIED alternatives!")
        return verified_alternatives
   
    def _get_region_for_country(self, country: str) -> Optional[Dict]:
       """Get region info for a country from nested structure"""
       regions = self.culinary_regions.get('regions', {})
       
       # Search through regions AND their subregions
       for region_key, region_data in regions.items():
           subregions = region_data.get('subregions', {})
           
           for subregion_key, subregion_data in subregions.items():
               if country in subregion_data.get('countries', []):
                   # Found it! Return subregion info with sister countries
                   return {
                       'key': subregion_key,
                       'name': subregion_data.get('name', subregion_key),
                       'countries': subregion_data.get('countries', []),
                       'region': region_key,
                       'region_name': region_data.get('name', region_key)
                   }
       
       return None

# Create singleton instance
recipe_matcher_4d = RecipeMatcher4D()