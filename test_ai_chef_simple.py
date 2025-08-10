# test_ai_chef_simple.py
"""
Simple test to verify A.I. Chef works
"""

print("Starting A.I. Chef simple test...")

# First, test if we can load the API key directly
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
print(f"Direct API key load: {api_key[:20] if api_key else 'FAILED'}...")

# Now test the generator
from ai_chef_generator import AIChefGenerator

print("\nCreating A.I. Chef generator...")
chef = AIChefGenerator()

print("\nGenerating a simple recipe...")
recipe = chef.generate_recipe("mexican", "stir-fry", ["chicken", "peppers", "onions"])

print(f"\nResult: {recipe.get('title', 'FAILED TO GENERATE')}")
if recipe.get('title') != 'Simple Mexican Stir-Fry':
    print("SUCCESS! Got a real AI-generated recipe!")
    print("\nFull recipe:")
    print(f"Title: {recipe.get('title')}")
    print(f"Ingredients: {len(recipe.get('ingredients', []))} items")
    print(f"Instructions: {len(recipe.get('instructions', []))} steps")
else:
    print("FAILED - Still using fallback recipe")