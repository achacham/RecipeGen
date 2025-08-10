"""
Culinary Regions Auto-Updater
Analyzes ingredients.json and maintains culinary_regions.json
Ensures all cuisines are properly mapped to regions
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class CulinaryRegionsManager:
    def __init__(self):
        self.ingredients_path = Path("data/ingredients.json")
        self.regions_path = Path("data/culinary_regions.json")
        
        # Master mapping of countries to regions
        # This is the knowledge base that drives the grouping
        self.country_to_region = {
            # Southeast Asian
            'thai': 'southeast_asian',
            'vietnamese': 'southeast_asian',
            'singaporean': 'southeast_asian',
            'malaysian': 'southeast_asian',
            'indonesian': 'southeast_asian',
            'filipino': 'southeast_asian',
            'cambodian': 'southeast_asian',
            'laotian': 'southeast_asian',
            'burmese': 'southeast_asian',
            
            # East Asian
            'chinese': 'east_asian',
            'japanese': 'east_asian',
            'korean': 'east_asian',
            'south korean': 'east_asian',
            'taiwanese': 'east_asian',
            
            # South Asian
            'indian': 'south_asian',
            'pakistani': 'south_asian',
            'bangladeshi': 'south_asian',
            'sri lankan': 'south_asian',
            'nepalese': 'south_asian',
            
            # Middle Eastern
            'lebanese': 'middle_eastern',
            'turkish': 'middle_eastern',
            'syrian': 'middle_eastern',
            'jordanian': 'middle_eastern',
            'israeli': 'middle_eastern',
            'saudi arabian': 'middle_eastern',
            'yemenite': 'middle_eastern',
            'persian': 'middle_eastern',
            'iranian': 'middle_eastern',
            'egyptian': 'middle_eastern',
            
            # Mediterranean
            'greek': 'mediterranean',
            'italian': 'mediterranean',
            'spanish': 'mediterranean',
            'portuguese': 'mediterranean',
            'moroccan': 'mediterranean',
            'tunisian': 'mediterranean',
            'algerian': 'mediterranean',
            'lybian': 'mediterranean',
            'croatian': 'mediterranean',
            
            # Caribbean
            'jamaican': 'caribbean',
            'trinbagonian': 'caribbean',
            'barbadian': 'caribbean',
            'cuban': 'caribbean',
            'puerto rican': 'caribbean',
            'haitian': 'caribbean',
            'grenadian': 'caribbean',
            'caymanian': 'caribbean',
            'antiguan': 'caribbean',
            'kittitian and nevisian': 'caribbean',
            'saint-martin creole': 'caribbean',
            'belizean': 'caribbean',
            'guyanese': 'caribbean',
            
            # European
            'french': 'european',
            'british': 'european',
            'austrian': 'european',
            'hungarian': 'european',
            'polish': 'european',
            'russian': 'european',
            'finnish': 'european',
            'swiss': 'european',
            'dutch': 'european',
            'danish': 'european',
            'swedish': 'european',
            'romanian': 'european',
            'ukrainian': 'european',
            'slovakian': 'european',
            'slovenian': 'european',
            'georgian': 'european',
            'moldovian': 'european',
            'albanian': 'european',
            
            # African
            'ethiopian': 'african',
            'kenyan': 'african',
            'south african': 'african',
            'nigerian': 'african',
            'senegalese': 'african',
            'ghanaian': 'african',
            'tanzanian': 'african',
            'malinese': 'african',
            
            # South American
            'brazilian': 'south_american',
            'argentinian': 'south_american',
            'peruvian': 'south_american',
            'colombian': 'south_american',
            'venezuelan': 'south_american',
            'surinamese': 'south_american',
            
            # North American
            'american': 'north_american',
            'mexican': 'north_american',
            'canadian': 'north_american',
            
            # Specialty
            'jewish': 'specialty',
            'creole': 'specialty',
            
            # Scandinavian
            'scandinavian': 'scandinavian',
        }
    
    def load_ingredients(self) -> List[Dict]:
        """Load ingredients.json"""
        with open(self.ingredients_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_all_cuisines(self, ingredients: List[Dict]) -> Set[str]:
        """Extract all unique cuisines from ingredients"""
        all_cuisines = set()
        for ingredient in ingredients:
            if 'cuisine' in ingredient:
                for cuisine in ingredient['cuisine']:
                    all_cuisines.add(cuisine.lower().strip())
        return all_cuisines
    
    def build_regions_data(self, all_cuisines: Set[str]) -> Dict:
        """Build the culinary regions data structure"""
        regions = defaultdict(lambda: {
            'name': '',
            'countries': [],
            'unmapped_countries': []
        })
        
        unmapped_cuisines = []
        
        for cuisine in sorted(all_cuisines):
            if cuisine in self.country_to_region:
                region_key = self.country_to_region[cuisine]
                regions[region_key]['countries'].append(cuisine)
            else:
                unmapped_cuisines.append(cuisine)
        
        # Convert to regular dict and set proper names
        region_names = {
            'southeast_asian': 'Southeast Asian',
            'east_asian': 'East Asian',
            'south_asian': 'South Asian',
            'middle_eastern': 'Middle Eastern',
            'mediterranean': 'Mediterranean',
            'caribbean': 'Caribbean',
            'european': 'European',
            'african': 'African',
            'south_american': 'South American',
            'north_american': 'North American',
            'scandinavian': 'Scandinavian',
            'specialty': 'Specialty Cuisines'
        }
        
        final_regions = {}
        for region_key, region_data in regions.items():
            if region_data['countries']:  # Only include regions with countries
                final_regions[region_key] = {
                    'name': region_names.get(region_key, region_key.replace('_', ' ').title()),
                    'countries': sorted(region_data['countries'])
                }
        
        return {
            'regions': final_regions,
            'unmapped_cuisines': sorted(unmapped_cuisines),
            'statistics': {
                'total_cuisines': len(all_cuisines),
                'mapped_cuisines': len(all_cuisines) - len(unmapped_cuisines),
                'unmapped_cuisines': len(unmapped_cuisines),
                'total_regions': len(final_regions)
            }
        }
    
    def update_regions(self):
        """Main function to update culinary_regions.json"""
        print("🔍 Loading ingredients.json...")
        ingredients = self.load_ingredients()
        
        print("📊 Extracting all cuisines...")
        all_cuisines = self.extract_all_cuisines(ingredients)
        print(f"   Found {len(all_cuisines)} unique cuisines")
        
        print("🗺️  Building regional mappings...")
        regions_data = self.build_regions_data(all_cuisines)
        
        print("💾 Saving culinary_regions.json...")
        with open(self.regions_path, 'w', encoding='utf-8') as f:
            json.dump(regions_data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n✅ Update complete!")
        print(f"   Total cuisines: {regions_data['statistics']['total_cuisines']}")
        print(f"   Mapped to regions: {regions_data['statistics']['mapped_cuisines']}")
        print(f"   Unmapped: {regions_data['statistics']['unmapped_cuisines']}")
        
        if regions_data['unmapped_cuisines']:
            print("\n⚠️  Unmapped cuisines found:")
            for cuisine in regions_data['unmapped_cuisines']:
                print(f"   - {cuisine}")
            print("\n   Add these to country_to_region mapping in the script!")
        
        print("\n📁 culinary_regions.json has been updated!")

if __name__ == "__main__":
    manager = CulinaryRegionsManager()
    manager.update_regions()