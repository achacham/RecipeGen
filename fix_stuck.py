import sqlite3

conn = sqlite3.connect('recipegen.db')

# Reset all stuck 'processing' tasks to 'pending'
cursor = conn.execute('''
    UPDATE video_generation_tasks 
    SET status = 'pending', started_at = NULL 
    WHERE status = 'processing'
''')

print(f"Reset {cursor.rowcount} stuck tasks to pending")

# Show current tasks
cursor = conn.execute('''
    SELECT task_id, status FROM video_generation_tasks 
    WHERE status IN ('pending', 'processing') 
    ORDER BY created_at DESC
''')

print("\nCurrent pending/processing tasks:")
for row in cursor:
    print(f"  {row[0][:8]}... Status: {row[1]}")

conn.commit()
conn.close()