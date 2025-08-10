"""
RecipeGen™ TheMealDB Downloader
Downloads ALL recipes from TheMealDB (it's free and has no rate limits!)
"""

import requests
import json
import sqlite3
import time
from datetime import datetime
import os

print("=== TheMealDB Complete Download ===\n")

# Setup paths
DB_PATH = "D:/RecipeGen_Database/processed/recipegen_master.db"
RAW_PATH = "D:/RecipeGen_Database/raw_downloads/themealdb/"
os.makedirs(RAW_PATH, exist_ok=True)

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def normalize_to_recipegen(meal_data):
    """Convert TheMealDB format to RecipeGen format"""
    
    # Extract ingredients (TheMealDB has them in separate fields)
    ingredients = []
    for i in range(1, 21):
        ingredient = meal_data.get(f'strIngredient{i}', '').strip()
        measure = meal_data.get(f'strMeasure{i}', '').strip()
        if ingredient:
            ingredients.append({
                'name': ingredient,
                'amount': measure,
                'slug': ingredient.lower().replace(' ', '_')
            })
    
    # Parse instructions into steps
    instructions_text = meal_data.get('strInstructions', '')
    steps = []
    
    # Try to split by common patterns
    if '\r\n' in instructions_text:
        parts = instructions_text.split('\r\n')
    elif '. ' in instructions_text:
        parts = instructions_text.split('. ')
    else:
        parts = [instructions_text]
    
    for i, part in enumerate(parts):
        if part.strip():
            steps.append({
                'step': i + 1,
                'instruction': part.strip()
            })
    
    # Map cuisine
    area = meal_data.get('strArea', '').lower()
    cuisine_map = {
        'american': 'american',
        'british': 'british', 
        'canadian': 'american',
        'chinese': 'chinese',
        'croatian': 'croatian',
        'dutch': 'dutch',
        'egyptian': 'egyptian',
        'french': 'french',
        'greek': 'greek',
        'indian': 'indian',
        'irish': 'irish',
        'italian': 'italian',
        'jamaican': 'jamaican',
        'japanese': 'japanese',
        'kenyan': 'kenyan',
        'malaysian': 'malaysian',
        'mexican': 'mexican',
        'moroccan': 'moroccan',
        'polish': 'polish',
        'portuguese': 'portuguese',
        'russian': 'russian',
        'spanish': 'spanish',
        'thai': 'thai',
        'tunisian': 'tunisian',
        'turkish': 'turkish',
        'unknown': 'international',
        'vietnamese': 'vietnamese'
    }
    
    cuisine = cuisine_map.get(area, area)
    
    # Build normalized recipe
    return {
        'id': f"mealdb_{meal_data['idMeal']}",
        'title': meal_data['strMeal'],
        'cuisine': cuisine,
        'dish_type': meal_data.get('strCategory', '').lower(),
        'ingredients': ingredients,
        'instructions': steps,
        'source': 'themealdb',
        'source_id': meal_data['idMeal'],
        'source_url': meal_data.get('strSource'),
        'image_url': meal_data.get('strMealThumb'),
        'video_url': meal_data.get('strYoutube'),
        'tags': [meal_data.get('strCategory'), area],
        'quality_score': 70 if meal_data.get('strYoutube') else 60
    }

def download_all_meals():
    """Download all meals from TheMealDB"""
    base_url = "https://www.themealdb.com/api/json/v1/1"
    
    # First, get all meal IDs by area
    areas_url = f"{base_url}/list.php?a=list"
    response = requests.get(areas_url)
    areas = response.json()['meals']
    
    total_downloaded = 0
    
    for area_obj in areas:
        area = area_obj['strArea']
        print(f"\nDownloading {area} recipes...")
        
        # Get all meals for this area
        meals_url = f"{base_url}/filter.php?a={area}"
        response = requests.get(meals_url)
        meals = response.json()['meals']
        
        print(f"  Found {len(meals)} {area} recipes")
        
        for meal_summary in meals:
            meal_id = meal_summary['idMeal']
            
            # Get full recipe details
            detail_url = f"{base_url}/lookup.php?i={meal_id}"
            response = requests.get(detail_url)
            meal_data = response.json()['meals'][0]
            
            # Save raw data
            raw_file = os.path.join(RAW_PATH, f"{meal_id}.json")
            with open(raw_file, 'w') as f:
                json.dump(meal_data, f, indent=2)
            
            # Normalize and save to database
            try:
                recipe = normalize_to_recipegen(meal_data)
                
                # Insert into main recipes table
                cursor.execute('''
                    INSERT OR REPLACE INTO recipes 
                    (id, title, cuisine, dish_type, ingredients, instructions,
                     source, source_id, source_url, image_url, video_url, tags, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    recipe['id'],
                    recipe['title'],
                    recipe['cuisine'],
                    recipe['dish_type'],
                    json.dumps(recipe['ingredients']),
                    json.dumps(recipe['instructions']),
                    recipe['source'],
                    recipe['source_id'],
                    recipe['source_url'],
                    recipe['image_url'],
                    recipe['video_url'],
                    json.dumps(recipe['tags']),
                    recipe['quality_score']
                ))
                
                # Insert into ingredients lookup table
                cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe['id'],))
                for ing in recipe['ingredients']:
                    cursor.execute('''
                        INSERT INTO recipe_ingredients (recipe_id, ingredient_slug, ingredient_name, amount)
                        VALUES (?, ?, ?, ?)
                    ''', (recipe['id'], ing['slug'], ing['name'], ing['amount']))
                
                total_downloaded += 1
                print(f"  ✓ {recipe['title']}")
                
            except Exception as e:
                print(f"  ✗ Error with {meal_data.get('strMeal', 'Unknown')}: {e}")
            
            time.sleep(0.1)  # Be nice even though there's no rate limit
    
    # Update statistics
    cursor.execute('''
        INSERT INTO download_log (source, recipes_downloaded, status)
        VALUES ('themealdb', ?, 'completed')
    ''', (total_downloaded,))
    
    # Update cuisine counts
    cursor.execute('''
        UPDATE statistics 
        SET recipe_count = (
            SELECT COUNT(*) FROM recipes WHERE cuisine = statistics.cuisine
        ),
        last_updated = CURRENT_TIMESTAMP
    ''')
    
    conn.commit()
    return total_downloaded

# Run the download
print("Starting download... (this is the only one that's actually fast!)")
start_time = time.time()
total = download_all_meals()
elapsed = time.time() - start_time

print(f"\n{'='*50}")
print(f"✅ DOWNLOAD COMPLETE!")
print(f"Total recipes downloaded: {total}")
print(f"Time taken: {elapsed:.1f} seconds")
print(f"Database location: {DB_PATH}")
print(f"Raw files saved to: {RAW_PATH}")
print(f"{'='*50}")

conn.close()