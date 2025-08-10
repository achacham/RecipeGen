"""
Culinary Regions Auto-Updater
Analyzes ingredients.json and maintains culinary_regions.json
Ensures all cuisines are properly mapped to regions and subregions
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class CulinaryRegionsManager:
    def __init__(self):
        self.ingredients_path = Path("data/ingredients.json")
        self.regions_path = Path("data/culinary_regions.json")
        
        # WORLD ATLAS - Geopolitical structure (stable for years)
        # This is geographical fact, not recipe logic
        self.world_structure = {
            'african': {
                'name': 'African',
                'subregions': {
                    'north_african': {
                        'name': 'North African',
                        'countries': ['moroccan', 'tunisian', 'algerian', 'egyptian', 'libyan']
                    },
                    'west_african': {
                        'name': 'West African',
                        'countries': ['nigerian', 'ghanaian', 'senegalese', 'malinese', 'ivorian', 'burkinabe', 'togolese', 'beninese']
                    },
                    'east_african': {
                        'name': 'East African',
                        'countries': ['ethiopian', 'kenyan', 'tanzanian', 'ugandan', 'rwandan', 'burundian', 'somali', 'eritrean']
                    },
                    'central_african': {
                        'name': 'Central African',
                        'countries': ['cameroonian', 'congolese', 'chadian', 'central african', 'gabonese']
                    },
                    'southern_african': {
                        'name': 'Southern African',
                        'countries': ['south african', 'zimbabwean', 'zambian', 'mozambican', 'namibian', 'botswanan']
                    }
                }
            },
            'asian': {
                'name': 'Asian',
                'subregions': {
                    'southeast_asian': {
                        'name': 'Southeast Asian',
                        'countries': ['thai', 'vietnamese', 'singaporean', 'malaysian', 'indonesian', 'filipino', 'cambodian', 'laotian', 'burmese', 'timorese', 'bruneian']
                    },
                    'east_asian': {
                        'name': 'East Asian',
                        'countries': ['chinese', 'japanese', 'korean', 'south korean', 'taiwanese', 'mongolian', 'macanese', 'hong kong']
                    },
                    'south_asian': {
                        'name': 'South Asian',
                        'countries': ['indian', 'pakistani', 'bangladeshi', 'sri lankan', 'nepalese', 'bhutanese', 'maldivian', 'afghan']
                    },
                    'central_asian': {
                        'name': 'Central Asian',
                        'countries': ['kazakh', 'uzbek', 'turkmen', 'tajik', 'kyrgyz']
                    },
                    'western_asian': {
                        'name': 'Western Asian',
                        'countries': ['persian', 'iranian', 'yemenite', 'saudi arabian', 'emirati', 'kuwaiti', 'bahraini', 'qatari', 'omani', 'iraqi']
                    }
                }
            },
            'european': {
                'name': 'European',
                'subregions': {
                    'western_european': {
                        'name': 'Western European',
                        'countries': ['french', 'british', 'irish', 'dutch', 'belgian', 'luxembourgish', 'german', 'austrian', 'swiss']
                    },
                    'southern_european': {
                        'name': 'Southern European',
                        'countries': ['italian', 'spanish', 'portuguese', 'greek', 'maltese', 'cypriot', 'san marinese', 'vatican']
                    },
                    'northern_european': {
                        'name': 'Northern European',
                        'countries': ['swedish', 'norwegian', 'danish', 'finnish', 'icelandic', 'faroese', 'greenlandic', 'scandinavian']
                    },
                    'eastern_european': {
                        'name': 'Eastern European',
                        'countries': ['polish', 'hungarian', 'romanian', 'ukrainian', 'russian', 'croatian', 'serbian', 'bulgarian', 'slovenian', 'slovakian', 'czech', 'moldovan', 'albanian', 'macedonian', 'bosnian', 'montenegrin', 'kosovar', 'belarusian', 'lithuanian', 'latvian', 'estonian']
                    },
                    'caucasian': {
                        'name': 'Caucasian',
                        'countries': ['georgian', 'armenian', 'azerbaijani']
                    }
                }
            },
            'middle_eastern': {
                'name': 'Middle Eastern',
                'subregions': {
                    'levantine': {
                        'name': 'Levantine',
                        'countries': ['lebanese', 'syrian', 'jordanian', 'palestinian', 'israeli']
                    },
                    'anatolian': {
                        'name': 'Anatolian',
                        'countries': ['turkish']
                    }
                }
            },
            'caribbean': {
                'name': 'Caribbean',
                'subregions': {
                    'greater_antilles': {
                        'name': 'Greater Antilles',
                        'countries': ['cuban', 'jamaican', 'haitian', 'dominican', 'puerto rican', 'caymanian']
                    },
                    'lesser_antilles': {
                        'name': 'Lesser Antilles',
                        'countries': ['trinbagonian', 'barbadian', 'grenadian', 'antiguan', 'kittitian and nevisian', 'saint lucian', 'vincentian', 'dominican']
                    },
                    'mainland_caribbean': {
                        'name': 'Mainland Caribbean',
                        'countries': ['belizean', 'guyanese', 'surinamese', 'french guianese']
                    },
                    'creole': {
                        'name': 'Creole',
                        'countries': ['creole', 'saint-martin creole']
                    }
                }
            },
            'north_american': {
                'name': 'North American',
                'subregions': {
                    'north_american': {
                        'name': 'North American',
                        'countries': ['american', 'canadian', 'mexican']
                    }
                }
            },
            'south_american': {
                'name': 'South American',
                'subregions': {
                    'amazonian': {
                        'name': 'Amazonian',
                        'countries': ['brazilian', 'peruvian', 'colombian', 'venezuelan', 'ecuadorian', 'bolivian']
                    },
                    'southern_cone': {
                        'name': 'Southern Cone',
                        'countries': ['argentinian', 'chilean', 'uruguayan', 'paraguayan']
                    }
                }
            },
            'oceanian': {
                'name': 'Oceanian',
                'subregions': {
                    'australasian': {
                        'name': 'Australasian',
                        'countries': ['australian', 'new zealand']
                    },
                    'polynesian': {
                        'name': 'Polynesian',
                        'countries': ['hawaiian', 'tahitian', 'samoan', 'tongan', 'fijian']
                    },
                    'melanesian': {
                        'name': 'Melanesian',
                        'countries': ['papua new guinean', 'solomon islander', 'vanuatuan', 'new caledonian']
                    }
                }
            },
            'specialty': {
                'name': 'Specialty Cuisines',
                'subregions': {
                    'religious': {
                        'name': 'Religious Cuisines',
                        'countries': ['jewish', 'halal', 'buddhist', 'jain', 'hindu vegetarian']
                    },
                    'regional_american': {
                        'name': 'Regional American',
                        'countries': ['cajun', 'southern', 'tex-mex', 'new england', 'pacific northwest']
                    },
                    'fusion': {
                        'name': 'Fusion',
                        'countries': ['fusion', 'modern', 'international']
                    }
                }
            }
        }
        
        # Country to Spoonacular mapping (the limited 26 categories)
        self.country_to_spoonacular = {
            # African countries (all map to generic "African")
            "moroccan": "African",
            "tunisian": "African",
            "algerian": "African",
            "egyptian": "African",
            "libyan": "African",
            "ethiopian": "African",
            "kenyan": "African",
            "tanzanian": "African",
            "nigerian": "African",
            "ghanaian": "African",
            "senegalese": "African",
            "south african": "African",
            "malinese": "African",
            
            # Asian - Southeast (mostly generic "Asian" except Thai/Vietnamese)
            "thai": "Thai",
            "vietnamese": "Vietnamese",
            "singaporean": "Asian",
            "malaysian": "Asian",
            "indonesian": "Asian",
            "filipino": "Asian",
            "cambodian": "Asian",
            "laotian": "Asian",
            "burmese": "Asian",
            
            # Asian - East (some have their own categories)
            "chinese": "Chinese",
            "taiwanese": "Chinese",
            "japanese": "Japanese",
            "korean": "Korean",
            "south korean": "Korean",
            "mongolian": "Asian",
            
            # Asian - South (all map to "Indian")
            "indian": "Indian",
            "pakistani": "Indian",
            "bangladeshi": "Indian",
            "sri lankan": "Indian",
            "nepalese": "Indian",
            
            # Caribbean (all map to "Caribbean")
            "jamaican": "Caribbean",
            "trinbagonian": "Caribbean",
            "barbadian": "Caribbean",
            "cuban": "Caribbean",
            "puerto rican": "Caribbean",
            "haitian": "Caribbean",
            "grenadian": "Caribbean",
            "caymanian": "Caribbean",
            "antiguan": "Caribbean",
            "kittitian and nevisian": "Caribbean",
            "saint-martin creole": "Caribbean",
            "belizean": "Caribbean",
            "guyanese": "Caribbean",
            "surinamese": "Caribbean",
            
            # European - Western (some have their own)
            "french": "French",
            "italian": "Italian",
            "spanish": "Spanish",
            "portuguese": "European",
            "british": "British",
            "irish": "Irish",
            "dutch": "European",
            "belgian": "European",
            "swiss": "European",
            "austrian": "European",
            "german": "German",
            
            # European - Eastern (all lumped as "Eastern European")
            "polish": "Eastern European",
            "hungarian": "Eastern European",
            "romanian": "Eastern European",
            "ukrainian": "Eastern European",
            "russian": "Eastern European",
            "croatian": "Eastern European",
            "slovenian": "Eastern European",
            "slovakian": "Eastern European",
            "moldovan": "Eastern European",
            "albanian": "Eastern European",
            "georgian": "Eastern European",
            
            # European - Nordic
            "swedish": "Nordic",
            "danish": "Nordic",
            "finnish": "Nordic",
            "norwegian": "Nordic",
            "scandinavian": "Nordic",
            
            # Mediterranean/Middle Eastern
            "greek": "Greek",
            "turkish": "Mediterranean",
            "israeli": "Jewish",
            "lebanese": "Middle Eastern",
            "syrian": "Middle Eastern",
            "jordanian": "Middle Eastern",
            "saudi arabian": "Middle Eastern",
            "yemenite": "Middle Eastern",
            "persian": "Middle Eastern",
            "iranian": "Middle Eastern",
            
            # Americas
            "american": "American",
            "mexican": "Mexican",
            "canadian": "American",
            "brazilian": "Latin American",
            "argentinian": "Latin American",
            "peruvian": "Latin American",
            "colombian": "Latin American",
            "venezuelan": "Latin American",
            
            # Special categories
            "jewish": "Jewish",
            "cajun": "Cajun",
            "creole": "Cajun",
            
            # Generic fallback
            "international": "American",
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
        """Build the nested culinary regions data structure"""
        # Deep copy the world structure to populate with actual data
        regions_output = {}
        
        # Track which cuisines from ingredients.json we've mapped
        mapped_cuisines = set()
        unmapped_cuisines = []
        
        # Build the nested structure
        for region_key, region_data in self.world_structure.items():
            region_output = {
                'name': region_data['name'],
                'subregions': {}
            }
            
            for subregion_key, subregion_data in region_data['subregions'].items():
                # Find which countries from this subregion exist in ingredients.json
                countries_in_ingredients = []
                for country in subregion_data['countries']:
                    if country in all_cuisines:
                        countries_in_ingredients.append(country)
                        mapped_cuisines.add(country)
                
                # Only include subregion if it has countries in ingredients.json
                if countries_in_ingredients:
                    region_output['subregions'][subregion_key] = {
                        'name': subregion_data['name'],
                        'countries': sorted(countries_in_ingredients)
                    }
            
            # Only include region if it has subregions with data
            if region_output['subregions']:
                regions_output[region_key] = region_output
        
        # Find unmapped cuisines
        for cuisine in all_cuisines:
            if cuisine not in mapped_cuisines:
                unmapped_cuisines.append(cuisine)
        
        # Build spoonacular mapping for found cuisines only
        active_spoonacular_mappings = {}
        for cuisine in all_cuisines:
            if cuisine in self.country_to_spoonacular:
                active_spoonacular_mappings[cuisine] = self.country_to_spoonacular[cuisine]
        
        return {
            'regions': regions_output,
            'country_to_spoonacular': active_spoonacular_mappings,
            'unmapped_cuisines': sorted(unmapped_cuisines),
            'statistics': {
                'total_cuisines': len(all_cuisines),
                'mapped_cuisines': len(mapped_cuisines),
                'unmapped_cuisines': len(unmapped_cuisines),
                'total_regions': len(regions_output),
                'total_subregions': sum(len(r['subregions']) for r in regions_output.values()),
                'spoonacular_categories': len(set(active_spoonacular_mappings.values()))
            }
        }
    
    def update_regions(self):
        """Main function to update culinary_regions.json"""
        print("🔍 Loading ingredients.json...")
        ingredients = self.load_ingredients()
        
        print("📊 Extracting all cuisines...")
        all_cuisines = self.extract_all_cuisines(ingredients)
        print(f"   Found {len(all_cuisines)} unique cuisines")
        
        print("🗺️  Building nested regional mappings...")
        regions_data = self.build_regions_data(all_cuisines)
        
        print("💾 Saving culinary_regions.json...")
        with open(self.regions_path, 'w', encoding='utf-8') as f:
            json.dump(regions_data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n✅ Update complete!")
        print(f"   Total cuisines: {regions_data['statistics']['total_cuisines']}")
        print(f"   Mapped to regions: {regions_data['statistics']['mapped_cuisines']}")
        print(f"   Active regions: {regions_data['statistics']['total_regions']}")
        print(f"   Active subregions: {regions_data['statistics']['total_subregions']}")
        print(f"   Unmapped: {regions_data['statistics']['unmapped_cuisines']}")
        print(f"   Spoonacular categories used: {regions_data['statistics']['spoonacular_categories']} (out of 26)")
        
        if regions_data['unmapped_cuisines']:
            print("\n⚠️  Unmapped cuisines found:")
            for cuisine in regions_data['unmapped_cuisines']:
                print(f"   - {cuisine}")
            print("\n   Add these to the world_structure in this script!")
        
        print("\n📁 culinary_regions.json has been updated with nested structure!")
        print("🌍 Like an atlas - stable geographical data that rarely changes")

if __name__ == "__main__":
    manager = CulinaryRegionsManager()
    manager.update_regions()
