import json

print("TEST RUN STARTED")

data = {
    "name": "LIONX TEST VPN",
    "status": "testing",
    "servers": [
        {
            "country": "Pakistan",
            "ip": "1.1.1.1",
            "protocol": "WireGuard",
            "status": "online"
        },
        {
            "country": "USA",
            "ip": "8.8.8.8",
            "protocol": "OpenVPN",
            "status": "online"
        }
    ]
}

with open("services.json", "w") as f:
    json.dump(data, f, indent=4)

print("TEST COMPLETE - FILE UPDATED")
