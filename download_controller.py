"""
RecipeGen™ Download Controller
Manages downloads from all APIs respecting rate limits
"""

import json
import time
import sqlite3
import requests
import os
from datetime import datetime, timedelta
import schedule

print("=== RecipeGen Download Controller ===\n")

# Configuration
DB_PATH = "D:/RecipeGen_Database/processed/recipegen_master.db"
RAW_BASE_PATH = "D:/RecipeGen_Database/raw_downloads/"
LOG_PATH = "D:/RecipeGen_Database/logs/"
os.makedirs(LOG_PATH, exist_ok=True)

# API Configurations with rate limits
API_CONFIGS = {
    'spoonacular': {
        'daily_limit': 150,
        'key': '900ff67536964e419f2584505480b7fa',
        'priority': 2
    },
    'edamam': {
        'daily_limit': 10000,  # Depends on your plan
        'app_id': '02b029a5',
        'app_key': 'fbbccebd37538d3bd2226a6b5fced68e',
        'priority': 1
    },
    'tasty': {
        'monthly_limit': 500,
        'daily_limit': 20,  # Self-imposed to spread over month
        'key': 'd445dcc16emsh4df4d0ee338f675p1c4c80jsne07e22c72a79',
        'priority': 3
    },
    'mycookbook': {
        'daily_limit': 100,  # Estimate
        'key': 'd445dcc16emsh4df4d0ee338f675p1c4c80jsne07e22c72a79',
        'priority': 4
    }
}

class DownloadController:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.load_progress()
    
    def load_progress(self):
        """Load download progress from database"""
        self.cursor.execute('''
            SELECT source, 
                   COUNT(DISTINCT source_id) as downloaded,
                   MAX(download_date) as last_download
            FROM recipes 
            GROUP BY source
        ''')
        
        self.progress = {}
        for row in self.cursor.fetchall():
            self.progress[row[0]] = {
                'downloaded': row[1],
                'last_download': row[2]
            }
        
        print("Current progress:")
        for source, data in self.progress.items():
            print(f"  {source}: {data['downloaded']} recipes")
    
    def can_download_today(self, api_name):
        """Check if we can download from this API today"""
        # Check today's downloads
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''
            SELECT COUNT(*) FROM download_log 
            WHERE source = ? AND DATE(download_date) = ?
        ''', (api_name, today))
        
        today_count = self.cursor.fetchone()[0]
        daily_limit = API_CONFIGS[api_name]['daily_limit']
        
        return today_count < daily_limit
    
    def download_spoonacular_batch(self, limit=150):
        """Download batch from Spoonacular"""
        if not self.can_download_today('spoonacular'):
            print("Spoonacular daily limit reached")
            return 0
        
        print("\n=== Downloading from Spoonacular ===")
        api_key = API_CONFIGS['spoonacular']['key']
        
        # Get cuisines to download
        cuisines = ['italian', 'chinese', 'mexican', 'indian', 'french', 
                   'japanese', 'thai', 'spanish', 'greek', 'korean']
        
        downloaded = 0
        for cuisine in cuisines:
            if downloaded >= limit:
                break
                
            offset = self.progress.get('spoonacular', {}).get('downloaded', 0)
            
            url = "https://api.spoonacular.com/recipes/complexSearch"
            params = {
                'apiKey': api_key,
                'cuisine': cuisine,
                'addRecipeInformation': True,
                'fillIngredients': True,
                'number': min(100, limit - downloaded),
                'offset': offset
            }
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    for recipe in data.get('results', []):
                        self.save_spoonacular_recipe(recipe)
                        downloaded += 1
                        
                    print(f"  Downloaded {len(data.get('results', []))} {cuisine} recipes")
                
                time.sleep(1)  # Rate limit respect
                
            except Exception as e:
                print(f"  Error: {e}")
        
        # Log the download
        self.cursor.execute('''
            INSERT INTO download_log (source, recipes_downloaded, status)
            VALUES ('spoonacular', ?, 'completed')
        ''', (downloaded,))
        self.conn.commit()
        
        return downloaded
    
    def save_spoonacular_recipe(self, recipe_data):
        """Save Spoonacular recipe to database"""
        # Normalize to RecipeGen format
        ingredients = []
        for ext_ing in recipe_data.get('extendedIngredients', []):
            ingredients.append({
                'name': ext_ing.get('name', ''),
                'amount': f"{ext_ing.get('amount', '')} {ext_ing.get('unit', '')}",
                'slug': ext_ing.get('name', '').lower().replace(' ', '_')
            })
        
        # Parse instructions
        instructions = []
        for instruction_group in recipe_data.get('analyzedInstructions', []):
            for step in instruction_group.get('steps', []):
                instructions.append({
                    'step': step['number'],
                    'instruction': step['step']
                })
        
        recipe = {
            'id': f"spoon_{recipe_data['id']}",
            'title': recipe_data['title'],
            'cuisine': recipe_data.get('cuisines', [''])[0].lower() if recipe_data.get('cuisines') else 'international',
            'dish_type': recipe_data.get('dishTypes', [''])[0] if recipe_data.get('dishTypes') else '',
            'ingredients': ingredients,
            'instructions': instructions,
            'prep_time': recipe_data.get('preparationMinutes'),
            'cook_time': recipe_data.get('cookingMinutes'),
            'total_time': recipe_data.get('readyInMinutes'),
            'servings': recipe_data.get('servings'),
            'source': 'spoonacular',
            'source_id': str(recipe_data['id']),
            'source_url': recipe_data.get('sourceUrl'),
            'image_url': recipe_data.get('image'),
            'nutrition': recipe_data.get('nutrition'),
            'quality_score': min(90, 50 + recipe_data.get('spoonacularScore', 0) // 2)
        }
        
        # Save to database
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO recipes 
                (id, title, cuisine, dish_type, ingredients, instructions,
                 prep_time, cook_time, total_time, servings,
                 source, source_id, source_url, image_url, nutrition, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe['id'], recipe['title'], recipe['cuisine'], recipe['dish_type'],
                json.dumps(recipe['ingredients']), json.dumps(recipe['instructions']),
                recipe['prep_time'], recipe['cook_time'], recipe['total_time'],
                recipe['servings'], recipe['source'], recipe['source_id'],
                recipe['source_url'], recipe['image_url'], 
                json.dumps(recipe['nutrition']) if recipe['nutrition'] else None,
                recipe['quality_score']
            ))
            
            # Update ingredients table
            self.cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe['id'],))
            for ing in recipe['ingredients']:
                self.cursor.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_slug, ingredient_name, amount)
                    VALUES (?, ?, ?, ?)
                ''', (recipe['id'], ing['slug'], ing['name'], ing['amount']))
                
        except Exception as e:
            print(f"    Error saving {recipe['title']}: {e}")
    
    def download_edamam_batch(self, limit=1000):
        """Download batch from Edamam"""
        if not self.can_download_today('edamam'):
            print("Edamam daily limit reached")
            return 0
        
        print("\n=== Downloading from Edamam ===")
        app_id = API_CONFIGS['edamam']['app_id']
        app_key = API_CONFIGS['edamam']['app_key']
        
        cuisines = ['american', 'asian', 'british', 'caribbean', 'central europe',
                   'chinese', 'eastern europe', 'french', 'indian', 'italian',
                   'japanese', 'mediterranean', 'mexican', 'middle eastern',
                   'nordic', 'south american', 'south east asian']
        
        downloaded = 0
        for cuisine in cuisines:
            if downloaded >= limit:
                break
            
            url = "https://api.edamam.com/api/recipes/v2"
            params = {
                'type': 'public',
                'app_id': app_id,
                'app_key': app_key,
                'cuisineType': cuisine,
                'random': 'true'
            }
            
            # Edamam uses pagination with _cont parameter
            next_page = None
            batch_size = 20
            
            while downloaded < limit:
                if next_page:
                    params['_cont'] = next_page
                
                try:
                    response = requests.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        
                        for hit in data.get('hits', []):
                            self.save_edamam_recipe(hit['recipe'])
                            downloaded += 1
                        
                        print(f"  Downloaded {len(data.get('hits', []))} {cuisine} recipes")
                        
                        # Get next page token
                        next_page = data.get('_links', {}).get('next', {}).get('href')
                        if not next_page or downloaded >= limit:
                            break
                    
                    time.sleep(0.6)  # Rate limit
                    
                except Exception as e:
                    print(f"  Error: {e}")
                    break
        
        # Log the download
        self.cursor.execute('''
            INSERT INTO download_log (source, recipes_downloaded, status)
            VALUES ('edamam', ?, 'completed')
        ''', (downloaded,))
        self.conn.commit()
        
        return downloaded
    
    def save_edamam_recipe(self, recipe_data):
        """Save Edamam recipe to database"""
        # Extract recipe ID from URI
        recipe_id = recipe_data['uri'].split('#recipe_')[1]
        
        # Normalize ingredients
        ingredients = []
        for ing in recipe_data.get('ingredients', []):
            ingredients.append({
                'name': ing.get('food', ''),
                'amount': ing.get('text', ''),
                'slug': ing.get('food', '').lower().replace(' ', '_')
            })
        
        # Edamam doesn't have step-by-step instructions, just ingredient lines
        instructions = [{
            'step': 1,
            'instruction': 'Prepare and combine ingredients as listed. Follow standard cooking methods for this dish type.'
        }]
        
        # Map cuisine
        cuisine_map = {
            'central europe': 'hungarian',
            'eastern europe': 'russian',
            'south american': 'brazilian',
            'south east asian': 'thai',
            'middle eastern': 'turkish'
        }
        cuisine = recipe_data.get('cuisineType', [''])[0].lower()
        cuisine = cuisine_map.get(cuisine, cuisine)
        
        recipe = {
            'id': f"edamam_{recipe_id}",
            'title': recipe_data['label'],
            'cuisine': cuisine,
            'dish_type': recipe_data.get('dishType', [''])[0] if recipe_data.get('dishType') else '',
            'ingredients': ingredients,
            'instructions': instructions,
            'total_time': recipe_data.get('totalTime', 0),
            'servings': int(recipe_data.get('yield', 4)),
            'source': 'edamam',
            'source_id': recipe_id,
            'source_url': recipe_data.get('url'),
            'image_url': recipe_data.get('image'),
            'nutrition': recipe_data.get('totalNutrients'),
            'quality_score': 70 if recipe_data.get('url') else 60
        }
        
        # Save to database (similar to spoonacular)
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO recipes 
                (id, title, cuisine, dish_type, ingredients, instructions,
                 total_time, servings, source, source_id, source_url, 
                 image_url, nutrition, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe['id'], recipe['title'], recipe['cuisine'], recipe['dish_type'],
                json.dumps(recipe['ingredients']), json.dumps(recipe['instructions']),
                recipe['total_time'], recipe['servings'], recipe['source'],
                recipe['source_id'], recipe['source_url'], recipe['image_url'],
                json.dumps(recipe['nutrition']) if recipe['nutrition'] else None,
                recipe['quality_score']
            ))
            
            # Update ingredients table
            self.cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe['id'],))
            for ing in recipe['ingredients']:
                self.cursor.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_slug, ingredient_name, amount)
                    VALUES (?, ?, ?, ?)
                ''', (recipe['id'], ing['slug'], ing['name'], ing['amount']))
                
        except Exception as e:
            print(f"    Error saving {recipe['title']}: {e}")
    
    def run_daily_downloads(self):
        """Run daily download tasks"""
        print(f"\n{'='*50}")
        print(f"Starting daily downloads - {datetime.now()}")
        print(f"{'='*50}")
        
        # Priority order
        total_downloaded = 0
        
        # 1. Edamam (highest limit)
        if self.can_download_today('edamam'):
            count = self.download_edamam_batch(1000)
            total_downloaded += count
            print(f"Edamam: {count} recipes")
        
        # 2. Spoonacular (limited)
        if self.can_download_today('spoonacular'):
            count = self.download_spoonacular_batch(150)
            total_downloaded += count
            print(f"Spoonacular: {count} recipes")
        
        # TODO: Add Tasty and MyCookbook downloaders
        
        # Update statistics
        self.cursor.execute('''
            UPDATE statistics 
            SET recipe_count = (
                SELECT COUNT(*) FROM recipes WHERE cuisine = statistics.cuisine
            ),
            last_updated = CURRENT_TIMESTAMP
        ''')
        self.conn.commit()
        
        print(f"\nTotal downloaded today: {total_downloaded}")
        
        # Show current totals
        self.cursor.execute("SELECT COUNT(*) FROM recipes")
        total = self.cursor.fetchone()[0]
        print(f"Total recipes in database: {total}")
        
        # Show by source
        self.cursor.execute('''
            SELECT source, COUNT(*) FROM recipes GROUP BY source
        ''')
        print("\nBy source:")
        for source, count in self.cursor.fetchall():
            print(f"  {source}: {count}")
    
    def schedule_downloads(self):
        """Schedule daily downloads"""
        # Run at 2 AM every day
        schedule.every().day.at("02:00").do(self.run_daily_downloads)
        
        print("Download scheduler started. Will run daily at 2 AM.")
        print("Press Ctrl+C to stop.")
        
        # Run once immediately
        self.run_daily_downloads()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    controller = DownloadController()
    
    print("\nOptions:")
    print("1. Run daily downloads now")
    print("2. Start scheduled downloads (runs daily at 2 AM)")
    print("3. Show current statistics")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        controller.run_daily_downloads()
    elif choice == "2":
        controller.schedule_downloads()
    elif choice == "3":
        controller.cursor.execute('''
            SELECT cuisine, recipe_count 
            FROM statistics 
            WHERE recipe_count > 0 
            ORDER BY recipe_count DESC
        ''')
        print("\nRecipes by cuisine:")
        for cuisine, count in controller.cursor.fetchall():
            print(f"  {cuisine}: {count}")
            