"""
RecipeGen™ Configurable Ingredient Normalizer
Data-driven approach for maintainable normalization
"""

import sqlite3
import json
import re
from typing import Dict, List, Set, Tuple
from difflib import get_close_matches

class IngredientNormalizer:
    def __init__(self, config_path: str = 'data/ingredient_mappings.json'):
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Load valid ingredients
        with open('data/ingredients.json', 'r', encoding='utf-8') as f:
            ingredients_data = json.load(f)
            self.valid_slugs = {ing['slug'] for ing in ingredients_data}
        
        # Connect to database
        self.conn = sqlite3.connect('D:/RecipeGen_Database/processed/recipegen_master.db')
        self.cursor = self.conn.cursor()
        
        self.normalization_log = []
    
    def detect_normalization_candidates(self) -> List[Tuple[str, str, str]]:
        """Auto-detect potential normalizations based on rules"""
        candidates = []
        
        # Get all ingredient slugs from database
        self.cursor.execute("""
            SELECT DISTINCT ingredient_slug, COUNT(*) as count 
            FROM recipe_ingredients 
            GROUP BY ingredient_slug
        """)
        all_slugs = self.cursor.fetchall()
        
        for slug, count in all_slugs:
            # Skip if already valid
            if slug in self.valid_slugs:
                continue
            
            # Check against each rule type
            normalized = self._apply_auto_rules(slug)
            if normalized and normalized != slug and normalized in self.valid_slugs:
                candidates.append((slug, normalized, 'auto_rule'))
                continue
            
            # Check configured synonyms
            for group in self.config['mappings']['synonym_groups']:
                if slug in group['synonyms']:
                    candidates.append((slug, group['canonical'], 'synonym'))
                    break
            
            # Check misspellings
            for correct, misspellings in self.config['mappings']['common_misspellings'].items():
                if slug in misspellings:
                    candidates.append((slug, correct, 'misspelling'))
                    break
            
            # Try fuzzy matching as last resort
            close_matches = get_close_matches(slug, self.valid_slugs, n=1, cutoff=0.85)
            if close_matches:
                candidates.append((slug, close_matches[0], 'fuzzy_match'))
        
        return candidates
    
    def _apply_auto_rules(self, slug: str) -> str:
        """Apply automatic detection rules"""
        rules = self.config['auto_detection_rules']
        
        # Handle pluralization
        if rules.get('detect_plurals'):
            singular = self._get_singular_form(slug)
            if singular != slug and singular in self.valid_slugs:
                return singular
        
        # Handle separators
        if rules.get('detect_hyphens_underscores'):
            # Try converting hyphens to underscores
            underscore_version = slug.replace('-', '_')
            if underscore_version in self.valid_slugs:
                return underscore_version
            
            # Try converting underscores to hyphens
            hyphen_version = slug.replace('_', '-')
            if hyphen_version in self.valid_slugs:
                return hyphen_version
        
        # Handle common prefixes/suffixes
        for prefix in rules.get('detect_common_prefixes', []):
            if slug.startswith(prefix):
                without_prefix = slug[len(prefix):]
                if without_prefix in self.valid_slugs:
                    return without_prefix
        
        return slug
    
    def _get_singular_form(self, word: str) -> str:
        """Get singular form of a word based on rules"""
        rules = self.config['mappings']['pluralization_rules']
        
        # Check no-change words
        if word in rules.get('no_change', []):
            return word
        
        # Check specific endings
        if word.endswith('ies') and len(word) > 3:
            return word[:-3] + 'y'
        elif word.endswith('ves'):
            return word[:-3] + 'f'
        elif word.endswith('es'):
            # Check if it's a valid es ending
            if word[:-2] in rules.get('es_ending', []):
                return word[:-2]
            return word[:-1] if word[:-1] in self.valid_slugs else word
        elif word.endswith('s'):
            return word[:-1]
        
        return word
    
    def add_custom_mapping(self, original: str, normalized: str, mapping_type: str):
        """Add a new mapping to the configuration"""
        if mapping_type == 'synonym':
            # Find or create synonym group
            found = False
            for group in self.config['mappings']['synonym_groups']:
                if group['canonical'] == normalized:
                    if original not in group['synonyms']:
                        group['synonyms'].append(original)
                    found = True
                    break
            
            if not found:
                self.config['mappings']['synonym_groups'].append({
                    'canonical': normalized,
                    'synonyms': [original]
                })
        
        elif mapping_type == 'misspelling':
            if normalized not in self.config['mappings']['common_misspellings']:
                self.config['mappings']['common_misspellings'][normalized] = []
            if original not in self.config['mappings']['common_misspellings'][normalized]:
                self.config['mappings']['common_misspellings'][normalized].append(original)
        
        # Save updated config
        with open('data/ingredient_mappings.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def normalize_database(self, dry_run: bool = True):
        """Run normalization with optional dry run"""
        candidates = self.detect_normalization_candidates()
        
        print(f"Found {len(candidates)} normalization candidates\n")
        
        # Group by type
        by_type = {}
        for orig, norm, norm_type in candidates:
            if norm_type not in by_type:
                by_type[norm_type] = []
            by_type[norm_type].append((orig, norm))
        
        # Show summary
        for norm_type, items in by_type.items():
            print(f"\n{norm_type.upper()} ({len(items)} items):")
            for orig, norm in items[:5]:  # Show first 5
                self.cursor.execute(
                    "SELECT COUNT(*) FROM recipe_ingredients WHERE ingredient_slug = ?",
                    (orig,)
                )
                count = self.cursor.fetchone()[0]
                print(f"  '{orig}' → '{norm}' ({count} occurrences)")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
        
        if dry_run:
            print("\n🔍 This is a DRY RUN. No changes made.")
            print("Run with dry_run=False to apply changes.")
            return
        
        # Apply normalizations
        print("\n\nApplying normalizations...")
        for orig, norm, norm_type in candidates:
            self.cursor.execute("""
                UPDATE recipe_ingredients 
                SET ingredient_slug = ? 
                WHERE ingredient_slug = ?
            """, (norm, orig))
            
            if self.cursor.rowcount > 0:
                print(f"✓ {norm_type}: '{orig}' → '{norm}' ({self.cursor.rowcount} updated)")
                self.normalization_log.append({
                    'original': orig,
                    'normalized': norm,
                    'type': norm_type,
                    'count': self.cursor.rowcount
                })
        
        self.conn.commit()
        
        # Save log
        with open('data/normalization_log.json', 'w') as f:
            json.dump(self.normalization_log, f, indent=2)
        
        print(f"\n✅ Normalization complete! Log saved to data/normalization_log.json")

# Interactive mode for unknown ingredients
def interactive_mode():
    normalizer = IngredientNormalizer()
    
    # Find ingredients not in ingredients.json
    normalizer.cursor.execute("""
        SELECT DISTINCT ingredient_slug, COUNT(*) as count 
        FROM recipe_ingredients 
        WHERE ingredient_slug NOT IN ({})
        GROUP BY ingredient_slug
        ORDER BY count DESC
        LIMIT 20
    """.format(','.join(['?'] * len(normalizer.valid_slugs))), 
    list(normalizer.valid_slugs))
    
    unknown = normalizer.cursor.fetchall()
    
    if unknown:
        print(f"\nFound {len(unknown)} unknown ingredients. Let's map them:")
        
        for slug, count in unknown:
            print(f"\n'{slug}' ({count} occurrences)")
            matches = get_close_matches(slug, normalizer.valid_slugs, n=3, cutoff=0.6)
            
            if matches:
                print("Suggestions:")
                for i, match in enumerate(matches, 1):
                    print(f"  {i}. {match}")
                print("  0. Skip")
                print("  M. Manual entry")
                
                choice = input("Choice: ").strip()
                
                if choice.isdigit() and 0 < int(choice) <= len(matches):
                    normalized = matches[int(choice) - 1]
                    normalizer.add_custom_mapping(slug, normalized, 'synonym')
                    print(f"✓ Mapped to '{normalized}'")
                elif choice.upper() == 'M':
                    normalized = input("Enter correct ingredient slug: ").strip()
                    if normalized in normalizer.valid_slugs:
                        normalizer.add_custom_mapping(slug, normalized, 'synonym')
                        print(f"✓ Mapped to '{normalized}'")
                    else:
                        print("❌ Not a valid ingredient slug")

if __name__ == "__main__":
    normalizer = IngredientNormalizer()
    
    print("=== RecipeGen Configurable Ingredient Normalizer ===\n")
    print("1. Run automatic normalization (dry run)")
    print("2. Run automatic normalization (apply changes)")
    print("3. Interactive mode for unknown ingredients")
    print("4. Show current configuration")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == '1':
        normalizer.normalize_database(dry_run=True)
    elif choice == '2':
        normalizer.normalize_database(dry_run=False)
    elif choice == '3':
        interactive_mode()
    elif choice == '4':
        print(json.dumps(normalizer.config, indent=2))