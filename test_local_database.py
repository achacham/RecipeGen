"""Test if RecipeGen can search the new local database"""
import sqlite3
import json

conn = sqlite3.connect('D:/RecipeGen_Database/processed/recipegen_master.db')
cursor = conn.cursor()

# Test 1: Search for Mexican pasta (your test case!)
print("Test 1: Mexican cuisine recipes")
cursor.execute("SELECT title, dish_type FROM recipes WHERE cuisine = 'mexican'")
for row in cursor.fetchall()[:5]:
    print(f"  - {row[0]} ({row[1]})")

# Test 2: Check cuisines
print("\nTest 2: Recipes by cuisine")
cursor.execute("SELECT cuisine, COUNT(*) FROM recipes GROUP BY cuisine ORDER BY COUNT(*) DESC")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} recipes")

# Test 3: Search by ingredient
print("\nTest 3: Recipes with chicken")
cursor.execute("""
    SELECT DISTINCT r.title, r.cuisine 
    FROM recipes r 
    JOIN recipe_ingredients ri ON r.id = ri.recipe_id 
    WHERE ri.ingredient_name LIKE '%chicken%' 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  - {row[0]} ({row[1]})")