import sqlite3

# Check for the task that's being polled
task_id = '0f65e3e57e94dbe891d0f66c01af9a9d'

conn = sqlite3.connect('recipegen.db')
cursor = conn.execute(
    'SELECT * FROM video_generation_tasks WHERE task_id = ?',
    (task_id,)
)
result = cursor.fetchone()

if result:
    print(f"Task found: {result}")
else:
    print(f"Task {task_id} NOT in database!")

conn.close()
