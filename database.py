import sqlite3
import json
from datetime import datetime
from pathlib import Path

class RecipeGenDB:
   def __init__(self, db_path: str = "recipegen.db"):
       self.db_path = Path(db_path)
       self.init_database()
   
   def init_database(self):
       """Create ALL tables for the complete RecipeGen system"""
       with sqlite3.connect(self.db_path) as conn:
           # Enable foreign keys
           conn.execute("PRAGMA foreign_keys = ON")
           
           # 1. ASYNC VIDEO TRACKING
           conn.execute('''
               CREATE TABLE IF NOT EXISTS video_generation_tasks (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   task_id TEXT UNIQUE NOT NULL,
                   recipe_id TEXT NOT NULL,
                   
                   cuisine TEXT NOT NULL,
                   ingredients TEXT NOT NULL,
                   dish_type TEXT,
                   prompt TEXT NOT NULL,
                   
                   provider TEXT NOT NULL,
                   provider_task_id TEXT,
                   
                   status TEXT NOT NULL DEFAULT 'pending',
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   started_at TIMESTAMP,
                   completed_at TIMESTAMP,
                   
                   video_url TEXT,
                   local_path TEXT,
                   error_message TEXT,
                   
                   credits_used INTEGER,
                   generation_time_seconds INTEGER
               )
           ''')
           
           # 2. GATEWAYS (Pasta Gate, Rice Gate, etc.)
           conn.execute('''
               CREATE TABLE IF NOT EXISTS gateways (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT UNIQUE NOT NULL,
                   display_name TEXT NOT NULL,
                   description TEXT,
                   image_url TEXT,
                   sort_order INTEGER DEFAULT 0,
                   is_active BOOLEAN DEFAULT 1,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           ''')
           
           # 3. CUISINES
           conn.execute('''
               CREATE TABLE IF NOT EXISTS cuisines (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   gateway_id INTEGER NOT NULL,
                   name TEXT NOT NULL,
                   display_name TEXT NOT NULL,
                   description TEXT,
                   image_url TEXT,
                   traditional_info TEXT,
                   chef_gender TEXT DEFAULT 'any',  -- male, female, any
                   sort_order INTEGER DEFAULT 0,
                   is_active BOOLEAN DEFAULT 1,
                   FOREIGN KEY (gateway_id) REFERENCES gateways(id)
               )
           ''')
           
           # 4. INGREDIENTS
           conn.execute('''
               CREATE TABLE IF NOT EXISTS ingredients (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT UNIQUE NOT NULL,
                   display_name TEXT NOT NULL,
                   category TEXT,
                   image_url TEXT,
                   description TEXT,
                   cooking_action TEXT,
                   is_active BOOLEAN DEFAULT 1
               )
           ''')
           
           # 5. CUISINE-INGREDIENT MAPPINGS
           conn.execute('''
               CREATE TABLE IF NOT EXISTS cuisine_ingredients (
                   cuisine_id INTEGER NOT NULL,
                   ingredient_id INTEGER NOT NULL,
                   is_default BOOLEAN DEFAULT 0,
                   sort_order INTEGER DEFAULT 0,
                   PRIMARY KEY (cuisine_id, ingredient_id),
                   FOREIGN KEY (cuisine_id) REFERENCES cuisines(id),
                   FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
               )
           ''')
           
           # 6. RECIPES
           conn.execute('''
               CREATE TABLE IF NOT EXISTS recipes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   recipe_id TEXT UNIQUE NOT NULL,
                   cuisine_id INTEGER NOT NULL,
                   dish_type TEXT NOT NULL,
                   ingredients TEXT NOT NULL,
                   recipe_text TEXT NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   video_task_id TEXT,
                   views INTEGER DEFAULT 0,
                   likes INTEGER DEFAULT 0,
                   FOREIGN KEY (cuisine_id) REFERENCES cuisines(id),
                   FOREIGN KEY (video_task_id) REFERENCES video_generation_tasks(task_id)
               )
           ''')
           
           # 7. UI MESSAGES (all user-facing text)
           conn.execute('''
               CREATE TABLE IF NOT EXISTS ui_messages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   key TEXT UNIQUE NOT NULL,
                   value TEXT NOT NULL,
                   category TEXT,  -- 'welcome', 'error', 'prompt', etc.
                   language TEXT DEFAULT 'en',
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           ''')
           
           # 8. PROVIDER SETTINGS
           conn.execute('''
               CREATE TABLE IF NOT EXISTS provider_settings (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   provider_name TEXT UNIQUE NOT NULL,
                   api_key TEXT,
                   is_active BOOLEAN DEFAULT 0,
                   cost_per_video DECIMAL(10,2),
                   average_generation_time INTEGER,  -- seconds
                   quality_score INTEGER,  -- 1-100
                   notes TEXT,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           ''')
           
           # 9. COST TRACKING
           conn.execute('''
               CREATE TABLE IF NOT EXISTS cost_tracking (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date DATE NOT NULL,
                   provider TEXT NOT NULL,
                   videos_generated INTEGER DEFAULT 0,
                   total_cost DECIMAL(10,2) DEFAULT 0,
                   credits_used INTEGER DEFAULT 0,
                   UNIQUE(date, provider)
               )
           ''')
           
           # 10. PROMPT TEMPLATES
           conn.execute('''
               CREATE TABLE IF NOT EXISTS prompt_templates (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   provider TEXT NOT NULL,
                   template_name TEXT NOT NULL,
                   template_text TEXT NOT NULL,
                   is_active BOOLEAN DEFAULT 1,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           ''')

           # 11. PROMPT TEMPLATES WITH EVOLUTION TRACKING
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_text TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    cuisine_affinity TEXT,  -- Works best with which cuisine
                    
                    -- Evolution tracking
                    generation INTEGER DEFAULT 0,  -- 0=human created, 1+ = AI evolved
                    parent_template_id INTEGER,  -- Which template it mutated from
                    mutation_description TEXT,  -- What changed
                    
                    -- Performance metrics
                    total_uses INTEGER DEFAULT 0,
                    successful_videos INTEGER DEFAULT 0,  -- Led to completed videos
                    videos_purchased INTEGER DEFAULT 0,  -- Led to recipe purchases
                    avg_video_quality FLOAT DEFAULT 0,  -- Based on flags
                    
                    -- Calculated success score (0-100)
                    success_score FLOAT DEFAULT 50,
                    
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (parent_template_id) REFERENCES prompt_templates(id)
                )
            ''')
            
            # 12. TRACK EVERY VIDEO RESULT
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prompt_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id INTEGER NOT NULL,
                    task_id TEXT NOT NULL,
                    
                    -- Quality flags (set by reviewing video)
                    has_vanishing_objects BOOLEAN DEFAULT 0,
                    has_scene_continuity BOOLEAN DEFAULT 0,
                    has_all_ingredients_visible BOOLEAN DEFAULT 0,
                    has_logical_sequence BOOLEAN DEFAULT 0,
                    
                    -- User behavior
                    video_watched_seconds INTEGER DEFAULT 0,
                    recipe_purchased BOOLEAN DEFAULT 0,
                    user_rating INTEGER,  -- 1-5 stars
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (template_id) REFERENCES prompt_templates(id),
                    FOREIGN KEY (task_id) REFERENCES video_generation_tasks(task_id)
                )
            ''')
           
           # Create indexes for performance
           conn.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON video_generation_tasks(status)')
           conn.execute('CREATE INDEX IF NOT EXISTS idx_recipe_created ON recipes(created_at)')
           conn.execute('CREATE INDEX IF NOT EXISTS idx_cost_date ON cost_tracking(date)')
           
           print("✅ Database initialized with all tables!")
   
   # ASYNC VIDEO METHODS
   def create_video_task(self, task_id: str, recipe_id: str, cuisine: str, 
                        ingredients: list, dish_type: str, prompt: str, provider: str) -> int:
       """Create a new async video generation task"""
       with sqlite3.connect(self.db_path) as conn:
           cursor = conn.execute('''
               INSERT INTO video_generation_tasks 
               (task_id, recipe_id, cuisine, ingredients, dish_type, prompt, provider)
               VALUES (?, ?, ?, ?, ?, ?, ?)
           ''', (task_id, recipe_id, cuisine, json.dumps(ingredients), 
                 dish_type, prompt, provider))
           return cursor.lastrowid
   
   def get_pending_tasks(self):
       """Get all pending/processing video tasks"""
       with sqlite3.connect(self.db_path) as conn:
           conn.row_factory = sqlite3.Row
           cursor = conn.execute('''
               SELECT * FROM video_generation_tasks 
               WHERE status IN ('pending', 'processing')
               ORDER BY created_at ASC
           ''')
           return [dict(row) for row in cursor.fetchall()]
   
   def update_task_status(self, task_id: str, status: str, **kwargs):
       """Update task status and optional fields"""
       fields = ['status = ?']
       values = [status]
       
       if status == 'processing' and 'started_at' not in kwargs:
           fields.append('started_at = CURRENT_TIMESTAMP')
       
       if status == 'completed' and 'completed_at' not in kwargs:
           fields.append('completed_at = CURRENT_TIMESTAMP')
           
       for key, value in kwargs.items():
           fields.append(f'{key} = ?')
           values.append(value)
           
       values.append(task_id)
       
       with sqlite3.connect(self.db_path) as conn:
           conn.execute(f'''
               UPDATE video_generation_tasks 
               SET {', '.join(fields)}
               WHERE task_id = ?
           ''', values)
   
   # CMS METHODS FOR YOUR WIFE
   def get_all_gateways(self):
       """Get all gateways for the editor"""
       with sqlite3.connect(self.db_path) as conn:
           conn.row_factory = sqlite3.Row
           cursor = conn.execute('''
               SELECT * FROM gateways 
               WHERE is_active = 1 
               ORDER BY sort_order, display_name
           ''')
           return [dict(row) for row in cursor.fetchall()]
   
   def update_provider_settings(self, provider_name: str, api_key: str, is_active: bool):
       """Update provider API keys and settings"""
       with sqlite3.connect(self.db_path) as conn:
           conn.execute('''
               INSERT OR REPLACE INTO provider_settings 
               (provider_name, api_key, is_active, updated_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ''', (provider_name, api_key, is_active))

# Initialize on import
db = RecipeGenDB()
