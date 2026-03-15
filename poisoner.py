#!/usr/bin/env python3
"""
poisoner.py — The Honeytoken Generator
Part of: The Poisoned JSON project
Author: You (guided by Senior Security Engineer AI)

Usage:
    python3 poisoner.py

What it does:
    Generates realistic fake credential JSON files with embedded
    canary URLs. When a hacker tries to use these credentials,
    your Vercel listener captures their info and alerts you on Discord.
"""

import json
import os
import random
import string
import datetime

# ============================================================
#  CONFIGURATION — Edit these before running
# ============================================================

# Your deployed Vercel URL
VERCEL_URL = "https://poisoned-json.vercel.app"

# ISOLATED: Only targets the victim_lab folder.
# poisoner.py will ONLY read/write inside this single directory.
# Nothing else in C:/CyberSecurity is touched.
TARGET_DIRS = [
    "/mnt/c/CyberSecurity/Poisoned-JSON-Project/victim_lab"
]

# Which honeytoken types to generate per directory
# Options: "firebase", "aws", "stripe"
TOKENS_TO_GENERATE = ["firebase", "aws", "stripe"]

# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def random_hex(length):
    """Generate a random hex string of given length."""
    return ''.join(random.choices(string.hexdigits[:16], k=length))

def random_b64_chunk(length):
    """Fake a base64-looking chunk (for private keys etc.)."""
    chars = string.ascii_letters + string.digits + '+/'
    return ''.join(random.choices(chars, k=length))

def make_token_id(prefix):
    """
    Create a unique token ID like FB001, AWS002.
    Uses a random 3-digit number so each scattered file is unique.
    """
    number = random.randint(100, 999)
    return f"{prefix}{number}"

def canary_url(token_id, svc):
    """Build the canary URL that phones home when accessed."""
    return f"{VERCEL_URL}/api/ping?token={token_id}&svc={svc}"

def fake_date(years_ago_range=(0, 2)):
    """Generate a realistic-looking past date string."""
    days_back = random.randint(years_ago_range[0] * 365, years_ago_range[1] * 365)
    dt = datetime.datetime.now() - datetime.timedelta(days=days_back)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# ============================================================
#  HONEYTOKEN GENERATORS
# ============================================================

def generate_firebase(token_id):
    """Generate a realistic Firebase service account JSON."""
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
        # ← THE TRAP: Firebase SDKs call token_uri during authentication
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
    """Generate a realistic AWS credentials JSON."""
    # AWS access keys always start with AKIA
    fake_access_key = "AKIA" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    fake_secret = random_b64_chunk(40)

    data = {
        "aws_access_key_id": fake_access_key,
        "aws_secret_access_key": fake_secret,
        "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
        "output": "json",
        # ← THE TRAP: endpoint_url overrides the default AWS endpoint
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
    """Generate a realistic Stripe keys JSON."""
    # Stripe keys have a recognisable format
    pk = "pk_live_51" + random_b64_chunk(48)
    sk = "sk_live_51" + random_b64_chunk(48)
    wh = "whsec_" + random_b64_chunk(32)

    data = {
        "environment": "production",
        "publishable_key": pk,
        "secret_key": sk,
        "webhook_secret": wh,
        # ← THE TRAP: api_base overrides Stripe's SDK base URL
        "api_base": canary_url(token_id, "stripe"),
        "metadata": {
            "account_name": random.choice([
                "MyStartup Inc.", "Acme Corp", "DevShop Ltd", "BuildFast Co."
            ]),
            "live_mode": True,
            "created": fake_date((0, 1)),
            "note": "Production keys — rotate quarterly"
        }
    }
    return data, "stripe_keys.json"


# ============================================================
#  CORE LOGIC
# ============================================================

GENERATORS = {
    "firebase": (generate_firebase, "FB"),
    "aws":      (generate_aws,      "AWS"),
    "stripe":   (generate_stripe,   "STR"),
}

def scatter_tokens():
    """Main function — generates and writes all honeytoken files."""
    print("\n🍯  The Poisoned JSON — Honeytoken Poisoner")
    print("=" * 50)

    created_files = []

    for target_dir in TARGET_DIRS:
        # Create directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        print(f"\n📁 Target: {target_dir}")

        for token_type in TOKENS_TO_GENERATE:
            if token_type not in GENERATORS:
                print(f"  ⚠️  Unknown token type '{token_type}' — skipping")
                continue

            gen_func, prefix = GENERATORS[token_type]

            # Generate unique token ID for this specific file
            token_id = make_token_id(prefix)

            # Generate the fake credential data
            data, filename = gen_func(token_id)

            # Write to target directory
            filepath = os.path.join(target_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            created_files.append({
                "token_id": token_id,
                "file": filepath,
                "canary_url": canary_url(token_id, token_type)
            })

            print(f"  ✅ [{token_id}] {filename}")

    # Print summary
    print("\n" + "=" * 50)
    print(f"✅ Done! Created {len(created_files)} honeytoken file(s).\n")
    print("📋 Token Registry (save this!):")
    print("-" * 50)
    for entry in created_files:
        print(f"  ID       : {entry['token_id']}")
        print(f"  File     : {entry['file']}")
        print(f"  Canary   : {entry['canary_url']}")
        print()

    print("💡 Tip: Run this script again to regenerate with new token IDs.")
    print("💡 Tip: Update VERCEL_URL before running in production.\n")


# ============================================================
#  ENTRY POINT
# ============================================================

if __name__ == "__main__":
    scatter_tokens()
