import os
import json
import socket
import requests
import re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

# ======================
# CONFIG
# ======================
GH_TOKEN = os.getenv("GH_TOKEN")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ======================
# SOURCES
# ======================
SOURCES = [
    "https://vlesskeys.com/",
    "https://keyvpn.net/",
]

# ======================
# COUNTRY CODE MAP
# ======================
COUNTRY_MAP = {
    "us": "UNITED STATES", "de": "GERMANY", "nl": "NETHERLANDS",
    "gb": "UNITED KINGDOM", "fr": "FRANCE", "jp": "JAPAN",
    "ca": "CANADA", "sg": "SINGAPORE", "au": "AUSTRALIA",
    "fi": "FINLAND", "se": "SWEDEN", "no": "NORWAY",
    "in": "INDIA", "br": "BRAZIL", "ru": "RUSSIA",
    "kr": "SOUTH KOREA", "hk": "HONG KONG", "tw": "TAIWAN",
    "tr": "TURKEY", "ae": "UAE", "pl": "POLAND",
}

def guess_country(text):
    text = text.lower()
    for code, name in COUNTRY_MAP.items():
        if code in text or name.lower() in text:
            return code, name
    return "un", "UNKNOWN"

# ======================
# PING CHECK
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
            host, port = host_port.rsplit(':', 1)
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
# SCRAPE SOURCES
# ======================
def scrape_site(url):
    print(f"Scraping: {url}")
    nodes = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        text = r.text

        # Find all VPN config links
        configs = re.findall(
            r'(ss://[^\s\'"<>]+|hy2://[^\s\'"<>]+|vless://[^\s\'"<>]+|vmess://[^\s\'"<>]+|trojan://[^\s\'"<>]+)',
            text
        )

        for config in configs:
            fragment = config.split('#')[-1] if '#' in config else config
            code, name = guess_country(fragment + config)
            nodes.append({
                "name": name,
                "config": config,
                "countryCode": code
            })

        # Also check linked pages (pagination / per-post pages)
        soup = BeautifulSoup(text, 'html.parser')
        sub_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(kw in href for kw in ['key', 'vpn', 'proxy', 'server', 'node', 'ss', 'vless']):
                if href.startswith('http'):
                    sub_links.add(href)
                elif href.startswith('/'):
                    base = url.rstrip('/')
                    sub_links.add(base + href)

        for sub in list(sub_links)[:10]:  # limit sub-pages
            try:
                sr = requests.get(sub, headers=HEADERS, timeout=8)
                sub_configs = re.findall(
                    r'(ss://[^\s\'"<>]+|hy2://[^\s\'"<>]+|vless://[^\s\'"<>]+|vmess://[^\s\'"<>]+|trojan://[^\s\'"<>]+)',
                    sr.text
                )
                for config in sub_configs:
                    fragment = config.split('#')[-1] if '#' in config else config
                    code, name = guess_country(fragment + config)
                    nodes.append({
                        "name": name,
                        "config": config,
                        "countryCode": code
                    })
            except:
                continue

    except Exception as e:
        print(f"Error scraping {url}: {e}")

    print(f"  Found {len(nodes)} configs from {url}")
    return nodes

# ======================
# MULTITHREAD CHECK
# ======================
def filter_alive(nodes):
    alive = []
    def check(node):
        if is_alive(node.get("config")):
            return node
        return None
    with ThreadPoolExecutor(max_workers=30) as executor:
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

    try:
        with open(file_path, "r") as f:
            current = json.load(f)
    except:
        current = []

    print(f"Existing servers: {len(current)}")

    # Step 1: Remove dead existing servers
    print("Checking existing servers...")
    current = filter_alive(current)
    print(f"Alive existing: {len(current)}")

    # Step 2: Scrape new servers from sources
    new_nodes = []
    for source in SOURCES:
        new_nodes += scrape_site(source)

    print(f"Scraped total: {len(new_nodes)}")

    # Step 3: Check new servers alive
    alive_new = filter_alive(new_nodes)
    print(f"Alive new: {len(alive_new)}")

    current += alive_new

    # Step 4: Deduplicate
    unique = {}
    for s in current:
        key = s.get("config", "").split('#')[0]  # ignore fragment for dedup
        if key:
            unique[key] = s

    final = list(unique.values())
    print(f"Final unique servers: {len(final)}")

    # Step 5: Save
    if final:
        with open(file_path, "w") as f:
            json.dump(final, f, indent=2)
        print(f"Saved {len(final)} servers.")
    else:
        print("No valid servers found, keeping old file.")

if __name__ == "__main__":
    main()
