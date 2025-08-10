"""
RecipeGen™ Master Database Creator
Creates the unified recipe database with proper schema
"""

import sqlite3
import json
from datetime import datetime

print("=== Creating RecipeGen Master Database ===\n")

# Create the database in the new folder structure
import os
db_path = "D:/RecipeGen_Database/processed/recipegen_master.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the main recipes table
cursor.execute('''
CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    cuisine TEXT NOT NULL,
    dish_type TEXT,
    ingredients JSON NOT NULL,
    instructions JSON NOT NULL,
    prep_time INTEGER,
    cook_time INTEGER,
    total_time INTEGER,
    servings INTEGER,
    difficulty TEXT,
    source TEXT NOT NULL,
    source_id TEXT,
    source_url TEXT,
    image_url TEXT,
    video_url TEXT,
    nutrition JSON,
    tags JSON,
    quality_score INTEGER DEFAULT 50,
    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    times_served INTEGER DEFAULT 0,
    user_rating REAL DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE
)
''')

# Create indices for fast searching
indices = [
    "CREATE INDEX IF NOT EXISTS idx_cuisine ON recipes(cuisine)",
    "CREATE INDEX IF NOT EXISTS idx_dish_type ON recipes(dish_type)", 
    "CREATE INDEX IF NOT EXISTS idx_source ON recipes(source)",
    "CREATE INDEX IF NOT EXISTS idx_quality ON recipes(quality_score DESC)",
    "CREATE INDEX IF NOT EXISTS idx_title ON recipes(title)",
    "CREATE INDEX IF NOT EXISTS idx_verified ON recipes(is_verified)"
]

for index in indices:
    cursor.execute(index)
    print(f"✓ {index.split('idx_')[1].split(' ')[0]} index created")

# Create ingredients lookup table for faster searching
cursor.execute('''
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id TEXT,
    ingredient_slug TEXT,
    ingredient_name TEXT,
    amount TEXT,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
)
''')

cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingredient_slug ON recipe_ingredients(ingredient_slug)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipe_ingredient ON recipe_ingredients(recipe_id)")

# Create download tracking table
cursor.execute('''
CREATE TABLE IF NOT EXISTS download_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recipes_downloaded INTEGER,
    status TEXT,
    error_message TEXT
)
''')

# Create statistics table
cursor.execute('''
CREATE TABLE IF NOT EXISTS statistics (
    cuisine TEXT PRIMARY KEY,
    recipe_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
print(f"\n✅ Database created at: {db_path}")
print(f"✅ All tables and indices created successfully!")

# Initialize statistics with our 52 supported cuisines
with open('data/supported_cuisines.json', 'r') as f:
    supported = json.load(f)
    
for cuisine in supported['cuisines']:
    cursor.execute('''
        INSERT OR IGNORE INTO statistics (cuisine, recipe_count) 
        VALUES (?, 0)
    ''', (cuisine,))

conn.commit()
print(f"✅ Initialized statistics for {len(supported['cuisines'])} cuisines")

conn.close()