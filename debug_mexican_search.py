import sqlite3

conn = sqlite3.connect('D:/RecipeGen_Database/processed/recipegen_master.db')
cursor = conn.cursor()

print("=== Debugging Mexican Chicken Search ===\n")

# 1. Check what Mexican recipes exist
print("Mexican recipes in database:")
cursor.execute("""
    SELECT id, title, dish_type 
    FROM recipes 
    WHERE cuisine = 'mexican'
""")
for id, title, dish_type in cursor.fetchall():
    print(f"  - {title} (type: {dish_type})")

# 2. Check ingredients for Crock Pot Chicken
print("\n\nIngredients for 'Crock Pot Chicken Baked Tacos':")
cursor.execute("""
    SELECT ri.ingredient_slug, ri.ingredient_name
    FROM recipe_ingredients ri
    JOIN recipes r ON r.id = ri.recipe_id
    WHERE r.title = 'Crock Pot Chicken Baked Tacos'
    ORDER BY ri.ingredient_slug
""")
for slug, name in cursor.fetchall():
    print(f"  - {slug}: {name}")

# 3. Test the exact query
print("\n\nTesting query for mexican + chicken:")
cursor.execute("""
    SELECT r.title
    FROM recipes r
    WHERE r.cuisine = 'mexican'
    AND EXISTS (
        SELECT 1 FROM recipe_ingredients ri
        WHERE ri.recipe_id = r.id
        AND ri.ingredient_slug = 'chicken'
    )
""")
results = cursor.fetchall()
print(f"Results: {len(results)}")
for title in results:
    print(f"  - {title[0]}")

# 4. Check if chicken_breast was normalized
print("\n\nChecking for 'chicken_breast' in ingredients:")
cursor.execute("""
    SELECT COUNT(*) 
    FROM recipe_ingredients 
    WHERE ingredient_slug = 'chicken_breast'
""")
count = cursor.fetchone()[0]
print(f"Found {count} recipes with 'chicken_breast'")

cursor.execute("""
    SELECT COUNT(*) 
    FROM recipe_ingredients 
    WHERE ingredient_slug = 'chicken'
""")
count = cursor.fetchone()[0]
print(f"Found {count} recipes with 'chicken'")

conn.close()
