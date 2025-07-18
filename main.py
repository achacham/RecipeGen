# ✅ Tehomia Diagnostic GPT Interface (Unified and Executable)

from openai import OpenAI
import os
from dotenv import load_dotenv

def run_diagnostics():
    print("✅ MAIN.PY LOADED — Running...\n")

    # 🧬 Load environment and check key
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    print("🔐 Loaded API Key:", "YES" if api_key else "NO")

    if not api_key:
        print("❌ ERROR: No API key loaded. Check .env file.")
        return

    # 🧠 Initialize client
    client = OpenAI(api_key=api_key)

    # 🧪 Sample diagnostic payload
    diagnostic_messages = [
        {
            "role": "system",
            "content": "You are a diagnostic-bound assistant. Your role is to trace and expose handler-to-UI propagation flaws using structured debug output."
        },
        {
            "role": "user",
            "content": "Generate a sample recipe object and output:\n📦 Pipeline Debug - Cuisine\n📄 Pipeline Debug - Title\n🖼️ Pipeline Debug - Static Image\n🚀 Final Response JSON"
        }
    ]

    # 🚀 Execute call with checkpoints
    try:
        print("📡 Sending request to GPT...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=diagnostic_messages,
            temperature=0.2
        )
        print("📨 Got response, printing now...\n")
        print(response.choices[0].message.content)

    except Exception as e:
        print("❌ GPT CALL FAILED:")
        print(e)

# 🔁 Trigger when script is run directly
if __name__ == "__main__
