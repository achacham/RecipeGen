import sqlite3

conn = sqlite3.connect('D:/RecipeGen_Database/processed/recipegen_master.db')
cursor = conn.cursor()

cursor.execute("SELECT title, dish_type FROM recipes WHERE cuisine = 'mexican'")
results = cursor.fetchall()

print(f"Mexican recipes in database: {len(results)}")
for title, dish_type in results:
    print(f"  - {title} ({dish_type})")

# Also check for chicken
print("\nChecking for ANY chicken recipes:")
cursor.execute("SELECT title, cuisine FROM recipes WHERE id IN (SELECT recipe_id FROM recipe_ingredients WHERE ingredient_name LIKE '%chicken%') LIMIT 5")
for title, cuisine in cursor.fetchall():
    print(f"  - {title} ({cuisine})")

conn.close()