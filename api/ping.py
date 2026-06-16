"""
api/ping.py — The Honeytoken Listener
Part of: The Poisoned JSON project
"""

import json
import os
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone


def get_geolocation(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,query"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                return data
    except Exception as e:
        print(f"ERROR geo lookup failed: {e}")
    return {}


def send_discord_alert(token_id, svc, ip, user_agent):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL is not set.")
        return

    geo     = get_geolocation(ip)
    city    = geo.get("city", "Unknown")
    region  = geo.get("regionName", "Unknown")
    country = geo.get("country", "Unknown")
    isp     = geo.get("isp", "Unknown")
    org     = geo.get("org", "Unknown")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    payload = {
        "content": (
            f"🚨 **Honeytoken Triggered!**\n"
            f"**Token:** `{token_id}`\n"
            f"**Service:** `{svc}`\n\n"
            f"🌐 **IP:** `{ip}`\n"
            f"📍 **Location:** {city}, {region}, {country}\n"
            f"🏢 **ISP:** {isp}\n"
            f"🏛️ **Org:** {org}\n\n"
            f"💻 **User-Agent:** `{user_agent[:150]}`\n"
            f"🕐 **Time:** {timestamp}"
        )
    }

    data = json.dumps(payload).encode("utf-8")
    url  = webhook_url + "?wait=true"
    req  = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; HoneytokenBot/1.0)"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    except urllib.error.HTTPError as e:
        print(f"ERROR HTTPError {e.code}: {e.reason} | {e.read().decode()}")
    except urllib.error.URLError as e:
        print(f"ERROR URLError: {e.reason}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def _handle_request(self):
        parsed   = urlparse(self.path)
        params   = parse_qs(parsed.query)
        token_id = params.get("token", ["UNKNOWN"])[0]
        svc      = params.get("svc",   ["unknown"])[0]

        ip = (
            self.headers.get("x-forwarded-for")
            or self.headers.get("x-real-ip")
            or "unknown"
        )
        ip = ip.split(",")[0].strip()

        user_agent = self.headers.get("user-agent", "unknown")

        send_discord_alert(token_id, svc, ip, user_agent)

        self.send_response(403)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": "invalid_grant",
            "error_description": "Invalid credentials or token has been revoked."
        }).encode("utf-8"))

    def log_message(self, format, *args):
        pass