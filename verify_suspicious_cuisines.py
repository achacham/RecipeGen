"""
RecipeGen™ Suspicious Cuisine Verifier
Double-checking cuisines that SHOULD have recipes
"""

import requests
import json
import time

# These seem like they SHOULD have coverage
SUSPICIOUS_MISSING = {
    'trinbagonian': ['trinidad', 'tobago', 'caribbean', 'west indian'],
    'south korean': ['korean'],
    'scandinavian': ['nordic', 'swedish', 'norwegian', 'danish']
}

print("=== Verifying Suspicious Missing Cuisines ===\n")

# Your API keys
SPOONACULAR_KEY = "900ff67536964e419f2584505480b7fa"
EDAMAM_APP_ID = "02b029a5"
EDAMAM_APP_KEY = "fbbccebd37538d3bd2226a6b5fced68e"
RAPIDAPI_KEY = "d445dcc16emsh4df4d0ee338f675p1c4c80jsne07e22c72a79"

results = {}

for cuisine, alternatives in SUSPICIOUS_MISSING.items():
    print(f"\n🔍 Checking: {cuisine}")
    print(f"   Also trying: {alternatives}")
    
    found_in = []
    
    # Check Spoonacular
    for term in [cuisine] + alternatives:
        try:
            url = f"https://api.spoonacular.com/recipes/complexSearch"
            params = {
                'apiKey': SPOONACULAR_KEY,
                'cuisine': term,
                'number': 1
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('totalResults', 0) > 0:
                    found_in.append(f"Spoonacular as '{term}': {data['totalResults']} recipes")
                    print(f"   ✓ Found in Spoonacular as '{term}'!")
            time.sleep(0.3)
        except:
            pass
    
    # Check Edamam
    for term in [cuisine] + alternatives:
        try:
            url = "https://api.edamam.com/api/recipes/v2"
            params = {
                'type': 'public',
                'app_id': EDAMAM_APP_ID,
                'app_key': EDAMAM_APP_KEY,
                'q': term,  # Search query instead of cuisineType
                'random': 'true'
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    found_in.append(f"Edamam searching '{term}': {data['count']} recipes")
                    print(f"   ✓ Found in Edamam searching '{term}'!")
            time.sleep(0.3)
        except:
            pass
    
    # Check Tasty
    for term in [cuisine] + alternatives:
        try:
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "tasty.p.rapidapi.com"
            }
            url = "https://tasty.p.rapidapi.com/recipes/list"
            
            # Try as tag
            querystring = {
                "from": "0",
                "size": "1",
                "tags": term.replace(' ', '_')
            }
            
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    found_in.append(f"Tasty as tag '{term}': {data['count']} recipes")
                    print(f"   ✓ Found in Tasty as '{term}'!")
            
            # Also try search query
            querystring = {
                "from": "0",
                "size": "1",
                "q": term
            }
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    found_in.append(f"Tasty searching '{term}': {data['count']} recipes")
                    print(f"   ✓ Found in Tasty searching '{term}'!")
            
            time.sleep(0.3)
        except:
            pass
    
    results[cuisine] = found_in

print("\n\n=== FINAL VERIFICATION RESULTS ===")
for cuisine, found in results.items():
    if found:
        print(f"\n⚠️  {cuisine.upper()} WAS INCORRECTLY MARKED AS MISSING!")
        print(f"   Found in: {found}")
    else:
        print(f"\n✅ {cuisine}: Confirmed missing from all APIs")

# Check if Korean/South Korean confusion
print("\n\n=== SPECIAL CHECK: Korean vs South Korean ===")
# The original analysis might have 'korean' but not 'south korean'
print("This needs manual verification - 'korean' might already be in your covered list")
print("covering both North and South Korean cuisines")

print("\n\n🎯 RECOMMENDATION:")
print("If any cuisines were found above, DO NOT remove them from ingredients.json!")