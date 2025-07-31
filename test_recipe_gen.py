import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Test ingredients
ingredients = ["Salmon", "Soy Sauce", "Chili Peppers", "Scallions"]
cuisine = "Indonesian"
dish_type = "pasta"

print(f"Testing recipe generation for {cuisine} {dish_type}...")
print(f"OpenAI Key: {openai.api_key[:20]}...")

try:
    prompt = f"Create a {cuisine} {dish_type} recipe using: {', '.join(ingredients)}"
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional chef."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    
    recipe_text = response.choices[0].message.content.strip()
    print("\nSUCCESS! Recipe generated:")
    print(recipe_text[:200] + "...")
    
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {str(e)}")
    