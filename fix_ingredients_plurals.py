"""
Fix ingredients.json to use singular forms consistently
Fully configurable, data-driven approach
"""

import json
import re
import shutil
from typing import Dict, List, Tuple, Optional

class ConfigurablePluralizationFixer:
    def __init__(self, rules_file: str = 'data/pluralization_rules.json'):
        """Initialize with configuration file"""
        with open(rules_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.version = self.config.get('version', '1.0')
        print(f"Loaded pluralization rules v{self.version}")
    
    def get_singular(self, word: str) -> Tuple[str, str]:
        """
        Convert plural to singular based on configured rules
        Returns: (singular_form, rule_used)
        """
        # Check if it's in the not-plural list
        if word in self.config.get('not_plural_endings_in_s', []):
            return word, "not_plural"
        
        # Check irregular plurals first
        irregular = self.config.get('irregular_plurals', {})
        if word in irregular:
            return irregular[word], "irregular"
        
        # Check no-change words
        if word in self.config.get('no_change_words', []):
            return word, "no_change"
        
        # Apply pattern rules in order
        for rule in self.config.get('rules', []):
            pattern = rule.get('pattern')
            if not pattern:
                continue
            
            if re.search(pattern, word):
                # Check conditions if any
                condition = rule.get('condition')
                if condition:
                    if not self._evaluate_condition(word, condition):
                        continue
                
                # Apply replacement
                if 'replacement' in rule:
                    replacement = rule['replacement']
                    if replacement.startswith('$'):
                        # Backreference
                        result = re.sub(pattern, replacement[1:], word)
                    else:
                        # Simple replacement
                        result = re.sub(pattern, replacement, word)
                    
                    return result, f"rule_{pattern}"
                
                # Special handling
                if rule.get('special_handling') == 'check_irregular_first':
                    # This means we should have caught it in irregular list
                    continue
        
        # No rules matched
        return word, "no_match"
    
    def _evaluate_condition(self, word: str, condition: str) -> bool:
        """Evaluate a condition string safely"""
        # Safe evaluation context
        context = {
            'length': len(word),
            'word': word,
            'vowels': 'aeiou',
            'char': word  # For indexing like char[-4]
        }
        
        # Simple conditions we can safely evaluate
        if condition == "default_rule":
            return True
        
        # For more complex conditions, we'd need a proper parser
        # For now, handle the specific case we need
        if "length > 3 and char[-4] not in vowels" in condition:
            return len(word) > 3 and word[-4] not in 'aeiou'
        
        return True
    
    def add_rule(self, pattern: str, replacement: str, examples: List[str], 
                 condition: Optional[str] = None):
        """Add a new rule to the configuration"""
        new_rule = {
            "pattern": pattern,
            "replacement": replacement,
            "examples": examples
        }
        if condition:
            new_rule["condition"] = condition
        
        self.config['rules'].insert(-1, new_rule)  # Insert before default rule
        self._save_config()
    
    def add_irregular(self, plural: str, singular: str):
        """Add a new irregular plural mapping"""
        if 'irregular_plurals' not in self.config:
            self.config['irregular_plurals'] = {}
        
        self.config['irregular_plurals'][plural] = singular
        self._save_config()
    
    def _save_config(self):
        """Save updated configuration"""
        with open('data/pluralization_rules.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        print("✓ Updated pluralization rules")
    
    def analyze_ingredients(self, ingredients_file: str = 'data/ingredients.json'):
        """Analyze ingredients file for needed fixes"""
        with open(ingredients_file, 'r', encoding='utf-8') as f:
            ingredients = json.load(f)
        
        print(f"\nAnalyzing {len(ingredients)} ingredients...\n")
        
        fixes_needed = []
        duplicates = []
        skipped = []
        
        # Build set of existing slugs for duplicate detection
        existing_slugs = {ing['slug'] for ing in ingredients}
        
        for ingredient in ingredients:
            slug = ingredient['slug']
            name = ingredient['name']
            
            # Skip if doesn't end in 's'
            if not slug.endswith('s'):
                continue
            
            singular_slug, rule = self.get_singular(slug)
            
            if singular_slug == slug:
                if rule in ["not_plural", "no_change"]:
                    skipped.append((slug, rule))
                continue
            
            # Check for duplicates
            if singular_slug in existing_slugs:
                duplicates.append({
                    'original': slug,
                    'singular': singular_slug,
                    'rule': rule
                })
            else:
                fixes_needed.append({
                    'ingredient': ingredient,
                    'original_slug': slug,
                    'singular_slug': singular_slug,
                    'original_name': name,
                    'rule': rule
                })
        
        return fixes_needed, duplicates, skipped
    
    def fix_ingredients(self, dry_run: bool = True):
        """Fix plural ingredients with optional dry run"""
        fixes_needed, duplicates, skipped = self.analyze_ingredients()
        
        # Display results
        print(f"Found {len(fixes_needed)} ingredients to convert:\n")
        
        # Group by rule
        by_rule = {}
        for fix in fixes_needed:
            rule = fix['rule']
            if rule not in by_rule:
                by_rule[rule] = []
            by_rule[rule].append(fix)
        
        for rule, fixes in by_rule.items():
            print(f"\n{rule.upper()} ({len(fixes)} items):")
            for fix in fixes[:3]:
                print(f"  '{fix['original_slug']}' → '{fix['singular_slug']}'")
            if len(fixes) > 3:
                print(f"  ... and {len(fixes) - 3} more")
        
        if duplicates:
            print(f"\n⚠️  Warning: {len(duplicates)} would create duplicates:")
            for dup in duplicates[:3]:
                print(f"  '{dup['original']}' → '{dup['singular']}' (already exists)")
        
        if skipped:
            print(f"\n✓ Correctly skipped {len(skipped)} items")
        
        if dry_run:
            print("\n🔍 DRY RUN - no changes made")
            print("Run with dry_run=False to apply changes")
            return
        
        if not fixes_needed:
            print("\n✅ No changes needed!")
            return
        
        # Apply fixes
        response = input(f"\nApply {len(fixes_needed)} fixes? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        # Backup first
        shutil.copy('data/ingredients.json', 'data/ingredients_backup.json')
        print("✓ Backup saved")
        
        # Load ingredients again for modification
        with open('data/ingredients.json', 'r', encoding='utf-8') as f:
            ingredients = json.load(f)
        
        # Apply fixes
        for fix in fixes_needed:
            for ingredient in ingredients:
                if ingredient['slug'] == fix['original_slug']:
                    ingredient['slug'] = fix['singular_slug']
                    # Update name if it's just the formatted slug
                    if ingredient['name'].lower() == fix['original_slug'].replace('_', ' '):
                        ingredient['name'] = fix['singular_slug'].replace('_', ' ').title()
                    break
        
        # Save
        with open('data/ingredients.json', 'w', encoding='utf-8') as f:
            json.dump(ingredients, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {len(fixes_needed)} ingredients!")
        
        # Update mappings
        self._update_ingredient_mappings(fixes_needed)
    
    def _update_ingredient_mappings(self, fixes: List[Dict]):
        """Update ingredient_mappings.json with plural->singular mappings"""
        with open('data/ingredient_mappings.json', 'r') as f:
            mappings = json.load(f)
        
        for fix in fixes:
            found = False
            for group in mappings['mappings']['synonym_groups']:
                if group['canonical'] == fix['singular_slug']:
                    if fix['original_slug'] not in group['synonyms']:
                        group['synonyms'].append(fix['original_slug'])
                    found = True
                    break
            
            if not found:
                mappings['mappings']['synonym_groups'].append({
                    'canonical': fix['singular_slug'],
                    'synonyms': [fix['original_slug']]
                })
        
        with open('data/ingredient_mappings.json', 'w') as f:
            json.dump(mappings, f, indent=2)
        
        print("✅ Updated ingredient mappings!")

def interactive_rule_builder():
    """Interactive mode to build rules from unknown cases"""
    fixer = ConfigurablePluralizationFixer()
    
    print("\n=== Interactive Rule Builder ===")
    print("Enter plural words to test/add rules (or 'quit' to exit):\n")
    
    while True:
        plural = input("Plural word: ").strip()
        if plural.lower() == 'quit':
            break
        
        singular, rule = fixer.get_singular(plural)
        print(f"  Result: '{plural}' → '{singular}' (rule: {rule})")
        
        if rule == "no_match" or singular == plural:
            correct = input("  Correct singular form: ").strip()
            if correct and correct != plural:
                # Determine what kind of rule to add
                if not re.match(r'^[a-z]+[aeiou]?[a-z]*s$', plural):
                    # Irregular
                    fixer.add_irregular(plural, correct)
                    print(f"  ✓ Added as irregular plural")
                else:
                    # Try to create a pattern
                    pattern = input("  Pattern (or press Enter for irregular): ").strip()
                    if pattern:
                        examples = [f"{plural}→{correct}"]
                        fixer.add_rule(pattern, correct, examples)
                        print(f"  ✓ Added new rule")
                    else:
                        fixer.add_irregular(plural, correct)
                        print(f"  ✓ Added as irregular plural")

if __name__ == "__main__":
    print("=== Configurable Ingredient Plural Fixer ===\n")
    print("1. Analyze ingredients (dry run)")
    print("2. Fix plural ingredients")
    print("3. Interactive rule builder")
    print("4. Show current rules")
    
    choice = input("\nChoice (1-4): ").strip()
    
    fixer = ConfigurablePluralizationFixer()
    
    if choice == '1':
        fixer.fix_ingredients(dry_run=True)
    elif choice == '2':
        fixer.fix_ingredients(dry_run=False)
    elif choice == '3':
        interactive_rule_builder()
    elif choice == '4':
        print(json.dumps(fixer.config, indent=2))