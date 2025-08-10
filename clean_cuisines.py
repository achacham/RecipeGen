"""
RecipeGen™ Cuisine Cleaner
Removes unsupported cuisines from ingredients.json
"""

import json

# The 32 cuisines to REMOVE (from your analysis)
CUISINES_TO_REMOVE = [
    'antiguan', 'barbadian', 'caymanian', 'grenadian', 'kittitian and nevisian',
    'saint-martin creole', 'albanian', 'moldovan', 'slovakian',
    'slovenian', 'algerian', 'ghanaian', 'libyan', 'malinese', 'senegalese',
    'tanzanian', 'belizean', 'burmese', 'cambodian', 'creole', 'georgian',
    'guyanese', 'jordanian', 'laotian', 'persian', 'saudi arabian',
    'surinamese', 'syrian', 'yemenite'
]

print("=== RecipeGen Cuisine Cleaner ===\n")
print(f"Removing {len(CUISINES_TO_REMOVE)} unsupported cuisines from ingredients.json")

# Load current ingredients
with open('data/ingredients.json', 'r', encoding='utf-8') as f:
    ingredients = json.load(f)

print(f"Loaded {len(ingredients)} ingredients")

# Track changes
total_removed = 0
ingredients_affected = 0

# Clean each ingredient
for ingredient in ingredients:
    if 'cuisine' in ingredient and ingredient['cuisine']:
        original_count = len(ingredient['cuisine'])
        
        # Remove unsupported cuisines
        cleaned_cuisines = [c for c in ingredient['cuisine'] 
                           if c.lower() not in CUISINES_TO_REMOVE]
        
        if len(cleaned_cuisines) < original_count:
            removed = original_count - len(cleaned_cuisines)
            total_removed += removed
            ingredients_affected += 1
            
            print(f"\n{ingredient['name']}:")
            print(f"  Removed: {[c for c in ingredient['cuisine'] if c.lower() in CUISINES_TO_REMOVE]}")
            print(f"  Keeping: {cleaned_cuisines}")
            
            ingredient['cuisine'] = cleaned_cuisines

# Save backup of original
print(f"\nBacking up original to data/ingredients_backup.json")
with open('data/ingredients_backup.json', 'w', encoding='utf-8') as f:
    with open('data/ingredients.json', 'r', encoding='utf-8') as original:
        f.write(original.read())

# Save cleaned version
print(f"Saving cleaned version to data/ingredients.json")
with open('data/ingredients.json', 'w', encoding='utf-8') as f:
    json.dump(ingredients, f, indent=2, ensure_ascii=False)

# Also save the list of supported cuisines
supported_cuisines = set()
for ingredient in ingredients:
    if 'cuisine' in ingredient:
        supported_cuisines.update([c.lower() for c in ingredient['cuisine']])

with open('data/supported_cuisines.json', 'w', encoding='utf-8') as f:
    json.dump({
        'count': len(supported_cuisines),
        'cuisines': sorted(list(supported_cuisines))
    }, f, indent=2)

print(f"\n=== SUMMARY ===")
print(f"Total cuisine entries removed: {total_removed}")
print(f"Ingredients affected: {ingredients_affected}")
print(f"Supported cuisines remaining: {len(supported_cuisines)}")
print(f"\n✅ ingredients.json cleaned!")
print(f"✅ Backup saved to ingredients_backup.json")
print(f"✅ Supported cuisines list saved to supported_cuisines.json")
print(f"\n🎉 RecipeGen now shows ONLY cuisines it can deliver!")
