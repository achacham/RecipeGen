import json
from pathlib import Path

def update_supported_cuisines():
    """
    Automatically generate supported_cuisines.json from all data sources
    """
    cuisines = set()
    
    # 1. Get cuisines from ingredients.json
    ingredients_path = Path(__file__).parent / "data" / "ingredients.json"
    with open(ingredients_path, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)
        for ingredient in ingredients:
            for cuisine in ingredient.get('cuisine', []):
                cuisines.add(cuisine.lower().strip())
    
    # 2. Get cuisines from culinary_regions.json
    regions_path = Path(__file__).parent / "data" / "culinary_regions.json"
    with open(regions_path, 'r', encoding='utf-8') as f:
        regions_data = json.load(f)
        
        # Get all countries from regions
        for region in regions_data.get('regions', {}).values():
            for subregion in region.get('subregions', {}).values():
                for country in subregion.get('countries', []):
                    cuisines.add(country.lower().strip())
        
        # Get all countries from mappings
        for country in regions_data.get('country_to_spoonacular', {}).keys():
            cuisines.add(country.lower().strip())
    
    # 3. Get cuisines from local database (if accessible)
    try:
        import sqlite3
        conn = sqlite3.connect("D:/RecipeGen_Database/processed/recipegen_master.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT cuisine FROM recipes WHERE cuisine IS NOT NULL")
        for row in cursor.fetchall():
            if row[0]:
                cuisines.add(row[0].lower().strip())
        conn.close()
    except:
        print("Could not read from database, skipping...")
    
    # Remove any empty strings or 'universal' entries
    cuisines.discard('')
    cuisines.discard('universal')
    
    # Sort the cuisines
    sorted_cuisines = sorted(list(cuisines))
    
    # Save to supported_cuisines.json
    output = {
        "count": len(sorted_cuisines),
        "cuisines": sorted_cuisines,
        "generated_from": [
            "ingredients.json",
            "culinary_regions.json",
            "local_database"
        ],
        "last_updated": __import__('datetime').datetime.now().isoformat()
    }
    
    output_path = Path(__file__).parent / "data" / "supported_cuisines.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Updated supported_cuisines.json with {len(sorted_cuisines)} cuisines")
    
    # Show what's new
    old_path = Path(__file__).parent / "data" / "supported_cuisines_backup.json"
    if old_path.exists():
        with open(old_path, 'r') as f:
            old_data = json.load(f)
            old_cuisines = set(old_data.get('cuisines', []))
            new_additions = cuisines - old_cuisines
            if new_additions:
                print(f"📍 New cuisines added: {sorted(list(new_additions))}")

if __name__ == "__main__":
    update_supported_cuisines()