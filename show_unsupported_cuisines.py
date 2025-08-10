"""
RecipeGen™ Unsupported Cuisines Report
Shows which cuisines have ZERO recipes in any API
"""

import json

# Load the analysis results
with open('api_gap_analysis.json', 'r') as f:
    results = json.load(f)

missing = sorted(results['missing'])
covered = sorted(results['covered'])

print("=" * 60)
print("CUISINES WITH ZERO RECIPES IN ANY API (53)")
print("=" * 60)
print("\nThese cuisines will ALWAYS result in 'We couldn't find...':\n")

# Group by region for easier review
regions = {
    'Caribbean': ['antiguan', 'barbadian', 'caymanian', 'cuban', 'grenadian', 
                  'guyanese', 'haitian', 'kittitian and nevisian', 'puerto rican', 
                  'saint-martin creole', 'surinamese', 'trinbagonian'],
    
    'African': ['algerian', 'ethiopian', 'ghanaian', 'libyan', 'malinese', 
                'nigerian', 'senegalese', 'south african', 'tanzanian'],
    
    'South American': ['argentinian', 'brazilian'],
    
    'Middle Eastern': ['iranian', 'israeli', 'jordanian', 'lebanese', 
                       'saudi arabian', 'syrian', 'yemenite'],
    
    'Asian': ['burmese', 'cambodian', 'indonesian', 'laotian', 'pakistani', 
              'singaporean', 'south korean'],
    
    'European': ['albanian', 'austrian', 'danish', 'finnish', 'georgian', 
                 'hungarian', 'moldovan', 'romanian', 'scandinavian', 'slovakian', 
                 'slovenian', 'swedish', 'swiss'],
    
    'Other': ['belizean', 'creole', 'persian']
}

for region, cuisines in regions.items():
    region_missing = [c for c in cuisines if c in missing]
    if region_missing:
        print(f"\n{region} ({len(region_missing)}):")
        for cuisine in region_missing:
            print(f"  ❌ {cuisine}")

print("\n" + "=" * 60)
print(f"RECOMMENDATION: Remove these {len(missing)} cuisines from RecipeGen")
print("They will ONLY produce fallback recipes!")
print("=" * 60)

# Also show what you CAN support
print(f"\n\nCUISINES WITH API SUPPORT ({len(covered)}):")
print("Keep these - they have real recipes:\n")
for cuisine in covered:
    print(f"  ✅ {cuisine}")