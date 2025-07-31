import sqlite3

def list_prompts():
    conn = sqlite3.connect('recipegen.db')
    cursor = conn.execute('SELECT id, provider, cuisine_affinity, template_text FROM prompt_templates WHERE is_active = 1')
    
    print("\n=== CURRENT PROMPTS ===")
    for row in cursor:
        print(f"\nID: {row[0]} | Provider: {row[1]} | Cuisine: {row[2] or 'All'}")
        print(f"Template: {row[3][:100]}...")
    
    conn.close()

def edit_prompt(prompt_id):
    conn = sqlite3.connect('recipegen.db')
    
    # Get current prompt
    cursor = conn.execute('SELECT template_text FROM prompt_templates WHERE id = ?', (prompt_id,))
    current = cursor.fetchone()
    
    if current:
        print(f"\nCurrent prompt:\n{current[0]}\n")
        print("Enter new prompt (use {cuisine}, {dish_type}, {ingredients}, {cooking_steps}):")
        print("Type 'END' on a new line when done:\n")
        
        lines = []
        while True:
            line = input()
            if line == 'END':
                break
            lines.append(line)
        
        new_prompt = '\n'.join(lines)
        
        # Update database
        conn.execute('UPDATE prompt_templates SET template_text = ? WHERE id = ?', (new_prompt, prompt_id))
        conn.commit()
        print("\n✅ Prompt updated!")
    
    conn.close()

def add_prompt():
    print("\nEnter new prompt (use {cuisine}, {dish_type}, {ingredients}, {cooking_steps}):")
    print("Type 'END' on a new line when done:\n")
    
    lines = []
    while True:
        line = input()
        if line == 'END':
            break
        lines.append(line)
    
    new_prompt = '\n'.join(lines)
    
    provider = input("\nProvider (kie/fal): ").lower()
    cuisine = input("Specific cuisine (or press Enter for all): ").strip() or None
    
    conn = sqlite3.connect('recipegen.db')
    conn.execute('''
        INSERT INTO prompt_templates (template_text, provider, cuisine_affinity, generation, success_score)
        VALUES (?, ?, ?, 0, 50)
    ''', (new_prompt, provider, cuisine))
    conn.commit()
    conn.close()
    
    print("\n✅ New prompt added!")

# Main menu
while True:
    print("\n=== PROMPT EDITOR ===")
    print("1. List all prompts")
    print("2. Edit a prompt") 
    print("3. Add new prompt")
    print("4. Exit")
    
    choice = input("\nChoice: ")
    
    if choice == '1':
        list_prompts()
    elif choice == '2':
        list_prompts()
        prompt_id = input("\nEnter prompt ID to edit: ")
        edit_prompt(int(prompt_id))
    elif choice == '3':
        add_prompt()
    elif choice == '4':
        break