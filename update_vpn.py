import os
import json
import socket
import requests
import re
import google.generativeai as genai
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# ======================
# CONFIG
# ======================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ======================
# FAST SAFE PING CHECK
# ======================
def is_alive(config_url):
    try:
        if not config_url:
            return False

        clean_url = config_url.split('#')[0]
        parsed = urlparse(clean_url)
        host_port = parsed.netloc.split('@')[-1]

        if not host_port:
            return False

        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 443

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()

        return result == 0

    except:
        return False


# ======================
# GITHUB SEARCH FIXED
# ======================
def search_github_configs():
    print("GitHub scanning...")

    query = "ss:// OR hy2:// extension:txt OR extension:md"
    url = f"https://api.github.com/search/code?q={query}&per_page=10"

    found = []

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        for item in data.get("items", []):
            raw_url = item["html_url"].replace(
                "github.com",
                "raw.githubusercontent.com"
            ).replace("/blob/", "/")

            try:
                text = requests.get(raw_url, timeout=8).text
                links = re.findall(r'(ss://[^\s\'"<>]+|hy2://[^\s\'"<>]+)', text)

                for link in links:
                    found.append({
                        "name": "GH-SERVER",
                        "config": link,
                        "countryCode": "un"
                    })
            except:
                continue

    except Exception as e:
        print("GitHub error:", e)

    return found


# ======================
# GEMINI AI FIXED
# ======================
def get_ai_servers():
    print("AI servers fetch...")

    prompt = """
Return ONLY JSON array:

[
  {"name":"US","config":"ss://...","countryCode":"us"}
]

Generate 15 working VPN nodes.
"""

    try:
        res = model.generate_content(prompt)
        text = res.text.strip()

        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            if isinstance(data, list):
                return data

    except Exception as e:
        print("AI error:", e)

    return []


# ======================
# MULTITHREAD CHECK (FAST)
# ======================
def filter_alive(nodes):
    alive = []

    def check(node):
        if is_alive(node.get("config")):
            return node
        return None

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(check, nodes)

    for r in results:
        if r:
            alive.append(r)

    return alive


# ======================
# MAIN
# ======================
def main():
    file_path = "services.json"

    # Load file safely
    try:
        with open(file_path, "r") as f:
            current = json.load(f)
    except:
        current = []

    print("Current:", len(current))

    # Step 1: clean old
    print("Checking existing servers...")
    current = filter_alive(current)

    # Step 2: refill if low
    if len(current) < 15:
        new_nodes = search_github_configs() + get_ai_servers()

        print("New found:", len(new_nodes))

        current += filter_alive(new_nodes)

    # Step 3: remove duplicates
    unique = {}
    for s in current:
        key = s.get("config")
        if key:
            unique[key] = s

    final = list(unique.values())

    # Step 4: save safely
    if final:
        with open(file_path, "w") as f:
            json.dump(final, f, indent=2)

        print("Saved:", len(final))

    else:
        print("No valid servers found")


if __name__ == "__main__":
    main()
