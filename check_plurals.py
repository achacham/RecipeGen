import json

with open('data/ingredients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

ingredients_slugs = {item['slug'] for item in data}

print("Checking which forms exist in ingredients.json:\n")

items_to_check = [
    ('lime', 'limes'),
    ('onion', 'onions'), 
    ('tomato', 'tomatoes'),
    ('apple', 'apples'),
    ('black_bean', 'black_beans')
]

for singular, plural in items_to_check:
    sing_exists = singular in ingredients_slugs
    plur_exists = plural in ingredients_slugs
    
    print(f"{singular}:")
    print(f"  Singular '{singular}': {'✓ EXISTS' if sing_exists else '✗ NOT FOUND'}")
    print(f"  Plural '{plural}': {'✓ EXISTS' if plur_exists else '✗ NOT FOUND'}")
    
    if plur_exists and not sing_exists:
        print(f"  ⚠️  Only plural form exists - this is why normalization is backwards!")
    print()