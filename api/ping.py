"""
api/ping.py — The Honeytoken Listener
Part of: The Poisoned JSON project

Deployed on Vercel as a serverless function.
Endpoint: https://poisoned-json.vercel.app/api/ping

Triggered when an attacker tries to use a fake credential file.
Captures their IP, User-Agent, and headers, then fires a Discord alert.

No third-party libraries — uses only Python stdlib + urllib.
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone


# ============================================================
#  DISCORD ALERT BUILDER
# ============================================================

def build_discord_embed(token_id, svc, ip, user_agent, headers, method):
    """
    Build a rich Discord embed payload.
    Returns a JSON-serializable dict ready to POST to the webhook.
    """

    # Colour per service type (Discord uses decimal colour codes)
    colours = {
        "firebase": 0xFFA000,   # amber
        "aws":      0xFF9900,   # AWS orange
        "stripe":   0x6772E5,   # Stripe purple
    }
    colour = colours.get(svc, 0xFF0000)  # default red

    # Format headers into a readable string, skip noisy ones
    skip_headers = {"host", "connection", "accept-encoding"}
    header_lines = "\n".join(
        f"`{k}`: {v}"
        for k, v in headers.items()
        if k.lower() not in skip_headers
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    embed = {
        "username": "🍯 HoneyToken Alert",
        "embeds": [
            {
                "title": f"🚨 Canary Triggered — {token_id}",
                "description": (
                    f"A honeytoken was accessed. "
                    f"Someone tried to use a **{svc.upper()}** fake credential."
                ),
                "color": colour,
                "fields": [
                    {
                        "name": "🪤 Token ID",
                        "value": f"`{token_id}`",
                        "inline": True
                    },
                    {
                        "name": "🔧 Service",
                        "value": f"`{svc}`",
                        "inline": True
                    },
                    {
                        "name": "🌐 IP Address",
                        "value": f"`{ip}`",
                        "inline": True
                    },
                    {
                        "name": "🕵️ Method",
                        "value": f"`{method}`",
                        "inline": True
                    },
                    {
                        "name": "💻 User-Agent",
                        "value": f"`{user_agent[:200]}`"  # cap length
                    },
                    {
                        "name": "📋 Headers",
                        "value": header_lines[:1000] if header_lines else "`none`"
                    },
                    {
                        "name": "🕐 Timestamp",
                        "value": timestamp
                    }
                ],
                "footer": {
                    "text": "The Poisoned JSON — Honeytoken System"
                }
            }
        ]
    }
    return embed


def send_discord_alert(embed_payload):
    """
    POST the embed to Discord via webhook.
    Uses only urllib — no requests library needed.
    Returns True on success, False on failure.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL env var is not set.")
        return False

    data = json.dumps(embed_payload).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 204  # Discord returns 204 No Content on success
    except Exception as e:
        print(f"ERROR sending Discord alert: {e}")
        return False


# ============================================================
#  VERCEL HANDLER
# ============================================================

class handler(BaseHTTPRequestHandler):
    """
    Vercel Python serverless functions must define a class called 'handler'
    that extends BaseHTTPRequestHandler.
    """

    def do_GET(self):
        self._handle_request("GET")

    def do_POST(self):
        self._handle_request("POST")

    def _handle_request(self, method):
        # ── 1. Parse query params ──────────────────────────────
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        token_id = params.get("token", ["UNKNOWN"])[0]
        svc      = params.get("svc",   ["unknown"])[0]

        # ── 2. Extract attacker info ───────────────────────────
        # Vercel passes the real client IP in x-forwarded-for
        ip = (
            self.headers.get("x-forwarded-for")
            or self.headers.get("x-real-ip")
            or self.client_address[0]
            or "unknown"
        )
        # Take only the first IP if there's a chain (proxies add more)
        ip = ip.split(",")[0].strip()

        user_agent = self.headers.get("user-agent", "unknown")

        # Collect all headers as a plain dict
        headers_dict = dict(self.headers)

        # ── 3. Fire Discord alert ──────────────────────────────
        embed = build_discord_embed(token_id, svc, ip, user_agent, headers_dict, method)
        send_discord_alert(embed)

        # ── 4. Return a convincing fake error response ─────────
        # Don't return 200 — that looks suspicious to an attacker.
        # A 403 or 401 looks like a real auth service rejecting bad creds.
        self.send_response(403)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        fake_error = json.dumps({
            "error": "invalid_grant",
            "error_description": "Invalid credentials or token has been revoked."
        })
        self.wfile.write(fake_error.encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress default BaseHTTPRequestHandler console logs on Vercel
        pass
