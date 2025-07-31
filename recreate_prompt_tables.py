import sqlite3

print("Recreating prompt tables with evolution structure...")

conn = sqlite3.connect('recipegen.db')

try:
    # Drop existing tables
    print("Dropping old tables...")
    conn.execute("DROP TABLE IF EXISTS prompt_results")
    conn.execute("DROP TABLE IF EXISTS prompt_templates")
    
    # Create new tables with evolution tracking
    print("Creating new prompt_templates table...")
    conn.execute('''
        CREATE TABLE prompt_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_text TEXT NOT NULL,
            provider TEXT NOT NULL,
            cuisine_affinity TEXT,
            
            generation INTEGER DEFAULT 0,
            parent_template_id INTEGER,
            mutation_description TEXT,
            
            total_uses INTEGER DEFAULT 0,
            successful_videos INTEGER DEFAULT 0,
            videos_purchased INTEGER DEFAULT 0,
            avg_video_quality FLOAT DEFAULT 0,
            
            success_score FLOAT DEFAULT 50,
            
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (parent_template_id) REFERENCES prompt_templates(id)
        )
    ''')
    
    print("Creating prompt_results table...")
    conn.execute('''
        CREATE TABLE prompt_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            
            has_vanishing_objects BOOLEAN DEFAULT 0,
            has_scene_continuity BOOLEAN DEFAULT 0,
            has_all_ingredients_visible BOOLEAN DEFAULT 0,
            has_logical_sequence BOOLEAN DEFAULT 0,
            
            video_watched_seconds INTEGER DEFAULT 0,
            recipe_purchased BOOLEAN DEFAULT 0,
            user_rating INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (template_id) REFERENCES prompt_templates(id),
            FOREIGN KEY (task_id) REFERENCES video_generation_tasks(task_id)
        )
    ''')
    
    conn.commit()
    print("✅ Tables recreated successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    
conn.close()