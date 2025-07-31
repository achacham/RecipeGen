import sqlite3
from video_generator import VideoRecipeGenerator

# Get failed tasks that have provider_task_id
conn = sqlite3.connect('recipegen.db')
cursor = conn.execute('''
    SELECT task_id, provider_task_id, cuisine 
    FROM video_generation_tasks 
    WHERE status = 'failed' 
    AND provider_task_id IS NOT NULL 
    ORDER BY created_at DESC 
    LIMIT 5
''')

generator = VideoRecipeGenerator()

for row in cursor:
    task_id, provider_task_id, cuisine = row
    print(f"\nChecking task {task_id[:8]}... with KIE ID: {provider_task_id}")
    
    # Check if video is still available
    status = generator.check_async_status(provider_task_id)
    print(f"Status: {status}")
    
    if status.get('status') == 'COMPLETED' and status.get('video_url'):
        print(f"🎉 Video found! URL: {status['video_url']}")
        # Try to download it
        filename = f"recovered_{cuisine}_{task_id[:8]}.mp4"
        success, result = generator.download_video(status['video_url'], filename)
        if success:
            print(f"✅ Recovered video saved to: {result}")
        else:
            print(f"❌ Download failed: {result}")

conn.close()