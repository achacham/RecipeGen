# check_recipes.py
import json

# Load the recipes database
with open('recipes_db.json', 'r') as f:
    data = json.load(f)
    
# Check what cuisines we have
cuisines = set()
dish_types = set()

for recipe in data['recipes']:
    cuisines.add(recipe.get('cuisine', 'unknown'))
    # Handle None dish_type
    dish_type = recipe.get('dish_type')
    if dish_type is not None:
        dish_types.add(dish_type)
    else:
        dish_types.add('unknown')

print("=== RECIPES IN DATABASE ===")
print(f"Total recipes: {len(data['recipes'])}")
print(f"\nCuisines available: {sorted(cuisines)}")
print(f"\nDish types available: {sorted(dish_types)}")

# Show a few recipe examples
print("\n=== SAMPLE RECIPES ===")
for recipe in data['recipes'][:3]:
    print(f"\n- {recipe['title']}")
    print(f"  Cuisine: {recipe.get('cuisine')}")
    print(f"  Dish Type: {recipe.get('dish_type', 'unknown')}")
    print(f"  Main ingredients: {[ing['slug'] for ing in recipe['all_ingredients'][:3]]}")