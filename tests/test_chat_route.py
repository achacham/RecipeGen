from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
import json
import os
import openai
from dotenv import load_dotenv

# === Load Environment ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
CORS(app)

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

@app.route('/chat', methods=['POST'])
def chat():
    if session.get('user') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.json
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({'response': 'Empty prompt submitted.'})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful culinary assistant specializing in global cuisine."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        answer = response['choices'][0]['message']['content'].strip()
        return jsonify({'response': answer})

    except Exception as e:
        return jsonify({'response': f'[OpenAI ERROR] {str(e)}'})

@app.route('/ui')
def serve_ui():
    return send_from_directory('static', 'index.html')

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
