#!/usr/bin/env python3
"""
poisoner.py — The Honeytoken Generator
Part of: The Poisoned JSON project

Usage:
    python3 poisoner.py
"""

import json
import os
import random
import string
import datetime

# ============================================================
#  CONFIGURATION
# ============================================================

VERCEL_URL = "https://poisoned-json.vercel.app"

TARGET_DIRS = [
    "/mnt/c/CyberSecurity/Poisoned-JSON-Project/victim_lab"
]

TOKENS_TO_GENERATE = ["firebase", "aws", "stripe"]

# Registry saves here — outside victim_lab, never committed
REGISTRY_PATH = os.path.expanduser("~/honeytoken_registry.json")

# ============================================================
#  HELPERS
# ============================================================

def random_hex(length):
    return ''.join(random.choices(string.hexdigits[:16], k=length))

def random_b64_chunk(length):
    chars = string.ascii_letters + string.digits + '+/'
    return ''.join(random.choices(chars, k=length))

def make_token_id(prefix):
    return f"{prefix}{random.randint(100, 999)}"

def canary_url(token_id, svc):
    return f"{VERCEL_URL}/api/ping?token={token_id}&svc={svc}"

def fake_date(years_ago_range=(0, 2)):
    days_back = random.randint(years_ago_range[0] * 365, years_ago_range[1] * 365)
    dt = datetime.datetime.now() - datetime.timedelta(days=days_back)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# ============================================================
#  GENERATORS
# ============================================================

def generate_firebase(token_id):
    project_id = f"myapp-prod-{random_hex(5)}"
    uid = random_hex(8)
    data = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": random_hex(40),
        "private_key": (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            + random_b64_chunk(64) + "\n"
            + random_b64_chunk(64) + "\n"
            + random_b64_chunk(64) + "\n"
            + "-----END RSA PRIVATE KEY-----\n"
        ),
        "client_email": f"firebase-adminsdk-{uid[:6]}@{project_id}.iam.gserviceaccount.com",
        "client_id": str(random.randint(10**17, 10**18 - 1)),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": canary_url(token_id, "firebase"),
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": (
            f"https://www.googleapis.com/robot/v1/metadata/x509/"
            f"firebase-adminsdk-{uid[:6]}%40{project_id}.iam.gserviceaccount.com"
        ),
        "universe_domain": "googleapis.com"
    }
    return data, "firebase-service-account.json"


def generate_aws(token_id):
    fake_access_key = "AKIA" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    data = {
        "aws_access_key_id": fake_access_key,
        "aws_secret_access_key": random_b64_chunk(40),
        "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
        "output": "json",
        "endpoint_url": canary_url(token_id, "aws"),
        "metadata": {
            "account_id": str(random.randint(10**11, 10**12 - 1)),
            "iam_user": random.choice(["deploy-bot", "ci-runner", "prod-deploy", "github-actions"]),
            "created": fake_date((0, 2)),
            "note": "CI/CD deployment credentials — do not share"
        }
    }
    return data, "aws_creds.json"


def generate_stripe(token_id):
    data = {
        "environment": "production",
        "publishable_key": "pk_live_51" + random_b64_chunk(48),
        "secret_key": "sk_live_51" + random_b64_chunk(48),
        "webhook_secret": "whsec_" + random_b64_chunk(32),
        "api_base": canary_url(token_id, "stripe"),
        "metadata": {
            "account_name": random.choice([
                "MyStartup Inc.", "Acme Corp", "DevShop Ltd.", "BuildFast Co."
            ]),
            "live_mode": True,
            "created": fake_date((0, 1)),
            "note": "Production keys — rotate quarterly"
        }
    }
    return data, "stripe_keys.json"


# ============================================================
#  CORE
# ============================================================

GENERATORS = {
    "firebase": (generate_firebase, "FB"),
    "aws":      (generate_aws,      "AWS"),
    "stripe":   (generate_stripe,   "STR"),
}

def load_registry():
    """Load existing registry or return empty list."""
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    return []

def save_registry(entries):
    """Save registry to JSON file."""
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(entries, f, indent=2)

def scatter_tokens():
    print("\n🍯  The Poisoned JSON — Honeytoken Poisoner")
    print("=" * 50)

    created_files = []

    for target_dir in TARGET_DIRS:
        os.makedirs(target_dir, exist_ok=True)
        print(f"\n📁 Target: {target_dir}")

        for token_type in TOKENS_TO_GENERATE:
            if token_type not in GENERATORS:
                print(f"  ⚠️  Unknown token type '{token_type}' — skipping")
                continue

            gen_func, prefix = GENERATORS[token_type]
            token_id = make_token_id(prefix)
            data, filename = gen_func(token_id)
            filepath = os.path.join(target_dir, filename)

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            entry = {
                "token_id": token_id,
                "service": token_type,
                "file": filepath,
                "canary_url": canary_url(token_id, token_type),
                "planted_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            created_files.append(entry)
            print(f"  ✅ [{token_id}] {filename}")

    # ── Save registry ──────────────────────────────────────
    existing = load_registry()
    existing.extend(created_files)
    save_registry(existing)

    # ── Summary ────────────────────────────────────────────
    print("\n" + "=" * 50)
    print(f"✅ Done! Created {len(created_files)} honeytoken file(s).\n")
    print("📋 Token Registry (save this!):")
    print("-" * 50)
    for entry in created_files:
        print(f"  ID       : {entry['token_id']}")
        print(f"  File     : {entry['file']}")
        print(f"  Canary   : {entry['canary_url']}")
        print(f"  Planted  : {entry['planted_at']}")
        print()
    print(f"💾 Registry saved to: {REGISTRY_PATH}\n")


if __name__ == "__main__":
    scatter_tokens()