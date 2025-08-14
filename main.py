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
from flask import send_from_directory

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


import json
import uuid
from datetime import datetime
import os
import sys
from io import StringIO

def log_system_error(error_type, user_request, console_snapshot, resolution="unknown", additional_data=None):
    """
    Log system errors for Editor analysis with complete diagnostic information
    """
    # Generate unique error ID
    timestamp = datetime.now()
    error_id = f"ERR-{timestamp.strftime('%Y-%m%d-%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Capture system state
    error_event = {
        "error_id": error_id,
        "timestamp": timestamp.isoformat(),
        "error_type": error_type,
        "user_request": user_request,
        "console_output": console_snapshot,
        "resolution": resolution,
        "system_state": {
            "python_version": sys.version,
            "openai_version": openai.__version__,
            "database_recipes": get_database_recipe_count(),
            "environment": "development" if app.debug else "production"
        },
        "additional_data": additional_data or {}
    }
    
    # Save to error log file
    save_error_to_log(error_event)
    
    return error_event

def capture_console_output():
    """
    Capture recent console output for error context
    NOTE: This is a simplified version - in production we'd implement 
    a circular buffer to capture the last N lines
    """
    # For now, return a placeholder - we'll implement proper console capture later
    return "Console output capture to be implemented with circular buffer"

def save_error_to_log(error_event):
    """
    Save error event to JSON log file for Editor to read
    """
    log_file = "logs/system_errors.json"
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Load existing errors or create new list
    try:
        with open(log_file, 'r') as f:
            errors = json.load(f)
    except FileNotFoundError:
        errors = []
    
    # Add new error
    errors.append(error_event)
    
    # Keep only last 100 errors to prevent file from growing too large
    errors = errors[-100:]
    
    # Save back to file
    with open(log_file, 'w') as f:
        json.dump(errors, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Error logged: {error_event['error_id']}")

def get_database_recipe_count():
    """Get current recipe count for system state logging"""
    try:
        with sqlite3.connect('recipegen.db') as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM recipes')
            return cursor.fetchone()[0]
    except:
        return "unknown"

# === Routes ===

# ================================================================================
# TEMPORARY TEST ROUTE - REMOVE BEFORE PRODUCTION
# Purpose: Test the error logging system without waiting for real errors
# Added: 2025-08-13 for error logging system testing
# TODO: Remove this route before deploying to production
# ================================================================================
@app.route('/test_error_logging')
def test_error_logging():
    """
    TEMPORARY: Test route to verify error logging functionality works correctly
    DELETE THIS ROUTE before production deployment
    """
    error_event = log_system_error(
        error_type="test_error",
        user_request={"test": "data"},
        console_snapshot="Test console output",
        resolution="test_resolution"
    )
    return jsonify({"message": "Error logged", "error_id": error_event['error_id']})
# ================================================================================

@app.route('/mockup')
def serve_mockup():
    return send_from_directory('.', 'mockup.html')

@app.route('/ingredients.json')
def serve_ingredients():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    return send_from_directory(data_dir, 'ingredients.json')

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

        # ====================================================       
        # Always deliver what the user requested
        # ====================================================
        # If Levels 1-3 failed, Level 4 (Our Recipe) should have generated the original request.
        # We NEVER return only alternatives - we always give the user what they asked for.
        if isinstance(matched_recipe, dict) and matched_recipe.get('type') == 'generation_failed':
            # Log the error event for Editor analysis
            error_event = log_system_error(
                error_type="4d_search_failure",
                user_request={
                    "cuisine": cuisine,
                    "dish_type": dish_type, 
                    "ingredients": ingredients,
                    "chef_preference": chef_preference
                },
                console_snapshot=capture_console_output(),
                resolution="fallback_to_ai_chef"
            )
            
            print(f"🔄 4D search failed (Error ID: {error_event['error_id']}), invoking AI Chef fallback...")
            # Trigger existing fallback instead of returning error
            matched_recipe = None  # This triggers the existing Essential Recipe logic below

        # Continue with normal flow - we should have a real recipe by now
        if matched_recipe:
            print(f"✅ Recipe generation successful: {matched_recipe.get('title', 'Generated Recipe')}")
        else:
            print("🔄 Proceeding to Essential Recipe generation...")
                
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
        recipe_title = matched_recipe.get('title', f"{cuisine.title()} {dish_type}") if matched_recipe else f"{cuisine.title()} {dish_type}"
        recipe_image = matched_recipe.get('image_url', '') if matched_recipe else ''

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
        
    # PROTECT BUSINESS MODEL - Block recipe giveaways
    recipe_blocking_patterns = [
        "recipe for", "how to make", "how to cook", "how to prepare", 
        "ingredients for", "instructions for", "steps to make",
        "cooking method", "preparation steps", "how do i cook",
        "what ingredients", "cooking instructions", "recipe steps",
        "how to bake", "how to fry", "how to grill", "how to roast",
        "tell me the recipe", "give me the recipe", "full recipe",
        "complete recipe", "step by step", "cooking process"
    ]

    if any(pattern in text for pattern in recipe_blocking_patterns):
        return jsonify({
            "reply": "I'd love to help you create that recipe! Please use our recipe generator above - just select your cuisine and ingredients, and I'll create the complete recipe with detailed instructions and video for $2.99. It's much better than anything I could type here!"
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

    # ⚠️ DEVELOPMENT MODE - CHANGE BEFORE PRODUCTION! ⚠️
    # app.run(host="0.0.0.0", port=port, debug=True)  # ← COMMENTED OUT
    # DEVELOPMENT MODE (with auto-reload)
    app.run(host="0.0.0.0", port=port, debug=True)

    # 🚀 PRODUCTION MODE - Uncomment these lines when deploying:
    # is_production = os.environ.get("ENVIRONMENT") == "production"
    # app.run(
    #     host="0.0.0.0", 
    #     port=port, 
    #     debug=not is_production
    # )