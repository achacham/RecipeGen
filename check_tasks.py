import sqlite3

# Connect to your database file
conn = sqlite3.connect('recipegen.db')

# Get the last 5 tasks
cursor = conn.execute('''
    SELECT task_id, status, recipe_id, created_at 
    FROM video_generation_tasks 
    ORDER BY created_at DESC 
    LIMIT 5
''')

print("\nYour recent video tasks:")
for row in cursor:
    print(f"Task: {row[0][:8]}... Status: {row[1]} Recipe: {row[2][:8] if row[2] else 'None'}... Time: {row[3]}")

conn.close()