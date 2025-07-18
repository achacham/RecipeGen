# ✅ Tehomia Diagnostic GPT Interface (Compatible with OpenAI ≥ 1.0.0)

from openai import OpenAI
import os
from dotenv import load_dotenv

# 🧪 Load environment and check key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print("🔍 Loaded API Key:", "YES" if api_key else "NO")

# 🧪 Initialize client
client = OpenAI(api_key=api_key)

# 🧪 Sample diagnostic payload
diagnostic_messages = [
    {"role": "system", "content": "You are a diagnostic-bound assistant. Your role is to trace and expose handler-to-UI propagation flaws using structured debug output."},
    {"role": "user", "content": "Generate a sample recipe object and output:\n📦 Pipeline Debug - Cuisine\n📄 Pipeline Debug - Title\n🖼️ Pipeline Debug - Static Image\n🚀 Final Response JSON"}
]

# 🚀 Execute call
try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=diagnostic_messages,
        temperature=0.2
    )

    # 📤 Print result
    print("\n📤 RESPONSE FROM GPT:\n")
    print(response.choices[0].message.content)

except Exception as e:
    print("❌ GPT CALL FAILED:")
    print(e)
