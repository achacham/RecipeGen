import sqlite3

conn = sqlite3.connect('recipegen.db')
cursor = conn.execute('''
    SELECT task_id, status, provider_task_id, created_at 
    FROM video_generation_tasks 
    WHERE provider_task_id IS NOT NULL 
    ORDER BY created_at DESC 
    LIMIT 10
''')

print("Tasks with provider IDs:")
for row in cursor:
    print(f"Task: {row[0][:8]}... Status: {row[1]} Provider ID: {row[2]} Time: {row[3]}")

conn.close()