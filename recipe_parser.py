"""
The Wise Parser - Extracts hero moments from recipes for video generation
Philosophy: Humble, bounded, and wise - extracts, never creates
Now with Narrative Intelligence: tells stories, not just moments
Enhanced with Fuzzy Tree Logic: multi-dimensional decision making
"""

import re
from typing import List, Dict, Optional, Tuple

# FUZZY WEIGHT TUNING GUIDE:
# Format: [completeness, cooking_action, visual_impact, assembly_bonus, minimum_threshold]
#
# 'completeness': Higher = favors complete sentences, lower = allows shorter phrases
# 'cooking_action': Higher = emphasizes frying/searing/cooking, lower = de-emphasizes
# 'visual_impact': Higher = prioritizes visual transformations, lower = focuses on actions
# 'assembly_bonus': Higher = boosts assembly/plating steps, lower = pure cooking focus
# 'minimum_threshold': Higher = stricter selection, lower = more inclusive
#
# Example configurations:
# [0.3, 0.3, 0.2, 0.3, 0.3] = Balanced approach
# [0.2, 0.5, 0.2, 0.1, 0.3] = Cooking-focused (more frying, searing)
# [0.2, 0.2, 0.5, 0.2, 0.3] = Visual-focused (transformations, color changes)
# [0.3, 0.2, 0.2, 0.5, 0.3] = Assembly-focused (good for pies, layered dishes)
# [0.5, 0.2, 0.2, 0.2, 0.4] = Fragment-elimination (complete sentences only)
#
# The weights work together - experiment to find your optimal configuration
class WiseRecipeParser:
    """
    Extracts 3-4 key visual moments from recipes for 8-second videos
    Uses fuzzy logic trees for intelligent moment selection
    """
    
    # FUZZY CONTROL PARAMETERS - Adjust these for different results
    # These act like trim pots on a circuit board - tune them to taste!
    FUZZY_WEIGHTS = {
        'completeness': 0.3,      # How much to value complete sentences
        'cooking_action': 0.3,    # How much to prioritize cooking verbs
        'visual_impact': 0.2,     # How much to value visual words
        'assembly_bonus': 0.3,    # Extra weight for assembly (pies, etc)
        'minimum_threshold': 0.3  # Minimum score to consider a moment
    }
    
    # Developer testing presets - like DIP switches for quick configuration changes
    # Format: [completeness, cooking_action, visual_impact, assembly_bonus, minimum_threshold]
    FUZZY_PRESETS = {
        'balanced': [0.3, 0.3, 0.2, 0.3, 0.3],
        'cooking_focused': [0.2, 0.5, 0.2, 0.1, 0.3],
        'visual_focused': [0.2, 0.2, 0.5, 0.2, 0.3],
        'assembly_focused': [0.2, 0.2, 0.2, 0.5, 0.3],
        'fragment_elimination': [0.5, 0.2, 0.2, 0.2, 0.4]
    }
    
    def __init__(self):
        """
        Initialize the parser with comprehensive pattern definitions
        These patterns have been refined through extensive testing
        """
        
        # EXPANDED hero moment indicators - comprehensive coverage
        # Each category serves a specific purpose in video generation
        self.hero_patterns = {
            'distinctive_techniques': [
                # Pastry work - crucial for baked goods
                'puff pastry', 'phyllo', 'filo', 'shortcrust', 'choux', 'croissant',
                'lattice', 'crimp', 'fold', 'roll out', 'blind bake', 'dock',
                'egg wash', 'brush with egg', 'beaten egg', 'egg yolk',
                'pastry over', 'over the top', 'pie dish', 'rim', 'edges', 
                
                # Fire techniques - dramatic visual moments
                'flambé', 'flame', 'ignite', 'torch', 'char', 'blacken', 'scorch',
                
                # Browning/coloring - key visual transformations
                'caramelize', 'brûlée', 'golden brown', 'golden-brown', 'bronzed',
                'glazed', 'lacquered', 'burnished', 'toasted', 'charred',
                
                # Assembly/decoration - the artistry moments
                'layer', 'stack', 'assemble', 'decorate', 'garnish', 'plate',
                'pipe', 'swirl', 'drizzle', 'dust', 'sprinkle', 'arrange',
                
                # Specialized cooking - advanced techniques
                'sous vide', 'confit', 'cure', 'smoke', 'pickle', 'ferment',
                'deglaze', 'emulsify', 'clarify', 'temper', 'bloom', 'proof'
            ],
            
            'visual_transformations': [
                # Basic visual actions - foundation movements
                'brush', 'lay', 'place', 'cover', 'spread', 'coat', 'dip',
                'fill', 'fold', 'seal', 'press', 'shape',
                
                # Rising/expanding - time-lapse worthy
                'rise', 'rising', 'puff up', 'puff', 'double in size', 'expand',
                'inflate', 'balloon', 'grow', 'swell', 'proof', 'ferment',
                
                # Melting/liquifying - state changes
                'melt', 'melting', 'liquify', 'dissolve', 'liquefy', 'render',
                
                # Bubbling/boiling - movement and energy
                'bubble', 'bubbling', 'simmer', 'boil', 'rolling boil', 'foam',
                'froth', 'effervesce', 'percolate',
                
                # Texture changes - the transformation magic
                'crisp', 'crispy', 'crunchy', 'firm up', 'gel', 'thicken',
                'reduce', 'concentrate', 'crystallize', 'solidify', 'coagulate',
                'reduced by half', 'volume of liquid', 'reduce until',
                
                # Color changes - visual drama
                'brown', 'golden', 'amber', 'mahogany', 'bronze', 'darken',
                'lighten', 'redden', 'turn golden', 'color develops',
                'browned on each side', 'until golden', 'golden-brown',
                
                # Time-based visual cues - process indicators
                'until golden', 'until browned', 'until crispy', 'until bubbling',
                'until reduced', 'until thickened', 'until set', 'until firm',
                
                # Finishing touches - the glamour shots
                'glaze', 'shine', 'gloss', 'sheen', 'lustrous', 'mirror-like'
            ],
            
            'signature_actions': [
                # Core cooking actions - the fundamentals
                'fry', 'sear', 'sauté', 'cook', 'heat', 'warm', 'transfer',

                # Wrapping/encasing - structural changes
                'stuff', 'wrap', 'encase', 'enrobe', 'coat', 'dredge', 'bread',
                'batter', 'crust', 'seal', 'fold over', 'tuck', 'roll up',
                
                # Liquid applications - saucing and coating
                'baste', 'brush with', 'drizzle over', 'pour over', 'ladle',
                'spoon over', 'cascade', 'ribbon', 'stream', 'flood',
                
                # Cutting/shaping - precision work
                'julienne', 'brunoise', 'chiffonade', 'dice', 'mince', 'shave',
                'ribbon', 'mandoline', 'tournée', 'score', 'butterfly',
                
                # Final touches - the finishing flourishes
                'torch', 'broil', 'gratinate', 'finish under', 'crown with',
                'top with', 'scatter over', 'nestle', 'cascade', 'fan out'
            ],
            
            'dramatic_moments': [
                # Temperature contrasts - shock value
                'shock in ice', 'plunge into', 'flash freeze', 'blast chill',
                'sear over high', 'quick fry', 'flash in pan',
                
                # Dramatic techniques - showstoppers
                'tableside', 'en papillote', 'salt crust', 'hay smoking',
                'cedar plank', 'banana leaf', 'parchment paper', 'foil packet',
                
                # Molecular/modern - cutting edge
                'spherification', 'gelification', 'foam', 'espuma', 'dust',
                'crisp', 'glass', 'chip', 'powder', 'snow',
                
                # Traditional spectacular - time-honored drama
                'whole roasted', 'spit roast', 'tandoor', 'wood-fired',
                'coal roasted', 'salt baked', 'clay baked', 'pit cooked'
            ]
        }
        
        # Dish-type specific priorities - what matters most for each dish
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
            'pie': ['lay the pastry', 'over the top', 'cover with pastry', 'place the pastry', 'drape', 'top with pastry'],
            'stew': ['ladle', 'thick and', 'rich sauce', 'tender meat'],
            'roast': ['carve', 'rest', 'crackling', 'juices run'],
            'baked': ['rise', 'golden top', 'spring back', 'dome'],
            'fried': ['flip', 'both sides', 'float', 'golden and crispy'],
            'grilled': ['grill marks', 'char lines', 'flame', 'sear marks'],
            'stir-fry': ['toss', 'wok hei', 'high heat', 'constantly moving'],
            'steamed': ['steam rises', 'tender', 'translucent', 'moist']
        }

        # Filler phrases to skip - the non-visual boring stuff
        self.skip_phrases = [
            'preheat', 'set aside', 'remove from heat', 'let rest', 'let cool',
            'set timer', 'prepare ingredients', 'wash', 'pat dry', 'room temperature',
            'meanwhile', 'in the meantime', 'while waiting', 'clean', 'reserve',
            'keep warm', 'transfer to plate', 'repeat process', 'continue',
            'occasionally', 'if needed', 'taste for seasoning', 'adjust seasoning',
            'gather ingredients', 'read through', 'have ready', 'to serve', 'serve',
            'refrigerate until', 'chill until', 'freeze until', 'cool completely',
            'bring to room temperature', 'let stand', 'allow to rest',
            'stir occasionally', 'stir frequently', 'check frequently',
            'line with parchment', 'grease the pan', 'spray with cooking spray',
            'season to taste', 'salt to taste', 'add salt and pepper',
            'discard', 'strain and discard', 'remove and discard',
            'cover with plastic wrap', 'cover with foil', 'cover tightly',
            'see notes', 'see tip', 'optional', 'if desired',
            'for serving', 'for garnish', 'to finish'
        ]
        
        # Cooking stages for narrative flow - the story arc
        self.cooking_stages = {
            'preparation': ['chop', 'dice', 'slice', 'mince', 'prepare', 'season', 'marinate', 'mix', 'combine', 'toss'],
            'initial_cooking': ['heat', 'sear', 'brown', 'fry', 'sauté', 'cook', 'simmer'],
            'transformation': ['reduce', 'thicken', 'caramelize', 'melt', 'dissolve', 'bubble', 'add the wine'],
            'assembly': ['transfer', 'layer', 'stack', 'fill', 'stuff', 'wrap', 'cover', 'lay', 'place', 'arrange', 'brush the rim'],
            'finishing': ['glaze', 'brush', 'garnish', 'crimp', 'seal', 'score', 'dust', 'drizzle', 'trim'],
            'final_cooking': ['bake', 'roast', 'grill', 'broil', 'golden', 'crispy', 'done', 'golden-brown', 'place in the oven']
        }
        
        # Narrative connections - what actions logically follow others
        self.narrative_connections = {
            'preparation': ['initial_cooking', 'assembly'],
            'initial_cooking': ['transformation', 'assembly'],
            'transformation': ['assembly', 'finishing'],
            'assembly': ['finishing', 'final_cooking'],
            'finishing': ['final_cooking'],
            'final_cooking': []
        }

    def extract_hero_moments(self, recipe: Dict) -> List[str]:
        """
        Extract 3-4 hero moments from a recipe with narrative flow
        Returns a story, not just moments
        
        Args:
            recipe: Dictionary containing recipe steps and metadata
            
        Returns:
            List of 3-4 moment descriptions for video generation
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
        
        # Extract all possible moments with their metadata
        all_moments = self._extract_all_moments_with_metadata(recipe.get('steps', []), dish_type)
        
        # Build narrative sequence using fuzzy logic
        narrative_moments = self._build_narrative_sequence(all_moments, dish_type, recipe.get('steps', []))
        
        return narrative_moments[:4]
    
    def _extract_all_moments_with_metadata(self, steps: List[Dict], dish_type: str) -> List[Dict]:
        """
        Extract all moments with step number, stage, and priority
        This is where we find ALL potential moments before scoring
        """
        all_moments = []
        
        for step in steps:
            step_num = step.get('step', 0)
            instruction = step.get('instruction', '')

            # DEBUG: See what patterns we find in key steps
            if step_num in [4, 6, 11]:  # Key steps we care about
                print(f"   📌 Step {step_num} patterns check: {instruction[:60]}...")

            # Skip pure filler steps
            if self._is_pure_filler(instruction):
                continue

            # DEBUG: See what's being processed
            print(f"🔍 Processing step {step_num}: {instruction[:50]}...")
            
            # Extract ALL patterns from this instruction
            moments_in_step = self._extract_all_patterns_from_instruction(instruction, dish_type, step_num)
            
            for moment in moments_in_step:
                stage = self._determine_cooking_stage(moment['text'])
                is_hero = self._is_hero_shot(moment['text'], dish_type)
                is_priority = self._is_priority_moment(moment['text'], dish_type)
                
                all_moments.append({
                    'text': moment['text'],
                    'step': step_num,
                    'stage': stage,
                    'is_hero': is_hero,
                    'is_priority': is_priority,
                    'pattern': moment['pattern'],
                    'pattern_type': moment.get('pattern_type', 'unknown')  # Essential for fuzzy scoring
                })
        
        return all_moments
    
    def _is_pure_filler(self, instruction: str) -> bool:
        """Check if entire instruction is just filler - no visual value"""
        instruction_lower = instruction.lower()
        filler_only = ['preheat the oven', 'set aside to cool', 'let rest', 'remove from the oven']
        return any(filler in instruction_lower for filler in filler_only)
    
    def _extract_all_patterns_from_instruction(self, instruction: str, dish_type: str, step_num: int) -> List[Dict]:
        """
        Extract ALL patterns from a single instruction
        Uses smart splitting to handle compound sentences
        """
        found_moments = []
        instruction_lower = instruction.lower()
        
        # DEBUG: See what patterns we find
        if step_num in [4, 6, 11]:  # Key steps we care about
            print(f"   📌 Step {step_num} patterns check: {instruction[:60]}...")

        # Split instruction into segments for compound sentences
        segments = self._smart_split_instruction(instruction)

        # DEBUG: See what segments were created
        if step_num in [4, 6, 11]:
            print(f"      Segments: {segments}")
        
        for segment in segments:
            segment_lower = segment.lower()
            
            # DEBUG: Track segment processing
            if step_num in [4, 6] and len(segment.split()) >= 3:
                print(f"         Checking segment: '{segment}'")

            # Skip if it's a serving instruction
            if any(serve_word in segment_lower for serve_word in ['to serve', 'serve', 'plate', 'alongside']):
                continue
                
            # Check all pattern categories - PRIORITIZE signature_actions for cooking steps
            found_in_segment = False
            pattern_order = ['signature_actions', 'visual_transformations', 'distinctive_techniques', 'dramatic_moments']

            for pattern_type in pattern_order:
                if pattern_type not in self.hero_patterns:
                    continue
                    
                patterns = self.hero_patterns[pattern_type]
                
                # Debug which pattern category we're checking
                if step_num in [4, 6] and pattern_type in ['signature_actions', 'visual_transformations']:
                    print(f"            🔍 Checking {pattern_type}: {patterns[:5]}...")

                for pattern in patterns:
                    if pattern in segment_lower:
                        print(f"            ✅ FOUND: pattern '{pattern}' in '{segment}'")
                        found_moments.append({
                            'text': segment.strip(),
                            'pattern': pattern,
                            'pattern_type': pattern_type
                        })
                        found_in_segment = True
                        break  # Break inner pattern loop only
                
                if found_in_segment:
                    break  # Break pattern_type loop only after finding one pattern per segment

        # Special handling for hero shots in compound sentences
        for pattern in self.hero_shots.get(dish_type, []):
            if pattern in instruction_lower:
                # Extract the specific part containing the hero shot
                hero_segment = self._extract_hero_segment(instruction, pattern)
                if hero_segment and not any(m['text'] == hero_segment for m in found_moments):
                    found_moments.append({
                        'text': hero_segment,
                        'pattern': pattern,
                        'pattern_type': 'hero_shot'
                    })
        
        return found_moments
    
    def _smart_split_instruction(self, instruction: str) -> List[str]:
        """
        Split instruction intelligently to handle compound sentences
        Preserves important phrases that shouldn't be split
        """
        # Prevent fragmenting important phrases before splitting
        # - "or until" often part of cooking duration (e.g., "cook for 20 min, or until golden")
        # - "then place" is a complete action
        # - "and lay" is a key pastry instruction
        instruction = instruction.replace(', or until', ' or until')
        instruction = instruction.replace(', then place', ' then place')
        segments = re.split(r'[,;.]|\bthen\b|\band\b(?! lay)', instruction)
        
        # Clean and filter segments
        cleaned_segments = []
        for segment in segments:
            cleaned = segment.strip()
            if cleaned and len(cleaned.split()) >= 3:  # At least 3 words
                cleaned_segments.append(cleaned)
        
        return cleaned_segments
    
    def _extract_hero_segment(self, instruction: str, pattern: str) -> str:
        """
        Extract the specific segment containing a hero pattern
        Extends intelligently to capture complete action
        """
        # Find the pattern location
        pattern_lower = pattern.lower()
        instruction_lower = instruction.lower()
        
        if pattern_lower not in instruction_lower:
            return ""
        
        # Extract a meaningful chunk around the pattern
        pos = instruction_lower.find(pattern_lower)
        
        # Look for natural boundaries
        start = pos
        end = pos + len(pattern)
        
        # Extend to include the complete action
        words_before = instruction_lower[:pos].split()
        words_after = instruction_lower[end:].split()
        
        # Include 2-3 words before if they're relevant verbs
        if len(words_before) >= 2:
            verb_words = ['lay', 'place', 'put', 'drape', 'cover', 'brush', 'roll']
            for i in range(min(3, len(words_before))):
                if words_before[-(i+1)] in verb_words:
                    start = instruction_lower.rfind(words_before[-(i+1)], 0, pos)
                    break
        
        # Include words after to complete the phrase
        if words_after:
            end_words = min(4, len(words_after))
            end = instruction.find(' ', end)
            for _ in range(end_words - 1):
                next_space = instruction.find(' ', end + 1)
                if next_space > 0:
                    end = next_space
                else:
                    break
        
        result = instruction[start:end].strip()
        
        # Capitalize first letter if needed
        if result and result[0].islower():
            result = result[0].upper() + result[1:]
            
        return result
    
    def _determine_cooking_stage(self, moment: str) -> str:
        """
        Determine which cooking stage this moment belongs to
        Used for narrative flow but not for selection
        """
        moment_lower = moment.lower()
        
        for stage, keywords in self.cooking_stages.items():
            for keyword in keywords:
                if keyword in moment_lower:
                    return stage
        
        return 'general'
    
    def _build_narrative_sequence(self, all_moments: List[Dict], dish_type: str, all_steps: List[Dict]) -> List[str]:
        """
        Select best 4 moments using fuzzy tree logic scoring
        This is the heart of the selection algorithm
        """
        # Sort by step number for temporal ordering
        all_moments.sort(key=lambda x: x['step'])
        
        # Score each moment using fuzzy tree logic
        scored_moments = []
        for moment in all_moments:
            score = self._fuzzy_score_moment(moment, dish_type)
            if score > self.FUZZY_WEIGHTS['minimum_threshold']:
                scored_moments.append({
                    'moment': moment,
                    'score': score
                })
        
        # Sort by score (highest first), then by step number for ties
        scored_moments.sort(key=lambda x: (-x['score'], x['moment']['step']))
        
        # Take top 4 moments
        final_moments = [sm['moment'] for sm in scored_moments[:4]]
        
        # Re-sort by step order for temporal flow in final video
        final_moments.sort(key=lambda x: x['step'])
        
        # DEBUG: Show what was selected
        print(f"🎯 WISE PARSER: Extracted {len(final_moments)} moments")

        return [m['text'] for m in final_moments]

    def _fuzzy_score_moment(self, moment: Dict, dish_type: str) -> float:
        """
        Score a moment using fuzzy tree logic (0.0 to 1.0)
        This implements multi-dimensional decision making
        """
        text_lower = moment['text'].lower()
        word_count = len(moment['text'].split())
        
        # Tree branch 1: Fragment detection - eliminate incomplete thoughts
        fragment_score = self._fuzzy_fragment_check(text_lower, word_count, moment)
        if fragment_score < 0.1:  # Hard reject fragments
            return 0.0
        
        # Tree branch 2: Reduction pattern detection - boost dramatic transformations
        reduction_score = self._fuzzy_reduction_check(text_lower)
        
        # Tree branch 3: Completion shot detection - find the glory moments
        completion_score = self._fuzzy_completion_check(text_lower, dish_type)
        
        # Tree branch 4: Standard scoring (base logic)
        base_score = 0.0
        
        # Completeness contribution (adjusted by fragment check)
        base_score += fragment_score * self.FUZZY_WEIGHTS['completeness']
        
        # Cooking action score
        cooking_verbs = ['fry', 'cook', 'sear', 'brown', 'reduce', 'simmer', 'boil']
        if any(verb in text_lower for verb in cooking_verbs):
            base_score += self.FUZZY_WEIGHTS['cooking_action']
        
        # Visual impact score (boosted by reduction check)
        visual_words = ['golden', 'bubble', 'sizzle', 'melt', 'crispy', 'until']
        if any(word in text_lower for word in visual_words):
            # Apply reduction boost if applicable
            visual_boost = 1.0 + (reduction_score * 0.5)
            base_score += self.FUZZY_WEIGHTS['visual_impact'] * visual_boost
        
        # Assembly importance (for dish-specific moments)
        if dish_type == 'pie':
            pie_words = ['pastry', 'brush', 'egg', 'lay', 'crimp', 'dish']
            if any(word in text_lower for word in pie_words):
                base_score += self.FUZZY_WEIGHTS['assembly_bonus']
        
        # Completion bonus for final glory shots
        base_score += completion_score * self.FUZZY_WEIGHTS['visual_impact']
        
        # Key moments bonus - specific high-value patterns
        if 'fry until browned' in text_lower:
            base_score += self.FUZZY_WEIGHTS['visual_impact']
        if 'cook until' in text_lower and 'reduced' in text_lower:
            base_score += self.FUZZY_WEIGHTS['visual_impact'] * 1.5  # Extra boost for reduction
        if 'lay the pastry' in text_lower:
            base_score += self.FUZZY_WEIGHTS['visual_impact']
        
        return min(base_score, 1.0)  # Cap at 1.0

    def _fuzzy_fragment_check(self, text_lower: str, word_count: int, moment: Dict) -> float:
        """
        Fuzzy tree branch for fragment detection - The Grammar Guardian
        
        This method acts as a quality gate, filtering out incomplete sentences and fragments
        that would produce poor video moments. It uses multi-dimensional analysis inspired
        by 1980s fuzzy logic principles to score text completeness.
        
        The scoring philosophy:
        - Complete cooking actions starting with verbs score highest (1.0)
        - Fragments, HTML remnants, and metadata score lowest (0.0)
        - Edge cases get middle scores, letting other factors decide
        
        Detection strategy (multi-layered like a circuit board):
        Layer 1: HTML/markup detection - immediate rejection
        Layer 2: Metadata patterns - recipe structure, not content
        Layer 3: First word analysis - verbs good, prepositions bad
        Layer 4: Word count scoring - longer generally better
        Layer 5: Combined fuzzy scoring - multiple factors weighted
        
        Args:
            text_lower: Lowercase version of the moment text
            word_count: Number of words in the moment
            moment: Full moment dictionary with original text
            
        Returns:
            float: Confidence score (0.0 to 1.0) that this is a complete, 
                video-worthy moment. Think of it as a "completeness voltage"
                where 1.0 is full signal and 0.0 is no signal.
        
        Examples of scoring:
            "Fry until golden brown" -> 0.7 (starts with verb, 4 words)
            "Heat oil in large pan" -> 0.7 (starts with verb, 5 words)
            "</li><li>Brown the beef" -> 0.0 (HTML fragment)
            "enough of the beef" -> 0.0 (fragment, starts badly)
            "Recipe one: Pour rice" -> 0.1 (metadata pattern)
            "Reduce liquid by half until thick" -> 1.0 (verb, 6+ words)
        
        Technical note:
            This implements a fuzzy decision tree where multiple weak signals
            combine to create strong confidence, similar to how op-amps sum
            multiple input voltages. Each factor contributes to the final score.
        """
        import re
        
        # Get the original text for analysis
        original_text = moment['text'].strip()
        
        # Hard reject if starts with HTML tags
        if original_text.startswith('<') or original_text.startswith('</'):
            return 0.0  # Definitely a fragment if starts with HTML
        
        # Clean any HTML remnants and special characters for first word detection
        clean_text = re.sub(r'<[^>]+>', '', original_text)  # Remove HTML tags
        clean_text = re.sub(r'^[^a-zA-Z]+', '', clean_text)  # Remove non-letters at start
        clean_text = clean_text.strip()
        
        # If nothing left after cleaning, it's a fragment
        if not clean_text:
            return 0.0
        
        # Get first word from cleaned text
        first_word = clean_text.split()[0].lower() if clean_text.split() else ''
        
        # Expanded list of strong action verbs that indicate complete moments
        starts_with_verb = first_word in [
            'fry', 'cook', 'heat', 'transfer', 'brush', 'trim', 'place', 'add', 
            'pour', 'mix', 'bake', 'boil', 'simmer', 'sauté', 'sear', 'brown',
            'reduce', 'stir', 'whisk', 'fold', 'beat', 'blend', 'chop', 'dice',
            'slice', 'drain', 'rinse', 'season', 'sprinkle', 'garnish', 'serve',
            'roll', 'wrap', 'cover', 'uncover', 'flip', 'turn', 'remove', 'set',
            'preheat', 'grease', 'line', 'arrange', 'layer', 'spread', 'coat',
            'dredge', 'toss', 'combine', 'melt', 'dissolve', 'chill', 'freeze',
            'refrigerate', 'marinate', 'rest', 'cool', 'warm', 'toast', 'broil',
            'grill', 'roast', 'steam', 'blanch', 'temper', 'strain', 'filter',
            'skim', 'deglaze', 'flambé', 'caramelize', 'crystallize', 'proof',
            'knead', 'punch', 'shape', 'score', 'crimp', 'seal', 'brush', 'egg',
            'glaze', 'dust', 'pipe', 'drizzle', 'ladle', 'spoon', 'scatter',
            'nestle', 'fan', 'torch', 'broil', 'gratinate', 'finish', 'top',
            'crown', 'stuff', 'fill', 'hollow', 'core', 'peel', 'zest', 'juice',
            'squeeze', 'press', 'crush', 'grind', 'pound', 'tenderize', 'butterfly',
            'score', 'slash', 'dock', 'prick', 'vent'
        ]
        
        # Expanded list of fragment indicators
        starts_badly = first_word in [
            'enough', 'of', 'the', 'and', 'or', 'with', 'until', 'for', 'to', 
            'in', 'on', 'at', 'by', 'from', 'into', 'onto', 'over', 'under',
            'through', 'about', 'around', 'between', 'during', 'without', 'within',
            'along', 'after', 'before', 'behind', 'below', 'beneath', 'beside',
            'besides', 'but', 'however', 'although', 'though', 'if', 'unless',
            'because', 'since', 'so', 'then', 'just', 'only', 'even', 'still',
            'already', 'also', 'too', 'very', 'quite', 'rather', 'somewhat',
            'recipe', 'step', 'note', 'tip', 'optional', 'alternatively'
        ]
        
        # Check for recipe metadata that shouldn't be extracted
        metadata_patterns = [
            'recipe one:', 'recipe two:', 'recipe 1:', 'recipe 2:',
            'method:', 'instructions:', 'directions:', 'procedure:',
            'ingredients:', 'you will need:', 'equipment:', 'notes:',
            'tip:', 'variation:', 'serving suggestion:', 'to serve:'
        ]
        
        if any(pattern in text_lower for pattern in metadata_patterns):
            return 0.1  # Very low score for metadata
        
        # Multi-factor scoring with refined thresholds
        if word_count >= 8 and starts_with_verb:
            return 1.0  # Definitely complete
        elif word_count >= 8 and not starts_badly:
            return 0.8  # Probably complete
        elif word_count >= 6 and starts_with_verb:
            return 0.8  # Good complete action
        elif word_count >= 5 and starts_with_verb:
            return 0.7  # Likely complete
        elif word_count >= 5 and not starts_badly:
            return 0.5  # Possibly complete
        elif word_count >= 4 and starts_with_verb:
            return 0.5  # Minimal but might be acceptable
        elif word_count >= 3 and starts_with_verb:
            return 0.4  # Very minimal but could work
        elif starts_badly or word_count < 3:
            return 0.0  # Definitely a fragment
        else:
            return 0.3  # Edge case - let other scoring factors decide


    def _fuzzy_reduction_check(self, text_lower: str) -> float:
        """
        Fuzzy tree branch for reduction pattern scoring
        Identifies and boosts dramatic liquid transformations
        """
        reduction_score = 0.0
        
        # Primary reduction indicators
        if 'reduce' in text_lower:
            reduction_score += 0.3
            if 'by half' in text_lower or 'reduced by half' in text_lower:
                reduction_score += 0.4  # Very specific and visual
            if 'volume' in text_lower or 'liquid' in text_lower:
                reduction_score += 0.3  # Clear visual transformation
        
        # Secondary reduction indicators
        if 'until' in text_lower and ('thick' in text_lower or 'syrup' in text_lower):
            reduction_score += 0.2
        
        # Cooking down indicators
        if 'cook down' in text_lower or 'simmer until' in text_lower:
            reduction_score += 0.2
            
        return min(reduction_score, 1.0)

    def _fuzzy_completion_check(self, text_lower: str, dish_type: str) -> float:
        """
        Fuzzy tree branch for final glory shot detection
        Identifies the money shot - the finished product
        """
        completion_score = 0.0
        
        # Universal completion indicators
        if 'golden-brown' in text_lower or 'golden brown' in text_lower:
            completion_score += 0.3
            if 'oven' in text_lower or 'bake' in text_lower:
                completion_score += 0.4  # Classic finish
        
        # "Until done" patterns
        if 'until' in text_lower:
            if 'cooked through' in text_lower or 'done' in text_lower:
                completion_score += 0.3
            if 'golden' in text_lower or 'crispy' in text_lower:
                completion_score += 0.2
        
        # Dish-specific completion
        if dish_type == 'pie':
            if 'crimp' in text_lower or 'edges' in text_lower:
                completion_score += 0.2  # Final assembly
            if 'place in the oven' in text_lower or 'bake for' in text_lower:
                completion_score += 0.3  # Going in for final cook
        elif dish_type == 'roast':
            if 'rest' in text_lower or 'carve' in text_lower:
                completion_score += 0.4  # Classic roast finish
                
        return min(completion_score, 1.0)
    
    def _is_priority_moment(self, moment: str, dish_type: str) -> bool:
        """
        Check if moment contains priority patterns for dish type
        Quick boolean check for high-value moments
        """
        if dish_type not in self.dish_priorities:
            return False
        
        moment_lower = moment.lower()
        priority_patterns = self.dish_priorities.get(dish_type, [])
        
        for pattern in priority_patterns:
            if pattern in moment_lower:
                return True
        return False

    def _is_hero_shot(self, moment: str, dish_type: str) -> bool:
        """
        Check if this is THE defining moment for the dish
        The "poster frame" moment
        """
        if dish_type not in self.hero_shots:
            return False
            
        moment_lower = moment.lower()
        hero_patterns = self.hero_shots.get(dish_type, [])
        
        for pattern in hero_patterns:
            if pattern in moment_lower:
                return True
        return False
    
    def build_recipe_aware_prompt(self, base_prompt: str, hero_moments: List[str]) -> str:
        """
        Integrate hero moments into existing prompt with narrative flow
        This is the final output that guides video generation
        """
        if not hero_moments:
            return base_prompt
            
        # Build a narrative sequence description
        narrative_sequence = self._create_narrative_description(hero_moments)
        
        # Find and replace the cooking sequence
        if "COMPLETE COOKING SEQUENCE:" in base_prompt:
            sequence = "COMPLETE COOKING SEQUENCE: " + narrative_sequence
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
        
        return base_prompt
    
    def _create_narrative_description(self, moments: List[str]) -> str:
        """
        Create a flowing narrative from moments
        Joins them in a way that reads naturally
        """
        if not moments:
            return ""
    
        # Extract text from moment dictionaries if needed
        if moments and isinstance(moments[0], dict):
            moment_texts = [m.get('text', '') for m in moments]
            return ". ".join(moment_texts)
    
        # Simply join with periods for clarity
        return ". ".join(moments)

# Global instance - ready to parse!
wise_parser = WiseRecipeParser()
