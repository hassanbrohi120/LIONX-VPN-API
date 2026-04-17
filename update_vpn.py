import os
import json
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

prompt = """
Generate ONLY valid JSON:

{
  "name": "LIONX VPN",
  "servers": [
    {
      "country": "Pakistan",
      "ip": "1.1.1.1",
      "protocol": "WireGuard",
      "status": "online"
    }
  ]
}
"""

try:
    res = model.generate_content(prompt)
    text = res.text.strip()

    if "```" in text:
        text = text.replace("```json", "").replace("```", "").strip()

    data = json.loads(text)

except:
    data = {
        "name": "LIONX VPN",
        "servers": [
            {"country": "Pakistan", "ip": "1.1.1.1", "protocol": "WireGuard", "status": "online"}
        ]
    }

with open("services.json", "w") as f:
    json.dump(data, f, indent=4)

print("DONE")
