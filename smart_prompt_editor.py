import sqlite3
from prompt_evolution import prompt_evolution

def list_prompts():
    conn = sqlite3.connect('recipegen.db')
    cursor = conn.execute('''
        SELECT id, provider, cuisine_affinity, success_score, total_uses, 
               successful_videos, template_text 
        FROM prompt_templates 
        WHERE is_active = 1 
        ORDER BY success_score DESC
    ''')
    
    print("\n=== PROMPTS (Sorted by Success) ===")
    for row in cursor:
        id, provider, cuisine, score, uses, successes, text = row
        print(f"\nID: {id} | Provider: {provider} | Cuisine: {cuisine or 'All'}")
        print(f"📊 Score: {score:.1f}% | Uses: {uses} | Successes: {successes}")
        print(f"Template: {text[:100]}...")
    
    conn.close()

def clone_and_edit(prompt_id):
    """Clone a successful prompt and create a variation"""
    conn = sqlite3.connect('recipegen.db')
    
    # Get original prompt
    cursor = conn.execute('''
        SELECT template_text, provider, cuisine_affinity, success_score 
        FROM prompt_templates WHERE id = ?
    ''', (prompt_id,))
    original = cursor.fetchone()
    
    if original:
        text, provider, cuisine, score = original
        print(f"\n📊 Original (Score: {score:.1f}%):\n{text}\n")
        print("Create a VARIATION (use {cuisine}, {dish_type}, {ingredients}, {cooking_steps}):")
        print("Type 'END' on a new line when done:\n")
        
        lines = []
        while True:
            line = input()
            if line == 'END':
                break
            lines.append(line)
        
        new_prompt = '\n'.join(lines)
        
        # Add as child/mutation
        conn.execute('''
            INSERT INTO prompt_templates 
            (template_text, provider, cuisine_affinity, generation, parent_template_id, 
             mutation_description, success_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (new_prompt, provider, cuisine, 1, prompt_id, 'Manual variation', score * 0.9))
        conn.commit()
        print("\n✅ Variation created! It will compete with the original.")
    
    conn.close()

def test_prompt(prompt_id):
    """Test how a prompt would render"""
    conn = sqlite3.connect('recipegen.db')
    cursor = conn.execute('SELECT template_text FROM prompt_templates WHERE id = ?', (prompt_id,))
    template = cursor.fetchone()
    
    if template:
        # Test with sample data
        test_prompt = template[0].format(
            cuisine="Indonesian",
            dish_type="pasta",
            ingredients="Salmon, Soy Sauce, Chili Peppers, Scallions",
            cooking_steps="cooking pasta. adding salmon. stirring vegetables"
        )
        print(f"\n🧪 TEST RENDER:\n{test_prompt}")
    
    conn.close()

def view_evolution_tree(prompt_id):
    """See the family tree of prompts"""
    conn = sqlite3.connect('recipegen.db')
    
    # Get all related prompts
    cursor = conn.execute('''
        WITH RECURSIVE prompt_tree AS (
            SELECT id, parent_template_id, mutation_description, success_score, generation, 0 as depth
            FROM prompt_templates WHERE id = ?
            
            UNION ALL
            
            SELECT p.id, p.parent_template_id, p.mutation_description, p.success_score, 
                   p.generation, pt.depth + 1
            FROM prompt_templates p
            JOIN prompt_tree pt ON p.parent_template_id = pt.id
        )
        SELECT * FROM prompt_tree ORDER BY depth, success_score DESC
    ''', (prompt_id,))
    
    print(f"\n🌳 EVOLUTION TREE:")
    for row in cursor:
        id, parent, mutation, score, gen, depth = row
        indent = "  " * depth
        print(f"{indent}ID {id}: Gen {gen}, Score {score:.1f}% - {mutation or 'Original'}")
    
    conn.close()

# Main menu
while True:
    print("\n=== SMART PROMPT EDITOR ===")
    print("1. List all prompts (by success)")
    print("2. Clone & edit a successful prompt") 
    print("3. Test render a prompt")
    print("4. View evolution tree")
    print("5. Exit")
    
    choice = input("\nChoice: ")
    
    if choice == '1':
        list_prompts()
    elif choice == '2':
        list_prompts()
        prompt_id = input("\nEnter prompt ID to clone & edit: ")
        clone_and_edit(int(prompt_id))
    elif choice == '3':
        prompt_id = input("\nEnter prompt ID to test: ")
        test_prompt(int(prompt_id))
    elif choice == '4':
        prompt_id = input("\nEnter prompt ID to see evolution: ")
        view_evolution_tree(int(prompt_id))
    elif choice == '5':
        break