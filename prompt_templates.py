"""
Prompt Templates for RecipeGen
Easy access for experimentation and tweaking
"""

def get_kie_prompt(cuisine, ingredients, dish_type):
    """KIE-optimized prompt template"""
    ingredient_list = ", ".join(ingredients)
    
    # Easy to modify template
    template = f"""
{cuisine.title()} chef in traditional kitchen preparing {dish_type} with {ingredient_list}.
COMPLETE COOKING SEQUENCE showing EVERY step:
- Show pasta cooking in pot until al dente
- Show each ingredient being added ONE BY ONE
- {ingredients[0]} prepared and added first
- Then {ingredients[1]} added next
- Follow with remaining ingredients
- Show final dish plating
Keep all ingredients VISIBLE throughout.
Traditional {cuisine} setting with proper cookware.
LOUD sizzling sounds, kitchen ambiance, traditional {cuisine} music.
"""
    return template.strip()

def get_fal_prompt(cuisine, ingredients, dish_type):
    """FAL standard prompt template"""
    # Different template for FAL
    pass

# Experiment with variations
def get_experimental_prompt_v1(cuisine, ingredients, dish_type):
    """Try to fix vanishing pasta problem"""
    # Your experimental version here
    pass