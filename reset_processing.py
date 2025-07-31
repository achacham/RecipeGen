import sqlite3

conn = sqlite3.connect('recipegen.db')
cursor = conn.execute('''
    UPDATE video_generation_tasks 
    SET status = 'pending', started_at = NULL, provider_task_id = NULL
    WHERE status = 'processing'
''')
conn.commit()
print(f"Reset {cursor.rowcount} processing tasks to pending")
conn.close()