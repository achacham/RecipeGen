from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
import json
import os
import openai
import sys
import requests
from dotenv import load_dotenv

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

# === Assign Keys ===
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
CORS(app)

# ✅ Blueprint registration
from video_routes import video_bp
app.register_blueprint(video_bp)

# === Load Data ===
with open('data/recipes.json') as f:
    recipes = json.load(f)

with open('data/history.json') as f:
    history = json.load(f)

# === Routes ===

@app.route('/categories', methods=['GET'])
def get_categories():
    categories = list({r['category'] for r in recipes})
    return jsonify(categories)

@app.route('/recipes', methods=['GET'])
def get_recipes():
    category = request.args.get('category')
    if category:
        filtered = [r for r in recipes if r['category'].lower() == category.lower()]
        return jsonify(filtered)
    return jsonify(recipes)

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
            entry = {'recipe_id': recipe_id, 'title': r['title']}
            history.append(entry)
            with open('data/history.json', 'w') as f:
                json.dump(history, f, indent=2)
            return jsonify({'instructions': 'Step-by-step instructions will appear here.'})
    return jsonify({'error': 'Recipe not found'}), 404

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(history)

@app.route('/login', methods=['POST'])
def login():
    credentials = request.json
    if credentials.get('username') == 'admin' and credentials.get('password') == 'password123':
        session['user'] = 'admin'
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failure'}), 401

@app.route("/ingredients", methods=["GET"])
def get_ingredients():
    try:
        with open("data/ingredients.json", "r", encoding="utf-8") as f:
            ingredients = json.load(f)
        return jsonify(ingredients)
    except Exception as e:
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
    if "login" in text or "log in" in text:
        print("🟡 Intercepted login/log in question")
        return jsonify({
            'reply': (
                "To log in, click the “Login” link in the top‑right navbar, "
                "enter your username and password, then hit Submit."
            )
        })

    admin_keywords = ["administrator", "admin", "support", "help", "contact", "account", "password"]
    if any(kw in text for kw in admin_keywords):
        print("🟡 Intercepted administrative/support question")
        return jsonify({
            'reply': (
                "For site‑administration or support issues, please use the “Contact” "
                "link in the top‑right navbar or email support@yourdomain.com."
            )
        })

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are RecipeGen."},
                {"role": "user",   "content": user_message}
            ],
            max_tokens=150
        )
        ai_reply = resp.choices[0].message.content.strip()
        print("🟣 AI reply:", ai_reply)
    except Exception as e:
        print("❌ OpenAI error:", e)
        return jsonify({'error': 'Server error'}), 500

    return jsonify(reply=ai_reply)

@app.route('/generate_video', methods=['POST'])
def generate_video():
    try:
        data = request.get_json(force=True)
        if not data:
            raise ValueError("No JSON data received")

        ingredients = data.get("ingredients", [])
        cuisine = data.get("cuisine", "")

        print("✅ Received ingredients:", ingredients)
        print("✅ Received cuisine:", cuisine)

        prompt = f"A {cuisine} cooking scene featuring {', '.join(ingredients)}. Close-up of preparation with rustic kitchen backdrop, natural lighting, and warm color tones."

        # 🔁 Simulated Video URL (mock result)
        video_url = f"https://static.tehomia.org/mock_videos/{cuisine.lower()}_{'_'.join(ingredients)}.mp4"
        print("✅ Mock video URL:", video_url)

        return jsonify({
            "video_url": video_url,
            "prompt": prompt
        })

    except Exception as e:
        print("❌ Video generation error:", str(e))
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

@app.route('/ui')
def serve_ui():
    return send_from_directory('static', 'index.html')

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
