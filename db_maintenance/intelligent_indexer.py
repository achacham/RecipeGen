import sqlite3
import json

class IntelligentIndexer:
    def __init__(self, db_path="D:/RecipeGen_Database/processed/recipegen_master.db"):
        self.db_path = db_path
        
    def build_search_index(self):
        """Create intelligent search indices for faster, better matching"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("   🔍 Building intelligent search indices...")
        
        # 1. Create ingredient frequency table (know what's common)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredient_popularity (
                ingredient_slug TEXT PRIMARY KEY,
                recipe_count INTEGER,
                is_common BOOLEAN
            )
        ''')
        
        cursor.execute('''
            INSERT OR REPLACE INTO ingredient_popularity (ingredient_slug, recipe_count, is_common)
            SELECT 
                ingredient_slug, 
                COUNT(DISTINCT recipe_id) as count,
                CASE WHEN COUNT(DISTINCT recipe_id) > 50 THEN 1 ELSE 0 END
            FROM recipe_ingredients
            GROUP BY ingredient_slug
        ''')
        
        print("      ✅ Built ingredient popularity index")
        
        # 2. Create cuisine-ingredient affinity table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cuisine_ingredient_affinity (
                cuisine TEXT,
                ingredient_slug TEXT,
                frequency REAL,
                PRIMARY KEY (cuisine, ingredient_slug)
            )
        ''')
        
        # Calculate which ingredients are typical for each cuisine
        cursor.execute('''
            INSERT OR REPLACE INTO cuisine_ingredient_affinity
            SELECT 
                r.cuisine,
                ri.ingredient_slug,
                CAST(COUNT(*) AS REAL) / (
                    SELECT COUNT(*) FROM recipes WHERE cuisine = r.cuisine
                ) as frequency
            FROM recipes r
            JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            WHERE r.cuisine IS NOT NULL
            GROUP BY r.cuisine, ri.ingredient_slug
            HAVING frequency > 0.2  -- Appears in >20% of that cuisine's recipes
        ''')
        
        print("      ✅ Built cuisine-ingredient affinity index")
        
        # 3. Create indices for faster searches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipe_quality ON recipes(quality_score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipe_cuisine ON recipes(cuisine)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipe_dish_type ON recipes(dish_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingredients_slug ON recipe_ingredients(ingredient_slug)")
        
        conn.commit()
        conn.close()
        print("   ✅ Built all intelligent search indices")
    
    def find_similar_recipes(self, recipe_id, limit=5):
        """Find recipes similar to a given recipe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get ingredients of target recipe
        cursor.execute('''
            SELECT ingredient_slug FROM recipe_ingredients WHERE recipe_id = ?
        ''', (recipe_id,))
        target_ingredients = set(row[0] for row in cursor.fetchall())
        
        if not target_ingredients:
            return []
        
        # Find recipes with overlapping ingredients
        placeholders = ','.join(['?'] * len(target_ingredients))
        cursor.execute(f'''
            SELECT 
                ri.recipe_id,
                COUNT(*) as common_ingredients,
                r.title,
                r.quality_score
            FROM recipe_ingredients ri
            JOIN recipes r ON ri.recipe_id = r.id
            WHERE ri.ingredient_slug IN ({placeholders})
            AND ri.recipe_id != ?
            GROUP BY ri.recipe_id
            ORDER BY common_ingredients DESC, r.quality_score DESC
            LIMIT ?
        ''', list(target_ingredients) + [recipe_id, limit])
        
        results = cursor.fetchall()
        conn.close()
        return results

if __name__ == "__main__":
    # Test the indexer
    indexer = IntelligentIndexer()
    indexer.build_search_index()