# /*
# * RecipeGen™ - AI-Powered Culinary Video & Recipe Generation Platform
# * © Copyright By Abraham Chachamovits
# * RecipeGen™ is a trademark of Abraham Chachamovits
# * 
# * File: main.py
# */

"""
RecipeGen Backend API
Main Flask application for recipe generation, video creation, and chat functionality
"""

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
from database import db
from async_worker import worker
import json
import os
import openai
import sys
import requests
import logging
import uuid
import sqlite3
from recipe_matcher_4d import recipe_matcher_4d
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
# On app startup, regenerate supported cuisines
from update_supported_cuisines import update_supported_cuisines
update_supported_cuisines()

# No need to import sys again
sys.path.append(str(Path(__file__).parent))
from music_config import music_db

def initialize_music_database():
    """Initialize and sync music database on startup"""
    # Sync with ingredients.json
    ingredients_path = Path(__file__).parent / "data" / "ingredients.json"  # ← Add "data"
    if ingredients_path.exists():
        new_cuisines = music_db.sync_with_ingredients(ingredients_path)
        if new_cuisines:
            print(f"🎵 Music database updated with new cuisines!")
    
    print(f"🎵 Music database loaded with {len(music_db.music_data)} cuisines")

# Call it right here, before any routes
initialize_music_database()

# Initialize database schema
with sqlite3.connect('recipegen.db') as conn:
    try:
        conn.execute('ALTER TABLE recipes ADD COLUMN matched_recipe_data TEXT')
        print("✅ Added matched_recipe_data column")
    except sqlite3.OperationalError:
        pass  # Column exists

# === Configuration and Setup ===
print("✅ ✅ ✅ THIS IS THE REAL main.py FROM videos FOLDER")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ✅ LEGACY IMPORT VALIDATION
assert openai.__version__.startswith("0.28"), f"WRONG openai VERSION LOADED: {openai.__version__}"

print("✅ main.py loaded and running")

# === Dual-path ENV Loader ===
abs_path = "D:\\RecipeGen\\Tehomia-chatgpt-diagnostics-remix\\.env"
if os.path.exists(abs_path):
    load_dotenv(dotenv_path=abs_path)
    print("✅ Loaded .env from ABSOLUTE path (development)")
elif os.path.exists(".env"):
    load_dotenv()
    print("✅ Loaded .env from RELATIVE path (production-ready)")
else:
    print("❌ No .env file found — check pathing before deployment.")

print("✅ Loaded API KEY (active load):", os.getenv("OPENAI_API_KEY"))

# 🔽 ENVIRONMENT DIAGNOSTICS
print("⚙️ ENVIRONMENT DIAGNOSTIC")
print(f"Python Executable : {sys.executable}")
print(f"Python Version    : {sys.version}")
print(f"OpenAI Version    : {openai.__version__}")
print(f"OpenAI Path       : {openai.__file__}")
print(f"ENV Variable OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")

# === Load Data ===
with open('data/recipes.json') as f:
    recipes = json.load(f)

with open('data/history.json') as f:
    history = json.load(f)

with open("data/ingredients.json", encoding="utf-8") as f:
    INGREDIENTS_LIST = json.load(f)
    INGREDIENTS_BY_SLUG = {item["slug"]: item for item in INGREDIENTS_LIST}

# === Assign Keys ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# Security: Move to environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password123')

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
CORS(app)

# ✅ Blueprint registration
from video_routes import video_bp
app.register_blueprint(video_bp)

# === Utility: Strict RecipeGen Chat Guardrail ===
def is_recipegen_related(message):
    allowed_keywords = [
        "recipe", "cook", "cooking", "bake", "baking", "ingredients", "ingredient",
        "dish", "meal", "prepare", "make", "food", "kitchen", "generate", "select",
        "category", "history", "video", "image", "site", "login", "account", "chat", "how to use"
    ]
    msg = message.lower()
    return any(kw in msg for kw in allowed_keywords)

def is_food_related(text):
    food_words = [
        "cook", "boil", "bake", "roast", "grill", "simmer", "chill", "refrigerate",
        "saute", "steam", "blend", "prep", "recipe", "dish", "ingredient", "oven",
        "microwave", "fry", "deep fry", "mince", "whisk", "dough", "batter", "rice", "meat"
    ]
    return any(word in text for word in food_words)

def is_geography_question(text):
    patterns = [
        "how long", "how far", "distance from", "distance to", "how many miles", "how many kilometers",
        "travel from", "travel to", "flight from", "flight to", "directions to"
    ]
    return any(p in text for p in patterns)

def validate_ingredients(ingredient_slugs, mode="jewish"):
    problems = []
    
    if mode != "jewish":
        return problems

    types_present = set()
    meat_names = []
    fish_names = []
    dairy_names = []
    has_non_kosher = False  # 🛡️ Guard flag

    for slug in ingredient_slugs:
        ing = INGREDIENTS_BY_SLUG.get(slug)
        if not ing:
            problems.append({"slug": slug, "error": "Unknown ingredient"})
            continue

        ing_type = ing.get("type")
        kashrut = ing.get("kashrut")

        # Check for non-kosher items (skip requires-supervision unless it's explicitly non-kosher)
        if kashrut == "non-kosher":
            has_non_kosher = True  # 🛡️ Set the guard flag
            problems.append({
            "slug": slug,
            "error": f"{ing['name']} is not permitted in Jewish cuisine."
        })

        # Track types for mixing validation
        if ing_type:
            types_present.add(ing_type)

            # Track kosher items for mixing rules
            if ing_type == "meats" and kashrut in ["kosher", "requires-supervision"]:
                meat_names.append(ing['name'])
            elif ing_type == "fish" and kashrut == "kosher":
                fish_names.append(ing['name'])
            elif ing_type in ["dairy", "milk product"]:
                dairy_names.append(ing['name'])

    # ❗ Don't apply mixing rules if a non-kosher item is present
    if not has_non_kosher:
        if meat_names and dairy_names:
            problems.append({
                "error": "Our Jewish cuisine follows kosher law, which prohibits the mixture of meat and dairy products."
            })
        # CHANGE THIS LINE: elif → if
        if meat_names and fish_names:
            problems.append({
                "error": "Our Jewish cuisine follows kosher law, which prohibits the mixture of meat and fish."
            })

    return problems


# === Routes ===

@app.route('/output/<filename>')
def serve_video(filename):
    return send_from_directory('output', filename)

@app.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = list({r['category'] for r in recipes})
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        return jsonify({'error': 'Failed to fetch categories'}), 500

@app.route('/recipes', methods=['GET'])
def get_recipes():
    try:
        category = request.args.get('category')
        if category:
            filtered = [r for r in recipes if r['category'].lower() == category.lower()]
            return jsonify(filtered)
        return jsonify(recipes)
    except Exception as e:
        logger.error(f"Error in get_recipes: {e}")
        return jsonify({'error': 'Failed to fetch recipes'}), 500

@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    for r in recipes:
        if r['id'] == recipe_id:
            return jsonify(r)
    return jsonify({'error': 'Recipe not found'}), 404

@app.route('/get_full_recipe/<recipe_id>')
def get_full_recipe(recipe_id):
    """Get the full recipe after payment"""
    try:
        print(f"🔓 UNLOCK RECIPE CALLED! Recipe ID: {recipe_id}")
        
        # Get the matched recipe ID from database
        with sqlite3.connect('recipegen.db') as conn:
            cursor = conn.execute(
                'SELECT matched_recipe_id, matched_recipe_data FROM recipes WHERE recipe_id = ?',
                (recipe_id,)
            )
            result = cursor.fetchone()
            
        if result:
            matched_recipe_id, matched_recipe_data = result
            
            # First try to get from stored matched_recipe_data (includes essential recipes)
            if matched_recipe_data:
                print(f"📍 Found recipe data in database")
                full_recipe = json.loads(matched_recipe_data)
                return jsonify({
                    "success": True,
                    "recipe": full_recipe
                })
            
            # Fallback to recipe_matcher_4d if no stored data
            elif matched_recipe_id:
                print(f"📍 Found matched recipe ID: {matched_recipe_id}")
                full_recipe = recipe_matcher_4d.get_recipe_by_id(matched_recipe_id)
                
                if full_recipe:
                    return jsonify({
                        "success": True,
                        "recipe": full_recipe
                    })
        
        return jsonify({
            "success": False,
            "error": "Recipe not found"
        })
    except Exception as e:
        print(f"❌ ERROR in get_full_recipe: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/check_video_status/<task_id>', methods=['GET'])
def check_video_status(task_id):
    """
    Check if background video is ready
    """
    try:
        # Query database for task status
        with sqlite3.connect('recipegen.db') as conn:
            cursor = conn.execute(
                'SELECT status, video_url, local_path FROM video_generation_tasks WHERE task_id = ?',
                (task_id,)
            )
            row = cursor.fetchone()
            
        if not row:
            return jsonify({"status": "not_found"}), 404
            
        status, video_url, local_path = row
        
        if status == 'completed':
            return jsonify({
                "status": "completed",
                "video_url": video_url,
                "local_path": local_path,
                "ready": True
            })
        elif status == 'failed':
            return jsonify({
                "status": "failed",
                "ready": False
            })
        else:
            return jsonify({
                "status": status,
                "ready": False
            })
            
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/add_ingredient', methods=['POST'])
def add_ingredient():
    """Add new ingredient and update music database if needed - FOR FUTURE EDITOR"""
    try:
        ingredient_data = request.get_json()
        
        # Load current ingredients
        with open("data/ingredients.json", "r", encoding="utf-8") as f:
            ingredients = json.load(f)
        
        # Add new ingredient
        ingredients.append(ingredient_data)
        
        # Save updated ingredients
        with open("data/ingredients.json", "w", encoding="utf-8") as f:
            json.dump(ingredients, f, indent=2, ensure_ascii=False)
        
        # Update music database if new cuisine
        if 'cuisine' in ingredient_data:
            cuisines = ingredient_data['cuisine']
            if isinstance(cuisines, str):
                cuisines = [cuisines]
            
            for cuisine in cuisines:
                if cuisine.lower() not in music_db.music_data:
                    music_db.add_cuisine(cuisine)
                    print(f"🎵 Added {cuisine} to music database")
        
        # Update the global INGREDIENTS_LIST and INGREDIENTS_BY_SLUG
        global INGREDIENTS_LIST, INGREDIENTS_BY_SLUG
        INGREDIENTS_LIST = ingredients
        INGREDIENTS_BY_SLUG = {item["slug"]: item for item in ingredients}
        
        return jsonify({"success": True, "message": "Ingredient added successfully"})
        
    except Exception as e:
        logger.error(f"Error adding ingredient: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_recipe_instant', methods=['POST'])
def generate_recipe_instant():
    """Generate instant teaser, queue EVERYTHING else"""
    try:
        data = request.get_json(force=True) or {}
        ingredients = data.get("ingredients", [])
        cuisine = data.get("cuisine", "")
        dish_type = data.get("dish_type", "")
        
        # CRITICAL: Check if this is an essential recipe request
        is_essential = data.get('is_essential', False)

        # Get ingredient names for teaser only
        ingredient_names = []
        for slug in ingredients:
            ing = INGREDIENTS_BY_SLUG.get(slug)
            if ing:
                ingredient_names.append(ing['name'])
        
        # Create IDs
        recipe_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        # If this is an essential recipe request, skip the 4D search!
        if is_essential:
            print("✨ Essential recipe requested - skipping 4D search")
            matched_recipe = None  # This will trigger essential recipe creation below
        else:
            # Normal 4D search
            chef_preference = data.get("chef_preference", "traditional")
            matched_recipe = recipe_matcher_4d.find_recipe(cuisine, ingredients, dish_type, chef_preference)

               
        # INTELLIGENT ALTERNATIVES SYSTEM
        # ================================
        # After building the complete 4D cascade logic, we discovered that many valid
        # user combinations (like Singaporean Baked Crab) simply don't exist in any
        # recipe database. Rather than silently falling back to generic recipes,
        # we now engage the user with intelligent alternatives.
        #
        # This transforms RecipeGen from a "dumb search" into a culinary advisor
        # that understands relationships between cuisines, cooking methods, and
        # ingredients. Like a skilled chef who says "We're out of salmon, but
        # I have beautiful sea bass that would work perfectly."
        #
        # The 4D system's journey through all levels provides rich context about
        # WHY a recipe wasn't found, enabling us to suggest smart alternatives.
        if isinstance(matched_recipe, dict) and matched_recipe.get('type') == 'no_match':
            print("🤔 No direct match found - preparing intelligent alternatives")
            
            # Store the failure context for potential future use
            with sqlite3.connect('recipegen.db') as conn:
                conn.execute('''
                    INSERT INTO recipes (recipe_id, cuisine_id, dish_type, ingredients, recipe_text, video_task_id, matched_recipe_id, matched_recipe_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (recipe_id, 0, dish_type, json.dumps(ingredients), "NO_MATCH", task_id, "alternatives", json.dumps(matched_recipe)))
            
            # Return alternatives to the frontend for user interaction
            # This is NOT admitting defeat - it's demonstrating culinary intelligence
            return jsonify({
                "success": False,
                "recipe_id": recipe_id,
                "no_match": True,
                "reason": matched_recipe['search_summary']['reason'],
                "alternatives": matched_recipe['alternatives'],
                "apis_checked": matched_recipe['search_summary']['apis_checked'],
                "original_request": {
                    "cuisine": cuisine.title(),
                    "dish_type": dish_type.replace('-', ' ').title(),
                    "ingredients": ingredient_names
                },
                "message": f"We searched extensively but couldn't find {cuisine.title()} {dish_type.replace('-', ' ')} "
                          f"with your selected ingredients. Here are some excellent alternatives we think you'll love:"
            })
        
        # If we have a real recipe match, continue as before
        matched_recipe_id = matched_recipe.get('recipe_id') if matched_recipe else None

        # FALLBACK PHILOSOPHY - The Essential Recipe
        # ==========================================
        # [Keep existing fallback comment and logic...]
        if not matched_recipe:
            # Create essential recipe - simple, honest, universal
            matched_recipe = {
                'recipe_id': f'essential-{recipe_id}',
                'title': f"{cuisine.title()} {dish_type.title() if dish_type else 'Dish'} with {', '.join(ingredient_names)}",
                'cuisine': cuisine,
                'dish_type': dish_type or 'general',
                'ingredients': [
                    {
                        'name': name,
                        'amount': '1 cup',
                        'slug': ingredients[i] if i < len(ingredients) else name.lower().replace(' ', '-')
                    }
                    for i, name in enumerate(ingredient_names)
                ],
                'steps': [
                    {'step': 1, 'instruction': f'Prepare all ingredients - wash and cut as needed'},
                    {'step': 2, 'instruction': f'Heat pan or wok with oil until hot'},
                    {'step': 3, 'instruction': f'Cook {ingredient_names[0] if ingredient_names else "main ingredient"} until done'},
                    {'step': 4, 'instruction': f'Add remaining ingredients and seasonings'},
                    {'step': 5, 'instruction': f'Cook together until everything is well combined'},
                    {'step': 6, 'instruction': f'Taste and adjust seasoning as needed'},
                    {'step': 7, 'instruction': f'Garnish and serve hot'}
                ],
                'source': 'RecipeGen Essential',
                'servings': 4,
                'prep_time': 15,
                'cook_time': 20
            }
            matched_recipe_id = matched_recipe['recipe_id']
        
        # [Rest of the function remains the same...]
        # Store placeholder recipe in database WITH matched recipe reference
        with sqlite3.connect('recipegen.db') as conn:
            conn.execute('''
                INSERT INTO recipes (recipe_id, cuisine_id, dish_type, ingredients, recipe_text, video_task_id, matched_recipe_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (recipe_id, 0, dish_type, json.dumps(ingredients), "GENERATING", task_id, matched_recipe_id))
            
            # Store matched recipe data in SAME transaction
            if matched_recipe:
                matched_recipe_json = json.dumps(matched_recipe)
                conn.execute(
                    'UPDATE recipes SET matched_recipe_data = ? WHERE recipe_id = ?',
                    (matched_recipe_json, recipe_id)
                )
                
        # Queue BOTH recipe generation AND video generation
        db.create_video_task(
            task_id=task_id,
            recipe_id=recipe_id,
            cuisine=cuisine or "international",
            ingredients=ingredient_names,
            dish_type=dish_type,
            prompt="pending",
            provider='kie'
        )
        
        # Return INSTANT teaser
        ingredient_list = ", ".join(ingredient_names[:3]) + "..." if len(ingredient_names) > 3 else ", ".join(ingredient_names)
        # Include actual recipe info if we have it
        recipe_title = matched_recipe.get('title', f"{cuisine.title()} {dish_type}")
        recipe_image = matched_recipe.get('image_url', '')

        return jsonify({
            "success": True,
            "recipe_id": recipe_id,
            "task_id": task_id,
            "teaser": f"Your delicious {cuisine.title()} {dish_type} with {ingredient_list} is being prepared!",
            "recipe_title": recipe_title,  # Add actual recipe title
            "recipe_image": recipe_image,    # Add recipe image if available
            "price": "$2.99"
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/recipes/<int:recipe_id>/generate', methods=['POST'])
def generate_recipe(recipe_id):
    for r in recipes:
        if r['id'] == recipe_id:
            try:
                entry = {
                    'recipe_id': recipe_id, 
                    'title': r['title'],
                    'timestamp': datetime.now().isoformat()  # Proper timestamp
                }
                history.append(entry)
                with open('data/history.json', 'w') as f:
                    json.dump(history, f, indent=2)
                return jsonify({'instructions': 'Step-by-step instructions will appear here.'})
            except Exception as e:
                logger.error(f"Error generating recipe: {e}")
                return jsonify({'error': 'Failed to generate recipe'}), 500
    return jsonify({'error': 'Recipe not found'}), 404

@app.route('/validate_ingredients', methods=['POST'])
def validate_ingredients_api():
    try:
        data = request.get_json(force=True)
        ingredient_slugs = data.get("ingredients", [])
        mode = data.get("mode", "jewish")
        problems = validate_ingredients(ingredient_slugs, mode=mode)
        return jsonify({"problems": problems, "count": len(problems)})
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": "Validation failed", "details": str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(history)

@app.route('/login', methods=['POST'])
def login():
    try:
        credentials = request.json
        if credentials.get('username') == ADMIN_USERNAME and credentials.get('password') == ADMIN_PASSWORD:
            session['user'] = credentials.get('username')
            return jsonify({'status': 'success'})
        return jsonify({'status': 'failure'}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route("/ingredients", methods=["GET"])
def get_ingredients():
    try:
        with open("data/ingredients.json", "r", encoding="utf-8") as f:
            ingredients = json.load(f)
        return jsonify(ingredients)
    except Exception as e:
        logger.error(f"Error loading ingredients: {e}")
        return jsonify({"error": "Unable to load ingredients", "details": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    print("🔵 /chat route hit")
    data = request.get_json(force=True)
    if not data or "message" not in data:
        print("🔴 No message found in payload.")
        return jsonify({'error': 'Invalid request'}), 400

    user_message = data["message"].strip()
    print("🟢 User message:", user_message)
    text = user_message.lower()

    # Keep ALL the nuanced filtering logic
    off_topic_patterns = [
        "president", "trump", "biden", "putin", "election", "politics",
        "soccer", "sex", "intimacy", "sensual", "football", "player", "news", "weather", "stock", "market",
        "company", "business", "music", "movie", "actor", "actress", "sport",
        "game", "science", "math", "state", "number", "capital", "country", "who is", "money",
        "celebrity", "politician", "government", "pandemic", "covid", "virus", "universe", "physics",
        "mount", "mountain", "everest", "how tall", "altitude", "height", "landmark", "show", "gossip",
        "mars", "venus", "jupiter", "planet", "space", "astronomy", "nasa", "moon", "solar system"
    ]

    if any(kw in text for kw in off_topic_patterns):
        return jsonify({
            "reply": (
                "I'm only able to answer questions about recipes, ingredients, cooking, or how to use RecipeGen. "
                "Please ask about food, ingredients, or this site."
            )
        })

    # Special handling for login questions
    if "login" in text or "log in" in text:
        return jsonify({
            'reply': (
                'To log in, click the "Login" link in the top‑right navbar, '
                'enter your username and password, then hit Submit.'
            )
        })

    # Special handling for admin/support questions
    admin_keywords = ["administrator", "admin", "support", "help", "contact", "account", "password"]
    if any(kw in text for kw in admin_keywords):
        return jsonify({
            'reply': (
                'For site‑administration or support issues, please use the "Contact" '
                'link in the top‑right navbar or email support@recipegen.io.'
            )
        })

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are RecipeGen."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )
        ai_reply = resp.choices[0].message.content.strip()
        print("🟣 AI reply:", ai_reply)
    except Exception as e:
        print("❌ OpenAI error:", e)
        logger.error(f"OpenAI API error: {e}")
        return jsonify({'error': 'Server error'}), 500

    return jsonify(reply=ai_reply)

# Remove the broken generate_video route - it's handled by video_bp

@app.route('/ui')
def serve_ui():
    return send_from_directory('static', 'index.html')

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

# === Error Handlers ===
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

worker.start()
logger.info("🎯 Async video worker started for background processing")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"🚀 Starting RecipeGen on port {port}")
    app.run(host="0.0.0.0", port=port)