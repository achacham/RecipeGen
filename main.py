
# ✅ Tehomia Diagnostic GPT Interface (Standalone)
import openai
import os

from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Sample diagnostic payload
diagnostic_messages = [
    {"role": "system", "content": "You are a diagnostic-bound assistant. Your role is to trace and expose handler-to-UI propagation flaws using structured debug output."},
    {"role": "user", "content": "Generate a sample recipe object and output:\n🧠 Pipeline Debug — Cuisine\n🧠 Pipeline Debug — Title\n🧠 Pipeline Debug — Static Image\n🚀 Final Response JSON"}
]

# Execute ChatGPT call
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=diagnostic_messages,
    temperature=0.2
)

# Extract and print result
print("\n🔎 RESPONSE FROM GPT:\n")
print(response.choices[0].message.content)
