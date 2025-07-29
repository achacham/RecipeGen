"""
RecipeGen Backend API
Main Flask application for recipe generation, video creation, and chat functionality
"""

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
import json
import os
import openai
import sys
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"🚀 Starting RecipeGen on port {port}")
    app.run(host="0.0.0.0", port=port)