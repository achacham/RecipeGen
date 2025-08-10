# test_api_key.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if key loads
api_key = os.getenv('OPENAI_API_KEY')

if api_key:
    print(f"✅ API Key loaded successfully!")
    print(f"   Key starts with: {api_key[:20]}...")
else:
    print("❌ API Key not found!")
    print("Checking .env file location...")
    
    import pathlib
    env_path = pathlib.Path('.env')
    if env_path.exists():
        print(f"✅ .env file found at: {env_path.absolute()}")
        with open('.env', 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY' in content:
                print("✅ OPENAI_API_KEY exists in .env")
            else:
                print("❌ OPENAI_API_KEY not in .env")
    else:
        print(f"❌ .env file not found at: {env_path.absolute()}")