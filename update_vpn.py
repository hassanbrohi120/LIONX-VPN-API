import requests
import base64
import json
import socket
import time
import os

# 1. Base Sources
SOURCES = [
    "https://raw.githubusercontent.com/freefq/free/master/v2ray",
    "https://raw.githubusercontent.com/v2rayfree/v2rayfree.github.io/main/v2ray"
]

# 2. Agentic Discovery: GitHub par naye servers dhoondna
def discover_new_sources():
    github_token = os.getenv("GH_TOKEN") # Aapka secret token
    headers = {"Authorization": f"token {github_token}"}
    query = "ss:// filename:nodes.txt OR filename:ss.txt OR filename:servers.json"
    url = f"https://api.github.com/search/code?q={query}&sort=indexed"
    
    new_links = []
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json().get('items', [])
            for item in items[:5]: # Top 5 naye repositories
                raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                new_links.append(raw_url)
    except: pass
    return new_links

def get_latency(host, port):
    try:
        start = time.time()
        sock = socket.create_connection((host, int(port)), timeout=1.5)
        sock.close()
        return int((time.time() - start) * 1000)
    except: return None

def update_process():
    # Discovery phase
    dynamic_sources = discover_new_sources()
    all_sources = SOURCES + dynamic_sources
    
    all_raw_nodes = []
    for url in all_sources:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                # Direct links or Base64 detection
                content = r.text
                if "ss://" not in content:
                    content = base64.b64decode(content + '===').decode('utf-8', 'ignore')
                
                all_raw_nodes.extend([l for l in content.splitlines() if l.startswith("ss://")])
        except: continue

    final_servers = []
    seen_configs = set()
    
    # Testing Phase (Har ghante fast servers select karna)
    for node in list(set(all_raw_nodes))[:60]: # Test more nodes
        if node in seen_configs: continue
        try:
            # Cleaning node URL
            clean_node = node.split("#")[0].split("?")[0]
            core = clean_node.split("@")[1]
            host, port = core.split(":")[0], core.split(":")[1]
            
            ping = get_latency(host, port)
            
            # Filter: Only very fast servers (< 400ms)
            if ping and ping < 400:
                # Smart Name & Country Detection
                c_code = "us"
                for code in ['gb', 'de', 'jp', 'nl', 'fr', 'ca', 'in', 'sg']:
                    if code in node.lower(): c_code = code; break

                final_servers.append({
                    "name": f"LIONX | {c_code.upper()} | {ping}ms",
                    "config": node,
                    "countryCode": c_code
                })
                seen_configs.add(node)
        except: continue

    # Sorting by fastest ping
    final_servers.sort(key=lambda x: int(x['name'].split('|')[-1].replace('ms','')))

    with open('services.json', 'w') as f:
        json.dump(final_servers[:30], f, indent=2)

if __name__ == "__main__":
    update_process()