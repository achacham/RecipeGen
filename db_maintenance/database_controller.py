import sqlite3
import json
import time
import os
import requests
from typing import Dict, Optional

class DatabaseController:
    def __init__(self, db_path: str = "D:/RecipeGen_Database/processed/recipegen_master.db"):
        """Initialize the database controller"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Track import statistics
        self.stats = {
            'imported': 0,
            'skipped': 0,
            'failed': 0,
            'duplicates': 0
        }
        
        # Load API keys from environment or .env file
        self.load_api_keys()
        
    def load_api_keys(self):
        """Load API keys from .env file"""
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_keys = {
            'spoonacular': os.getenv('SPOONACULAR_API_KEY'),
            'tasty': os.getenv('RAPIDAPI_KEY'),
            'edamam_id': os.getenv('EDAMAM_APP_ID'),
            'edamam_key': os.getenv('EDAMAM_APP_KEY')
        }
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path, timeout=30)
        self.cursor = self.conn.cursor()
        
        # Check if cuisine column allows NULL
        self.cursor.execute("PRAGMA table_info(recipes)")
        columns = self.cursor.fetchall()
        cuisine_col = next((col for col in columns if col[1] == 'cuisine'), None)
        
        if cuisine_col and cuisine_col[3] == 1:  # NOT NULL constraint exists
            print("⚠️  Fixing database schema to allow NULL cuisines...")
            
            # Get the actual CREATE statement from existing table
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='recipes'")
            create_statement = self.cursor.fetchone()[0]
            
            # Replace NOT NULL for cuisine column
            create_statement = create_statement.replace('cuisine TEXT NOT NULL', 'cuisine TEXT')
            create_statement = create_statement.replace('CREATE TABLE recipes', 'CREATE TABLE recipes_temp')
            
            # Create temp table with modified schema
            self.cursor.execute("DROP TABLE IF EXISTS recipes_temp")
            self.cursor.execute(create_statement)
            
            # Copy data
            self.cursor.execute("INSERT INTO recipes_temp SELECT * FROM recipes")
            self.cursor.execute("DROP TABLE recipes")
            self.cursor.execute("ALTER TABLE recipes_temp RENAME TO recipes")
            self.conn.commit()
            print("✅ Database schema updated")
            
        print(f"✅ Connected to database: {self.db_path}")
        
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            print("\n📊 Import Statistics:")
            print(f"   ✅ Imported: {self.stats['imported']}")
            print(f"   ⏭️ Skipped: {self.stats['skipped']}")
            print(f"   ❌ Failed: {self.stats['failed']}")
            print(f"   🔁 Duplicates: {self.stats['duplicates']}")

    def import_from_local_themealdb_files(self):
        """Import from already downloaded TheMealDB files"""
        print("\n🍽️ Importing from LOCAL TheMealDB files...")
        
        import glob
        local_path = "D:/RecipeGen_Database/raw_downloads/themealdb/*.json"
        themealdb_files = glob.glob(local_path)
        
        if not themealdb_files:
            print(f"   ⚠️ No files found in {local_path}")
            return
            
        print(f"   📁 Found {len(themealdb_files)} local files")
        
        from themealdb_fetcher import TheMealDBFetcher
        fetcher = TheMealDBFetcher()
        
        for file_path in themealdb_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    meal_data = json.load(f)
                    recipe = fetcher.convert_to_recipegen_format(meal_data)
                    if recipe:
                        self.save_recipe(recipe, 'themealdb')
            except Exception as e:
                print(f"   ⚠️ Error processing {file_path}: {e}")
                self.stats['failed'] += 1
        
        print(f"   ✅ Processed {len(themealdb_files)} local files")

    def import_from_themealdb(self, limit=None):
        """Import recipes from TheMealDB API"""
        print("\n🍽️ Starting TheMealDB API import...")
        from themealdb_fetcher import TheMealDBFetcher
        
        fetcher = TheMealDBFetcher()
        imported_count = 0
        
        try:
            # Get categories from API
            response = requests.get('https://www.themealdb.com/api/json/v1/1/list.php?c=list')
            categories = response.json()['meals']
            
            for cat_item in categories:
                if limit and imported_count >= limit:
                    break
                    
                category = cat_item['strCategory']
                print(f"   📝 Fetching {category} recipes...")
                
                cat_response = requests.get(f'https://www.themealdb.com/api/json/v1/1/filter.php?c={category}')
                meals = cat_response.json().get('meals', [])
                
                for meal_summary in meals:
                    if limit and imported_count >= limit:
                        break
                        
                    meal_id = meal_summary['idMeal']
                    full_response = requests.get(f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}')
                    full_meal = full_response.json()['meals'][0]
                    
                    recipe = fetcher.convert_to_recipegen_format(full_meal)
                    if recipe:
                        if self.save_recipe(recipe, 'themealdb'):
                            imported_count += 1
                        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    def import_from_spoonacular(self, limit=20):
        """Import recipes from Spoonacular"""
        print("\n🥄 Starting Spoonacular import...")
        
        if not self.api_keys['spoonacular']:
            print("   ⚠️ Spoonacular API key not found in .env file")
            return
            
        from spoonacular_fetcher import SpoonacularFetcher
        fetcher = SpoonacularFetcher(self.api_keys['spoonacular'])
        imported_count = 0
        
        try:
            # Query the API for random recipes
            params = {
                'apiKey': self.api_keys['spoonacular'],
                'number': limit,
                'random': True
            }
            
            response = requests.get('https://api.spoonacular.com/recipes/complexSearch', params=params)
            
            if response.status_code == 200:
                data = response.json()
                recipes = data.get('results', [])
                
                for recipe_summary in recipes:
                    # Get full recipe details
                    recipe_id = recipe_summary['id']
                    detail_params = {'apiKey': self.api_keys['spoonacular']}
                    detail_response = requests.get(
                        f'https://api.spoonacular.com/recipes/{recipe_id}/information',
                        params=detail_params
                    )
                    
                    if detail_response.status_code == 200:
                        full_recipe = detail_response.json()
                        recipe = fetcher.convert_to_recipegen_format(full_recipe)
                        if recipe:
                            if self.save_recipe(recipe, 'spoonacular'):
                                imported_count += 1
                                
                print(f"   ✅ Imported {imported_count} Spoonacular recipes")
            else:
                print(f"   ❌ Error: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

    def convert_tasty_to_recipegen(self, tasty_recipe):
        """Convert Tasty recipe format to RecipeGen format"""
        try:
            # Extract basic info
            title = tasty_recipe.get('name', '').strip()
            if not title:
                return None
            
            # Get cuisine from tags or set default
            tags = tasty_recipe.get('tags', [])
            cuisine = 'international'  # default
            for tag in tags:
                tag_name = tag.get('display_name', '').lower()
                if tag.get('type') == 'cuisine':
                    cuisine = tag_name
                    break
            
            # Determine dish type from tags
            dish_type = 'main'  # default
            for tag in tags:
                tag_name = tag.get('display_name', '').lower()
                if tag.get('type') == 'meal':
                    if 'breakfast' in tag_name:
                        dish_type = 'breakfast'
                    elif 'dessert' in tag_name:
                        dish_type = 'dessert'
                    elif 'appetizer' in tag_name or 'snack' in tag_name:
                        dish_type = 'appetizer'
                    elif 'side' in tag_name:
                        dish_type = 'side-dish'
                    break
            
            # Extract ingredients from sections
            ingredients = []
            sections = tasty_recipe.get('sections', [])
            for section in sections:
                for component in section.get('components', []):
                    raw_text = component.get('raw_text', '')
                    ingredient = component.get('ingredient', {}).get('name', '')
                    
                    if raw_text:
                        # Parse the raw text for amount and item
                        parts = raw_text.split(',', 1)
                        amount_part = parts[0].strip()
                        
                        # Try to extract the ingredient name
                        if ingredient:
                            item_name = ingredient
                        else:
                            # Fallback: extract from raw_text
                            item_name = amount_part
                        
                        ingredients.append({
                            'item': item_name,
                            'amount': amount_part,
                            'slug': item_name.lower().replace(' ', '_')
                        })
            
            # Extract instructions
            instructions = []
            instruction_list = tasty_recipe.get('instructions', [])
            for idx, inst in enumerate(instruction_list, 1):
                display_text = inst.get('display_text', '')
                if display_text:
                    instructions.append({
                        'step': idx,
                        'instruction': display_text
                    })
            
            # Skip recipes without instructions
            if not instructions:
                return None
            
            # Get timing info
            prep_time = tasty_recipe.get('prep_time_minutes', 0)
            cook_time = tasty_recipe.get('cook_time_minutes', 0)
            total_time = tasty_recipe.get('total_time_minutes', 0)
            
            # If total_time is 0, calculate it
            if total_time == 0:
                total_time = prep_time + cook_time
            
            # Get other metadata
            servings = tasty_recipe.get('num_servings', 4)
            
            # Get image URL
            image_url = (tasty_recipe.get('thumbnail_url') or 
                        tasty_recipe.get('beauty_url') or 
                        tasty_recipe.get('video_url'))
            
            # Calculate quality score based on available data
            quality_score = 60  # Base score
            if instructions and len(instructions) >= 3:
                quality_score += 10
            if ingredients and len(ingredients) >= 3:
                quality_score += 10
            if image_url:
                quality_score += 10
            if tasty_recipe.get('user_ratings'):
                rating = tasty_recipe['user_ratings'].get('score', 0)
                if rating > 0:
                    quality_score += int(rating * 10)  # Add up to 10 points for rating
            
            # Build RecipeGen format
            return {
                'title': title,
                'cuisine': cuisine,
                'dish_type': dish_type,
                'ingredients': ingredients,
                'instructions': instructions,
                'prep_time': prep_time,
                'cook_time': cook_time,
                'total_time': total_time,
                'servings': servings,
                'source': 'tasty',
                'source_id': str(tasty_recipe.get('id', '')),
                'source_url': tasty_recipe.get('original_video_url', ''),
                'image_url': image_url,
                'quality_score': min(quality_score, 100),  # Cap at 100
                'is_verified': True  # Tasty recipes are generally well-tested
            }
            
        except Exception as e:
            print(f"      ⚠️ Conversion error for '{tasty_recipe.get('name', 'Unknown')}': {str(e)[:100]}")
            return None
            
    def import_from_tasty(self, limit=100):
        """Import recipes from Tasty via RapidAPI"""
        print("\n🍳 Starting Tasty import...")
        
        if not self.api_keys.get('tasty'):
            print("   ⚠️ Tasty RapidAPI key not found")
            return
        
        print(f"   🔑 Using API key: {self.api_keys['tasty'][:8]}...")
        
        imported_count = 0
        skipped_count = 0
        
        try:
            url = "https://tasty.p.rapidapi.com/recipes/list"
            headers = {
                "X-RapidAPI-Key": self.api_keys['tasty'],
                "X-RapidAPI-Host": "tasty.p.rapidapi.com"
            }
            
            # NEW: Loop through multiple pages to get more recipes!
            batch_size = 40  # Tasty seems to return max 40 per request
            for offset in range(0, limit, batch_size):
                remaining = limit - imported_count
                if remaining <= 0:
                    break
                    
                params = {
                    "from": offset,
                    "size": min(batch_size, remaining)
                }
                
                print(f"\n   📡 Requesting batch starting at {offset} (up to {params['size']} recipes)...")
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                print(f"   📊 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    total_available = data.get('count', 0)
                    recipes = data.get('results', [])
                    
                    # Only show this info on first batch
                    if offset == 0:
                        print(f"   📚 Tasty has {total_available:,} total recipes available")
                    
                    print(f"   📦 Received {len(recipes)} recipes in this batch")
                    
                    if not recipes:
                        print("   ⚠️ No more recipes available")
                        break  # No more recipes to fetch
                    
                    # Process each recipe in this batch
                    batch_imported = 0
                    for idx, tasty_recipe in enumerate(recipes, 1):
                        try:
                            # Debug first recipe structure (only on first batch)
                            if offset == 0 and idx == 1:
                                print(f"   🔍 First recipe keys: {list(tasty_recipe.keys())[:10]}...")
                            
                            if not tasty_recipe.get('name'):
                                skipped_count += 1
                                continue
                            
                            recipe = self.convert_tasty_to_recipegen(tasty_recipe)
                            
                            if recipe:
                                if self.save_recipe(recipe, 'tasty'):
                                    imported_count += 1
                                    batch_imported += 1
                                    if imported_count % 10 == 0:
                                        print(f"      ✅ Imported {imported_count} recipes total...")
                            else:
                                skipped_count += 1
                                
                        except Exception as e:
                            print(f"   ⚠️ Error processing recipe {idx}: {str(e)[:100]}")
                            skipped_count += 1
                            continue
                    
                    print(f"   📦 Batch complete: imported {batch_imported} from this batch")
                    
                    # Add a small delay between batches to be respectful to the API
                    if offset + batch_size < limit and len(recipes) == batch_size:
                        print("   ⏳ Waiting 2 seconds before next batch...")
                        time.sleep(2)
                        
                elif response.status_code == 403:
                    print(f"   ❌ Authentication failed - check your API key")
                    break  # Stop trying if auth fails
                elif response.status_code == 429:
                    print(f"   ⚠️ Rate limit exceeded - stopping Tasty import")
                    break  # Stop if rate limited
                else:
                    print(f"   ❌ Error: Status {response.status_code}")
                    break  # Stop on other errors
            
            # Final summary
            print(f"\n   ✅ Imported {imported_count} Tasty recipes total")
            if skipped_count > 0:
                print(f"   ⏭️ Skipped {skipped_count} recipes (conversion failed or missing data)")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timed out after 30 seconds")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error - check your internet connection")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            import traceback
            print(f"   Full error: {traceback.format_exc()[:500]}")
                
            
    def import_from_edamam(self, limit=500):
        """Import recipes from Edamam with PAGINATION"""
        print("\n🥗 Starting Edamam import...")
        
        if not self.api_keys['edamam_id'] or not self.api_keys['edamam_key']:
            print("   ⚠️ Edamam API credentials not found")
            return
        
        imported_count = 0
        base_url = "https://api.edamam.com/api/recipes/v2"
        
        try:
            # Get search terms as before
            queries = [
                "SELECT DISTINCT cuisine FROM recipes WHERE cuisine IS NOT NULL",
                "SELECT DISTINCT ingredient_slug FROM recipe_ingredients ORDER BY RANDOM() LIMIT 30",
                "SELECT DISTINCT dish_type FROM recipes WHERE dish_type IS NOT NULL"
            ]
            
            all_search_terms = []
            for query in queries:
                self.cursor.execute(query)
                all_search_terms.extend([row[0] for row in self.cursor.fetchall()])
            
            search_terms = list(dict.fromkeys(all_search_terms))
            
            if not search_terms:
                print("   ⚠️ No search terms found")
                return
            
            print(f"   📝 Using {len(search_terms)} search terms")
            
            for term in search_terms:
                if imported_count >= limit:
                    break
                
                # NEW: Get up to 100 per search term with pagination!
                recipes_per_term = min(100, limit - imported_count)
                
                for start_from in range(0, recipes_per_term, 20):  # Paginate in batches of 20
                    if imported_count >= limit:
                        break
                    
                    params = {
                        'type': 'public',
                        'app_id': self.api_keys['edamam_id'],
                        'app_key': self.api_keys['edamam_key'],
                        'q': term,
                        'from': start_from,  # NEW: Pagination!
                        'to': min(start_from + 20, recipes_per_term)
                    }
                    
                    response = requests.get(base_url, params=params)
                    time.sleep(6)  # Rate limit: 10/minute
                    
                    if response.status_code == 200:
                        data = response.json()
                        hits = data.get('hits', [])
                        
                        if not hits:
                            break  # No more results for this term
                        
                        for hit in hits:
                            if imported_count >= limit:
                                break
                            recipe = self.convert_edamam_to_recipegen(hit['recipe'])
                            if recipe:
                                if self.save_recipe(recipe, 'edamam'):
                                    imported_count += 1
                                    if imported_count % 50 == 0:
                                        print(f"      ✅ Imported {imported_count} recipes...")
                    
                    else:
                        print(f"   ⚠️ Error for '{term}': Status {response.status_code}")
                        break  # Skip this search term
            
            print(f"   ✅ Imported {imported_count} Edamam recipes")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    def convert_edamam_to_recipegen(self, edamam_recipe):
        """Convert Edamam format to RecipeGen format"""
        try:
            ingredients = []
            for ing in edamam_recipe.get('ingredientLines', []):
                ingredients.append({
                    'name': ing,
                    'amount': ''
                })
            
            # Get cuisine if provided
            cuisine_type = edamam_recipe.get('cuisineType', [])
            cuisine = cuisine_type[0].lower() if cuisine_type else None
            
            return {
                'id': edamam_recipe.get('uri', '').split('#')[-1],
                'title': edamam_recipe.get('label'),
                'cuisine': cuisine,  # Can be NULL
                'dish_type': None,
                'ingredients': ingredients,
                'instructions': [],  # Edamam doesn't provide instructions
                'prep_time': None,
                'cook_time': edamam_recipe.get('totalTime'),
                'total_time': edamam_recipe.get('totalTime'),
                'servings': edamam_recipe.get('yield'),
                'image_url': edamam_recipe.get('image'),
                'source_url': edamam_recipe.get('url')
            }
        except Exception as e:
            return None
            
    def save_recipe(self, recipe: Dict, source: str) -> bool:
        """Save recipe exactly as provided"""
        try:
            recipe_id = f"{source}_{recipe.get('id', '')}"
            if not recipe.get('id'):
                title_slug = recipe['title'].replace(' ', '_').lower()[:50]
                recipe_id = f"{source}_{title_slug}_{int(time.time())}"
                
            self.cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
            if self.cursor.fetchone():
                self.stats['duplicates'] += 1
                return False
                
            # Skip if no title
            if not recipe.get('title'):
                self.stats['skipped'] += 1
                return False
                
            # Get all column names from the table
            self.cursor.execute("PRAGMA table_info(recipes)")
            columns_info = self.cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            # Build values based on what columns exist
            values = []
            for col in column_names:
                if col == 'id':
                    values.append(recipe_id)
                elif col == 'title':
                    values.append(recipe.get('title'))
                elif col == 'cuisine':
                    values.append(recipe.get('cuisine'))
                elif col == 'dish_type':
                    values.append(recipe.get('dish_type'))
                elif col == 'ingredients':
                    values.append(json.dumps(recipe.get('ingredients', [])))
                elif col == 'instructions':
                    values.append(json.dumps(recipe.get('instructions', [])))
                elif col == 'prep_time':
                    values.append(recipe.get('prep_time'))
                elif col == 'cook_time':
                    values.append(recipe.get('cook_time'))
                elif col == 'total_time':
                    values.append(recipe.get('total_time'))
                elif col == 'servings':
                    values.append(recipe.get('servings'))
                elif col == 'source':
                    values.append(source)
                elif col == 'source_id':
                    values.append(recipe.get('id'))
                elif col == 'source_url':
                    values.append(recipe.get('source_url'))
                elif col == 'image_url':
                    values.append(recipe.get('image_url'))
                elif col == 'quality_score':
                    values.append(recipe.get('quality_score', 70))
                elif col == 'is_verified':
                    values.append(True)
                elif col == 'created_at':
                    values.append(None)  # Let database use default
                elif col == 'times_served':
                    values.append(0)
                else:
                    values.append(None)  # Unknown column
            
            # Build INSERT query dynamically
            placeholders = ','.join(['?' for _ in column_names])
            columns_str = ','.join(column_names)
            query = f"INSERT INTO recipes ({columns_str}) VALUES ({placeholders})"
            
            self.cursor.execute(query, values)
            
            # Save ingredients for search
            for ing in recipe.get('ingredients', []):
                ingredient_name = ing.get('item') or ing.get('name', '')
                ingredient_slug = ing.get('slug', '')
                
                if not ingredient_slug and ingredient_name:
                    ingredient_slug = ingredient_name.lower().replace(' ', '_')
                    
                if ingredient_slug:
                    try:
                        self.cursor.execute('''
                            INSERT INTO recipe_ingredients (recipe_id, ingredient_slug, ingredient_name, amount)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            recipe_id,
                            ingredient_slug,
                            ingredient_name,
                            ing.get('amount', '')
                        ))
                    except:
                        pass  # recipe_ingredients table might not exist
            
            self.conn.commit()
            self.stats['imported'] += 1
            
            if self.stats['imported'] % 50 == 0:
                print(f"      ✅ Imported {self.stats['imported']} recipes...")
                
            return True
            
        except Exception as e:
            print(f"   ⚠️ Error saving: {e}")
            self.stats['failed'] += 1
            return False
            
    def import_all(self):
        """Import from all available sources"""
        print("\n🚀 Starting complete database import...")
        print("=" * 60)
        
        # Use LOCAL files first
        self.import_from_local_themealdb_files()
        
        # Then API imports with limits to respect rate limits
        self.import_from_spoonacular(limit=100)  # This is working best
        self.import_from_tasty(limit=200)        # Keep trying
        self.import_from_edamam(limit=500)       # Reduce, not productive anyway
        
        print("\n" + "=" * 60)
        print("✅ Complete import finished!")

if __name__ == "__main__":
    controller = DatabaseController()
    controller.connect()
    controller.import_all()
    controller.disconnect()
