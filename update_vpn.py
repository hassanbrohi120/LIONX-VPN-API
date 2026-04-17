import os
import json
import socket
import requests
import re
import google.generativeai as genai
from urllib.parse import urlparse

# 1. API Configurations (GitHub Secrets se ayenge)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Ping Test Function (Zinda servers check karne ke liye)
def is_alive(config_url):
    try:
        if not config_url: return False
        # Link se IP aur Port nikalna
        clean_url = config_url.split('#')[0]
        parsed = urlparse(clean_url)
        host_port = parsed.netloc.split('@')[-1]
        
        if ':' in host_port:
            host = host_port.split(':')[0]
            port = int(host_port.split(':')[1])
        else:
            return False

        # Connection check (3 seconds timeout)
        with socket.create_connection((host, port), timeout=3):
            return True
    except:
        return False

# 3. GitHub se Configs dhoondne ka Function
def search_github_configs():
    print("GitHub se naye servers dhoond raha hoon...")
    headers = {"Authorization": f"token {GH_TOKEN}"}
    query = "ss:// OR hy2:// extension:txt OR extension:md"
    url = f"https://api.github.com/search/code?q={query}&sort=indexed&order=desc"
    
    found_configs = []
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get('items', [])[:15] 
            for item in items:
                file_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                content = requests.get(file_url).text
                # Links nikalne ke liye Regex
                links = re.findall(r'(ss://[^\s\'"<>]+|hy2://[^\s\'"<>]+)', content)
                for link in links:
                    found_configs.append({
                        "name": "LIONX-GH-SERVER",
                        "config": link,
                        "countryCode": "un"
                    })
    except Exception as e:
        print(f"GitHub search error: {e}")
    return found_configs

# 4. Gemini AI se Configs mangwane ka Function
def get_new_servers_from_ai():
    print("Gemini AI se naye servers mangwa raha hoon...")
    prompt = """
    Search and provide a JSON list of 30 fresh and working Shadowsocks (ss://) and Hysteria2 (hy2://) nodes.
    Format MUST be exactly like this:
    [
      {"name": "COUNTRY_NAME", "config": "ss_or_hy2_link", "countryCode": "us"}
    ]
    Return ONLY raw JSON, no markdown, no comments.
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return []

# 5. Main Process
def main():
    file_path = 'services.json'
    
    # Purani file load karein
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                current_servers = json.load(f)
            except:
                current_servers = []
    else:
        current_servers = []

    print(f"Total purane servers: {len(current_servers)}")

    # STEP 1: Ping Test (Jo band hain unhe delete kardo)
    print("Ping test aur safai shuru...")
    verified_servers = [s for s in current_servers if is_alive(s.get('config', ''))]
    print(f"Zinda bache servers: {len(verified_servers)}")

    # STEP 2: Naye servers ki talash (Agar 20 se kam hon)
    if len(verified_servers) < 20:
        gh_nodes = search_github_configs()
        ai_nodes = get_new_servers_from_ai()
        
        all_new = gh_nodes + ai_nodes
        print(f"Dhoonde gaye naye servers: {len(all_new)}")
        
        # Naye servers ko test karke add karein
        for node in all_new:
            if is_alive(node.get('config', '')):
                verified_servers.append(node)

    # STEP 3: Duplicates khatam karein (Base on Config URL)
    final_list = {s['config']: s for s in verified_servers}.values()

    # STEP 4: Save karein
    with open(file_path, 'w') as f:
        json.dump(list(final_list), f, indent=2)
    
    print(f"Kaam mukammal! Final active servers saved: {len(final_list)}")

if __name__ == "__main__":
    main()
