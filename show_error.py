import sqlite3
conn = sqlite3.connect('recipegen.db')
cursor = conn.execute("SELECT task_id, error_message FROM video_generation_tasks WHERE status='failed' ORDER BY created_at DESC LIMIT 1")
result = cursor.fetchone()
if result:
    print(f"Task {result[0][:8]}... failed with error:")
    print(result[1])
conn.close()