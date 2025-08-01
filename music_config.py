# music_config.py - New module for music configuration

import json
import os
from pathlib import Path

class MusicDatabase:
    def __init__(self):
        self.db_path = Path(__file__).parent / "music_database.json"
        self.music_data = self._load_database()
    
    def _load_database(self):
        """Load the music database from JSON file"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('cuisines', {})
        except FileNotFoundError:
            print("⚠️ Music database not found. Using generic music descriptions.")
            return {}
        except json.JSONDecodeError:
            print("⚠️ Music database corrupted. Using generic music descriptions.")
            return {}
    
    def get_music_description(self, cuisine):
        """Get music description for a cuisine with intelligent fallback"""
        cuisine_lower = cuisine.lower().strip()
        
        # Direct match
        if cuisine_lower in self.music_data:
            info = self.music_data[cuisine_lower]
            return self._format_description(info, cuisine)
        
        # Handle multi-word cuisines (e.g., "southeast asian")
        if ' ' in cuisine_lower:
            # Try with underscores
            cuisine_underscore = cuisine_lower.replace(' ', '_')
            if cuisine_underscore in self.music_data:
                info = self.music_data[cuisine_underscore]
                return self._format_description(info, cuisine)
            
            # Try without spaces
            cuisine_nospace = cuisine_lower.replace(' ', '')
            if cuisine_nospace in self.music_data:
                info = self.music_data[cuisine_nospace]
                return self._format_description(info, cuisine)
        
        # Generic fallback
        return f"traditional {cuisine} instrumental music"
    
    def _format_description(self, info, cuisine):
        """Format the music info into a descriptive string"""
        style = info.get('style', f'traditional {cuisine}')
        instruments = info.get('instruments', 'traditional instruments')
        characteristics = info.get('characteristics', '')
        
        description = f"{style} music featuring {instruments}"
        if characteristics:
            description += f", {characteristics}"
        
        return description
    
    def add_cuisine(self, cuisine_name, music_info=None):
        """Add a new cuisine to the database (for when ingredients.json is updated)"""
        cuisine_lower = cuisine_name.lower().strip()
        
        if music_info is None:
            # Auto-generate basic entry
            music_info = {
                "instruments": f"traditional {cuisine_name} instruments",
                "style": f"traditional {cuisine_name} folk",
                "tempo": "culturally appropriate rhythm",
                "characteristics": f"authentic {cuisine_name} musical elements"
            }
        
        self.music_data[cuisine_lower] = music_info
        self._save_database()
    
    def _save_database(self):
        """Save the updated database back to JSON"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            
            full_data['cuisines'] = self.music_data
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save music database: {e}")
    
    def sync_with_ingredients(self, ingredients_path):
        """Sync music database with cuisines found in ingredients.json"""
        try:
            with open(ingredients_path, 'r', encoding='utf-8') as f:
                ingredients = json.load(f)
            
            # Extract all unique cuisines
            all_cuisines = set()
            for ingredient in ingredients:
                if 'cuisine' in ingredient:
                    cuisines = ingredient['cuisine']
                    if isinstance(cuisines, list):
                        all_cuisines.update(c.lower().strip() for c in cuisines)
                    elif isinstance(cuisines, str):
                        all_cuisines.add(cuisines.lower().strip())
            
            # Add any missing cuisines
            added = []
            for cuisine in all_cuisines:
                if cuisine not in self.music_data:
                    self.add_cuisine(cuisine)
                    added.append(cuisine)
            
            if added:
                print(f"✅ Added {len(added)} new cuisines to music database: {', '.join(added)}")
            
            return added
            
        except Exception as e:
            print(f"⚠️ Could not sync with ingredients: {e}")
            return []

# Singleton instance
music_db = MusicDatabase()
