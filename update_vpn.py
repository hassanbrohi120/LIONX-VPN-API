import os
import json
import socket
import requests
import re
import google.generativeai as genai
from urllib.parse import urlparse

# 1. API Configurations
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Ping Test Function (Timeout 5s for better accuracy)
def is_alive(config_url):
    try:
        if not config_url: return False
        clean_url = config_url.split('#')[0]
        parsed = urlparse(clean_url)
        host_port = parsed.netloc.split('@')[-1]
        
        if ':' in host_port:
            host = host_port.split(':')[0]
            port = int(host_port.split(':')[1])
        else:
            host = host_port
            port = 443 # Default port

        with socket.create_connection((host, port), timeout=5):
            return True
    except:
        return False

# 3. GitHub Search Function
def search_github_configs():
    print("GitHub se naye servers dhoond raha hoon...")
    headers = {"Authorization": f"token {GH_TOKEN}"}
    query = "ss:// OR hy2:// extension:txt OR extension:md"
    url = f"[https://api.github.com/search/code?q=](https://api.github.com/search/code?q=){query}&sort=indexed&order=desc"
    
    found_configs = []
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get('items', [])[:15] 
            for item in items:
                file_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                content = requests.get(file_url).text
                links = re.findall(r'(ss://[^\s\'"<>]+|hy2://[^\s\'"<>]+)', content)
                for link in links:
                    found_configs.append({
                        "name": "LIONX-GH-SERVER",
                        "config": link,
                        "countryCode": "un"
                    })
    except Exception as e:
        print(f"GitHub Error: {e}")
    return found_configs

# 4. Gemini AI Search (With JSON extraction fix)
def get_new_servers_from_ai():
    print("Gemini AI se naye servers mangwa raha hoon...")
    prompt = """Provide a JSON list of 30 fresh Shadowsocks (ss://) and Hysteria2 (hy2://) nodes. 
    Format: [{"name": "Country", "config": "url", "countryCode": "us"}]. 
    Return ONLY the raw JSON array."""
    try:
        response = model.generate_content(prompt)
        text = response.text
        # Extract JSON using Regex (Important Fix)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        print(f"AI Error: {e}")
        return []

# 5. Main Process
def main():
    file_path = 'services.json'
    
    # Load current file
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                current_servers = json.load(f)
        else:
            current_servers = []
    except:
        current_servers = []

    print(f"Pehle se maujood: {len(current_servers)}")

    # Step 1: Filter Alive Servers
    print("Zinda servers check ho rahe hain...")
    verified_servers = [s for s in current_servers if is_alive(s.get('config', ''))]
    print(f"Zinda bache: {len(verified_servers)}")

    # Step 2: Add New if needed
    if len(verified_servers) < 20:
        new_nodes = search_github_configs() + get_new_servers_from_ai()
        print(f"Dhoonde gaye naye: {len(new_nodes)}")
        
        for node in new_nodes:
            if is_alive(node.get('config', '')):
                verified_servers.append(node)

    # Step 3: Remove Duplicates
    final_data = list({s['config']: s for s in verified_servers}.values())

    # Step 4: Final Save (Only if not empty)
    if final_data:
        with open(file_path, 'w') as f:
            json.dump(final_data, f, indent=2)
        print(f"Success! {len(final_data)} servers save ho gaye.")
    else:
        print("Koi working server nahi mila, file update nahi ki.")

if __name__ == "__main__":
    main()
