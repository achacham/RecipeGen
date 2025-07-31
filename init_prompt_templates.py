import sqlite3

# Connect to database
conn = sqlite3.connect('recipegen.db')

# Check if we already have templates
cursor = conn.execute('SELECT COUNT(*) FROM prompt_templates')
count = cursor.fetchone()[0]

if count == 0:
    print("Adding initial prompt template...")
    
    # Insert the default KIE prompt template
    conn.execute('''
        INSERT INTO prompt_templates 
        (template_text, provider, cuisine_affinity, generation, success_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        '''{cuisine} chef in traditional kitchen preparing {dish_type} with {ingredients}.
COMPLETE COOKING SEQUENCE showing EVERY step:
{cooking_steps}
Show CONTINUOUS cooking action from start to finish.
Traditional {cuisine} setting with proper cookware.
LOUD sizzling sounds throughout, kitchen ambiance, traditional {cuisine} music.''',
        'kie',
        None,  # Works for all cuisines
        0,     # Human created
        50     # Starting score
    ))
    
    conn.commit()
    print("✅ Initial prompt template added!")
else:
    print(f"Already have {count} prompt templates")

conn.close()