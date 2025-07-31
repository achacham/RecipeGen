from video_generator import VideoRecipeGenerator

# The KIE task ID from your console
kie_task_id = '1e38283098b059fa5b72ebae6ab571a7'

generator = VideoRecipeGenerator()
print(f"Checking KIE task: {kie_task_id}")

# Check status directly with KIE
import requests
headers = {
    'Authorization': f'Bearer {generator.api_key}',
    'Content-Type': 'application/json'
}

url = f"https://api.kie.ai/api/v1/veo/record-info?taskId={kie_task_id}"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    result = response.json()
    print(f"KIE Response: {result}")
    
    if result.get("code") == 200:
        data = result.get("data", {})
        if data.get("successFlag") == 1:
            response_data = data.get("response", {})
            video_urls = response_data.get("resultUrls", [])
            if video_urls:
                print(f"\n🎉 VIDEO IS READY!")
                print(f"URL: {video_urls[0]}")
                
                # Try to download it
                filename = "manual_indonesian_pasta.mp4"
                success, path = generator.download_video(video_urls[0], filename)
                if success:
                    print(f"✅ Downloaded to: {path}")
                else:
                    print(f"❌ Download failed: {path}")
        else:
            print("Video still processing or failed")