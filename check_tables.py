import sqlite3

conn = sqlite3.connect('recipegen.db')

# Check the structure of prompt_templates
print("Checking prompt_templates structure...")
cursor = conn.execute("PRAGMA table_info(prompt_templates)")
columns = cursor.fetchall()

print("\nColumns in prompt_templates:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Check if table has any data
cursor = conn.execute("SELECT COUNT(*) FROM prompt_templates")
count = cursor.fetchone()[0]
print(f"\nRows in table: {count}")

conn.close()