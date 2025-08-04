"""
The Wise Parser - Extracts hero moments from recipes for video generation
Philosophy: Humble, bounded, and wise - extracts, never creates
"""

import re
from typing import List, Dict, Optional

class WiseRecipeParser:
    """Extracts 3-4 key visual moments from recipes for 8-second videos"""
    
    def __init__(self):
        # EXPANDED hero moment indicators - comprehensive coverage
        self.hero_patterns = {
            'distinctive_techniques': [
                # Pastry work
                'puff pastry', 'phyllo', 'filo', 'shortcrust', 'choux', 'croissant',
                'lattice', 'crimp', 'fold', 'roll out', 'blind bake', 'dock',
                'egg wash', 'brush with egg', 'beaten egg', 'egg yolk',
                'pastry over', 'over the top', 'pie dish', 'rim', 'edges', 
                
                # Fire techniques
                'flambé', 'flame', 'ignite', 'torch', 'char', 'blacken', 'scorch',
                
                # Browning/coloring
                'caramelize', 'brûlée', 'golden brown', 'golden-brown', 'bronzed',
                'glazed', 'lacquered', 'burnished', 'toasted', 'charred',
                
                # Assembly/decoration
                'layer', 'stack', 'assemble', 'decorate', 'garnish', 'plate',
                'pipe', 'swirl', 'drizzle', 'dust', 'sprinkle', 'arrange',
                
                # Specialized cooking
                'sous vide', 'confit', 'cure', 'smoke', 'pickle', 'ferment',
                'deglaze', 'emulsify', 'clarify', 'temper', 'bloom', 'proof'
            ],
            
            'visual_transformations': [
                # Basic visual actions
                'brush', 'lay', 'place', 'cover', 'spread', 'coat', 'dip',
                'fill', 'fold', 'seal', 'press', 'shape',
                
                # Rising/expanding
                'rise', 'rising', 'puff up', 'puff', 'double in size', 'expand',
                'inflate', 'balloon', 'grow', 'swell', 'proof', 'ferment',
                
                # Melting/liquifying
                'melt', 'melting', 'liquify', 'dissolve', 'liquefy', 'render',
                
                # Bubbling/boiling
                'bubble', 'bubbling', 'simmer', 'boil', 'rolling boil', 'foam',
                'froth', 'effervesce', 'percolate',
                
                # Texture changes
                'crisp', 'crispy', 'crunchy', 'firm up', 'gel', 'thicken',
                'reduce', 'concentrate', 'crystallize', 'solidify', 'coagulate',
                'reduced by half', 'volume of liquid', 'reduce until',
                
                # Color changes
                'brown', 'golden', 'amber', 'mahogany', 'bronze', 'darken',
                'lighten', 'redden', 'turn golden', 'color develops',
                'browned on each side', 'until golden', 'golden-brown',
                
                # Time-based visual cues
                'until golden', 'until browned', 'until crispy', 'until bubbling',
                'until reduced', 'until thickened', 'until set', 'until firm',
                
                # Finishing
                'glaze', 'shine', 'gloss', 'sheen', 'lustrous', 'mirror-like'
            ],
            
            'signature_actions': [
                # Wrapping/encasing
                'stuff', 'wrap', 'encase', 'enrobe', 'coat', 'dredge', 'bread',
                'batter', 'crust', 'seal', 'fold over', 'tuck', 'roll up',
                
                # Liquid applications
                'baste', 'brush with', 'drizzle over', 'pour over', 'ladle',
                'spoon over', 'cascade', 'ribbon', 'stream', 'flood',
                
                # Cutting/shaping
                'julienne', 'brunoise', 'chiffonade', 'dice', 'mince', 'shave',
                'ribbon', 'mandoline', 'tournée', 'score', 'butterfly',
                
                # Final touches
                'torch', 'broil', 'gratinate', 'finish under', 'crown with',
                'top with', 'scatter over', 'nestle', 'cascade', 'fan out'
            ],
            
            'dramatic_moments': [
                # Temperature contrasts
                'shock in ice', 'plunge into', 'flash freeze', 'blast chill',
                'sear over high', 'quick fry', 'flash in pan',
                
                # Dramatic techniques
                'tableside', 'en papillote', 'salt crust', 'hay smoking',
                'cedar plank', 'banana leaf', 'parchment paper', 'foil packet',
                
                # Molecular/modern
                'spherification', 'gelification', 'foam', 'espuma', 'dust',
                'crisp', 'glass', 'chip', 'powder', 'snow',
                
                # Traditional spectacular
                'whole roasted', 'spit roast', 'tandoor', 'wood-fired',
                'coal roasted', 'salt baked', 'clay baked', 'pit cooked'
            ]
        }
        
        # Dish-type specific priorities
        self.dish_priorities = {
            'pie': ['pastry over', 'lay', 'brush with egg', 'beaten egg', 'crimp', 'edges', 'rim', 'golden-brown', 'puff pastry'],
            'stew': ['reduce', 'reduced by half', 'simmer', 'bubble', 'thicken', 'brown', 'sear'],
            'roast': ['sear', 'brown', 'baste', 'golden', 'crispy', 'rest', 'carve'],
            'baked': ['rise', 'golden', 'puff', 'crisp', 'brush', 'glaze', 'brown'],
            'fried': ['sizzle', 'golden', 'crispy', 'flip', 'bubble', 'float', 'drain'],
            'grilled': ['char', 'grill marks', 'flame', 'sear', 'blacken', 'smoke'],
            'stir-fry': ['toss', 'flame', 'sizzle', 'coat', 'glisten', 'wok'],
            'steamed': ['steam', 'moist', 'tender', 'wrap', 'basket', 'vapor']
        }
        
        # Hero shots - THE defining moment for each dish type
        self.hero_shots = {
            'pie': ['lay the pastry', 'over the top', 'cover with pastry', 'place the pastry'],
            'stew': ['ladle', 'thick and', 'rich sauce', 'tender meat'],
            'roast': ['carve', 'rest', 'crackling', 'juices run'],
            'baked': ['rise', 'golden top', 'spring back', 'dome'],
            'fried': ['flip', 'both sides', 'float', 'golden and crispy'],
            'grilled': ['grill marks', 'char lines', 'flame', 'sear marks'],
            'stir-fry': ['toss', 'wok hei', 'high heat', 'constantly moving'],
            'steamed': ['steam rises', 'tender', 'translucent', 'moist']
        }

        # Filler phrases to skip
        self.skip_phrases = [
            'preheat', 'set aside', 'remove from heat', 'let rest', 'let cool',
            'set timer', 'prepare ingredients', 'wash', 'pat dry', 'room temperature',
            'meanwhile', 'in the meantime', 'while waiting', 'clean', 'reserve',
            'keep warm', 'transfer to plate', 'repeat process', 'continue',
            'occasionally', 'if needed', 'taste for seasoning', 'adjust seasoning',
            'gather ingredients', 'read through', 'have ready'
        ]

    def extract_hero_moments(self, recipe: Dict) -> List[str]:
        """
        Extract 3-4 hero moments from a recipe
        Prioritizes based on dish type and hero shots
        """
        if not recipe or 'steps' not in recipe:
            return []
        
        # Get dish type for prioritization
        dish_type = recipe.get('dish_type', '').lower()
        title = recipe.get('title', '').lower()
        
        # Detect dish type from title if needed
        if 'pie' in title:
            dish_type = 'pie'
        elif 'stew' in title or 'braise' in title:
            dish_type = 'stew'
        elif 'roast' in title:
            dish_type = 'roast'
        
        hero_shots = []
        priority_moments = []
        regular_moments = []
        
        steps = recipe.get('steps', [])
        
        # Find moments, categorizing by importance
        for step in steps:
            instruction = step.get('instruction', '')
            moment = self._extract_moment_phrase(instruction, dish_type)
            
            if not moment:
                continue
                
            # Skip filler content
            if self._should_skip_moment(moment):
                continue
                
            # Check if already collected
            if moment in hero_shots or moment in priority_moments or moment in regular_moments:
                continue
            
            # Categorize by importance
            if self._is_hero_shot(moment, dish_type):
                hero_shots.append(moment)
            elif self._is_priority_moment(moment, dish_type):
                priority_moments.append(moment)
            else:
                regular_moments.append(moment)
        
        # Combine: hero shots first, then priority, then regular
        final_moments = hero_shots[:2] + priority_moments[:4-len(hero_shots[:2])] + regular_moments[:4-len(hero_shots[:2])-len(priority_moments[:4-len(hero_shots[:2])])]
        
        return final_moments[:4]
    
    def _is_priority_moment(self, moment: str, dish_type: str) -> bool:
        """Check if moment contains priority patterns for dish type"""
        if dish_type not in self.dish_priorities:
            return False
        
        moment_lower = moment.lower()
        priority_patterns = self.dish_priorities.get(dish_type, [])
        
        for pattern in priority_patterns:
            if pattern in moment_lower:
                return True
        return False
    
    def _should_skip_moment(self, moment: str) -> bool:
        """Check if moment should be skipped as filler"""
        moment_lower = moment.lower()
        
        # Skip if contains filler phrases
        for skip_phrase in self.skip_phrases:
            if skip_phrase in moment_lower:
                return True
        
        # Skip very short moments (likely fragments)
        if len(moment.split()) < 4:
            return True
            
        # Skip moments without visual action verbs
        action_verbs = ['pour', 'mix', 'stir', 'cook', 'bake', 'fry', 'grill',
                        'brown', 'sear', 'flip', 'roll', 'brush', 'spread', 'layer',
                        'fold', 'crimp', 'cut', 'chop', 'slice', 'dice']
        
        has_action = any(verb in moment_lower for verb in action_verbs)
        if not has_action:
            return True
            
        return False

    def _is_hero_shot(self, moment: str, dish_type: str) -> bool:
        """Check if this is THE defining moment for the dish"""
        if dish_type not in self.hero_shots:
            return False
            
        moment_lower = moment.lower()
        hero_patterns = self.hero_shots.get(dish_type, [])
        
        for pattern in hero_patterns:
            if pattern in moment_lower:
                return True
        return False
    
    def _extract_moment_phrase(self, instruction: str, dish_type: str = '') -> Optional[str]:
        """Extract the actual phrase containing a hero pattern"""
        instruction_lower = instruction.lower()
        
        # Check all pattern categories
        for patterns in self.hero_patterns.values():
            for pattern in patterns:
                if pattern in instruction_lower:
                    # Extract the phrase around this pattern
                    return self._extract_phrase_around_pattern(instruction, pattern)
                    
        return None
    
    def _extract_phrase_around_pattern(self, instruction: str, pattern: str) -> str:
        """Extract the relevant phrase around a pattern"""
        # Split by common delimiters
        segments = re.split(r'[,;.]|\bthen\b|\band\b', instruction)
        
        # Find segment containing pattern
        for segment in segments:
            if pattern in segment.lower():
                # Clean and return the actual segment
                cleaned = segment.strip()
                # Capitalize first letter if needed
                if cleaned and cleaned[0].islower():
                    cleaned = cleaned[0].upper() + cleaned[1:]
                return cleaned
                
        # Fallback: return trimmed instruction if pattern found but no segment
        if pattern in instruction.lower():
            # Return reasonable chunk around the pattern
            pattern_pos = instruction.lower().find(pattern)
            start = max(0, pattern_pos - 20)
            end = min(len(instruction), pattern_pos + len(pattern) + 30)
            
            # Try to find sentence boundaries
            text_before = instruction[:pattern_pos]
            text_after = instruction[pattern_pos:]
            
            # Look for sentence start
            last_period = text_before.rfind('. ')
            if last_period > 0 and pattern_pos - last_period < 50:
                start = last_period + 2
            
            # Look for sentence end
            next_period = text_after.find('.')
            if next_period > 0 and next_period < 50:
                end = pattern_pos + next_period
                
            return instruction[start:end].strip()
            
        return ""
    
    def build_recipe_aware_prompt(self, base_prompt: str, hero_moments: List[str]) -> str:
        """
        Integrate hero moments into existing prompt
        Preserves all cultural elements, just updates the cooking sequence
        """
        if not hero_moments:
            return base_prompt
            
        # Find and replace the cooking sequence
        if "COMPLETE COOKING SEQUENCE:" in base_prompt:
            sequence = "COMPLETE COOKING SEQUENCE: " + ". ".join(hero_moments)
            parts = base_prompt.split("COMPLETE COOKING SEQUENCE:")
            if len(parts) == 2:
                # Find end of current sequence
                after_sequence = parts[1]
                # Look for the next major section
                markers = ['Show food transformation', 'Professional', 'Audio:', 'traditional']
                earliest_marker = len(after_sequence)
                
                for marker in markers:
                    pos = after_sequence.find(marker)
                    if pos > 0 and pos < earliest_marker:
                        earliest_marker = pos
                        
                remaining = after_sequence[earliest_marker:] if earliest_marker < len(after_sequence) else ""
                return parts[0] + sequence + ". " + remaining
        
        # Should not reach here if prompts are well-formed
        return base_prompt

# Global instance
wise_parser = WiseRecipeParser()
