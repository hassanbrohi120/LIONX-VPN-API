import os
import json
import google.generativeai as genai

# 🔑 API Key load
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API key missing!")
    exit()

genai.configure(api_key=api_key)

# 🤖 Model
model = genai.GenerativeModel("gemini-1.5-flash")

# 🧠 Prompt (important)
prompt = """
Generate a JSON for VPN services.

Format:
{
  "name": "LIONX VPN",
  "status": "active",
  "servers": [
    {
      "country": "Country Name",
      "ip": "IP Address",
      "protocol": "WireGuard/OpenVPN",
      "status": "online"
    }
  ]
}

Generate at least 5 servers.
Only return JSON. No explanation.
"""

try:
    # 🔥 Gemini response
    response = model.generate_content(prompt)

    text = response.text.strip()

    # 🧹 clean response (kabhi ```json aata hai)
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    # 🔄 convert to JSON
    data = json.loads(text)

except Exception as e:
    print("Gemini error:", e)

    # fallback data (kabhi API fail ho jaye)
    data = {
        "name": "LIONX VPN",
        "status": "fallback",
        "servers": [
            {"country": "Pakistan", "ip": "1.1.1.1", "protocol": "WireGuard", "status": "online"}
        ]
    }

# 💾 file write
with open("services.json", "w") as f:
    json.dump(data, f, indent=4)

print("services.json updated successfully")
