# 🍯 The Poisoned JSON — Honeytoken Deception System

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?logo=vercel)
![Discord](https://img.shields.io/badge/Alerts-Discord-5865F2?logo=discord)
![Doppler](https://img.shields.io/badge/Secrets-Doppler-800080?logo=doppler)
![License](https://img.shields.io/badge/License-MIT-green)

A deception-based **honeytoken system** for detecting unauthorized access to credential files. Built as a cybersecurity portfolio project demonstrating threat deception, serverless architecture, secrets management, and real-time alerting.

---

## 🎯 Real-World Detection

Within hours of deployment, the system autonomously detected a real automated credential scanner:

| Field | Value |
|-------|-------|
| **IP** | `3.224.234.70` |
| **Location** | Ashburn, Virginia, United States |
| **ISP** | Amazon Technologies Inc. |
| **Org** | AWS EC2 (us-east-1) |
| **User-Agent** | `Mozilla/5.0 (compatible)` |
| **Time** | 2026-03-16 05:33:14 UTC |

> An automated AWS-hosted bot probed the honeytoken endpoint within hours of the repository going public — confirming the system works against real-world credential scanners with zero manual intervention.

---

## 📖 What Is A Honeytoken?

A honeytoken is a fake credential or resource deliberately planted in a system. It has no legitimate use — so any interaction with it is an immediate indicator of compromise (IoC). This technique is used by security teams at major companies to detect insider threats, credential theft, and automated scanners.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                LOCAL MACHINE (WSL)                   │
│                                                     │
│  poisoner.py                                        │
│  ├── Generates fake .json credential files          │
│  ├── Embeds unique canary URLs per file             │
│  └── Scatters files into target directories         │
└──────────────────────┬──────────────────────────────┘
                       │  e.g. token_uri, endpoint_url
                       ▼
┌─────────────────────────────────────────────────────┐
│              VERCEL (Serverless Function)            │
│                                                     │
│  /api/ping.py                                       │
│  ├── Receives request from attacker/bot             │
│  ├── Captures IP, User-Agent, headers               │
│  ├── Geolocates IP (city, ISP, country)             │
│  └── Fires Discord alert via webhook                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                  DISCORD WEBHOOK                     │
│                                                     │
│  #honeytoken-alerts                                 │
│  └── Rich alert: IP, location, ISP, UA, token ID   │
└─────────────────────────────────────────────────────┘
```

---

## ✨ Features

- 🎭 **Realistic fake credentials** — Firebase, AWS, and Stripe JSON files that look genuine
- 🪤 **Unique token IDs** — each planted file has a unique ID so you know exactly which file was triggered
- 🌐 **IP capture** — logs the attacker's real public IP via `x-forwarded-for`
- 📍 **Geolocation** — resolves IP to city, region, country, ISP and org
- 🔔 **Instant Discord alerts** — real-time notifications with full attacker context
- 🔒 **Secrets management** — Discord webhook URL managed via Doppler, never hardcoded
- 📦 **Zero dependencies** — Python standard library only (`json`, `os`, `urllib`, `datetime`)
- ⚡ **Serverless** — Vercel cold-start in milliseconds, scales infinitely

---

## 📁 Project Structure

```
poisoned-json/
├── poisoner.py          # Local script — generates & scatters fake credential files
├── vercel.json          # Vercel deployment configuration
├── README.md            # This file
└── api/
    └── ping.py          # Vercel serverless function — the trap listener
```

---

## 🪤 Honeytoken File Types

| File | Canary Field | Why It Fires |
|------|-------------|--------------|
| `firebase-service-account.json` | `token_uri` | Firebase SDKs call this during authentication |
| `aws_creds.json` | `endpoint_url` | AWS CLI/SDK uses this to override the default endpoint |
| `stripe_keys.json` | `api_base` | Stripe SDK uses this as the base API URL |

---

## 🚀 Setup & Deployment

### Prerequisites
- WSL (Ubuntu) with Python 3
- Node.js v20+ (for Vercel CLI)
- Vercel account (free)
- Doppler account (free)
- Discord server with a webhook

### 1. Clone The Repo
```bash
git clone https://github.com/yourusername/poisoned-json.git
cd poisoned-json
```

### 2. Set Up Doppler
```bash
# Create a Doppler project called 'poisoned-json'
# Add secret: DISCORD_WEBHOOK_URL = your Discord webhook URL
# Connect Doppler → Vercel via Doppler dashboard Syncs
```

### 3. Deploy To Vercel
```bash
npm install -g vercel
vercel login
vercel --prod
```

### 4. Configure The Poisoner
Edit `poisoner.py` and update:
```python
VERCEL_URL = "https://your-app.vercel.app"
TARGET_DIRS = ["/path/to/your/target/directory"]
```

### 5. Generate Honeytokens
```bash
python3 poisoner.py
```

### 6. Test The Trap
```bash
curl "https://your-app.vercel.app/api/ping?token=TEST001&svc=aws"
```

Check your Discord — you should receive an alert instantly.

---

## 📬 Discord Alert Example

```
🚨 Honeytoken Triggered!
Token: AWS293
Service: aws

🌐 IP: 103.x.x.x
📍 Location: Mumbai, Maharashtra, India
🏢 ISP: Reliance Jio Infocomm
🏛️ Org: AS55836 Reliance Jio

💻 User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0...)
🕐 Time: 2026-03-15 18:21:33 UTC
```

---

## 🔐 Security Design Decisions

| Decision | Rationale |
|----------|-----------|
| Returns `403 invalid_grant` | Looks like a real auth rejection — doesn't tip off the attacker |
| `?wait=true` on webhook URL | Bypasses Cloudflare bot protection on Discord's CDN |
| Doppler for secrets | Webhook URL never touches the codebase or git history |
| Unique token IDs | Identifies exactly which file was triggered and where it was planted |
| Zero dependencies | No supply chain attack surface — pure stdlib only |

---

## ⚖️ Legal & Ethical Notice

> Honeytokens are a legal and widely accepted defensive security technique.
> This project must **only** be deployed on systems you own or have explicit written authorization to monitor.
> Unauthorized deployment on systems you do not own may violate computer fraud laws in your jurisdiction.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Honeytoken Generator | Python 3 (stdlib only) |
| Trap Listener | Python 3 on Vercel Serverless |
| Secrets Management | Doppler |
| Alerting | Discord Webhooks |
| Geolocation | ip-api.com (free tier) |
| Deployment | Vercel CLI |

---

## 📚 References & Further Reading

- [Canarytokens by Thinkst](https://canarytokens.org) — industry standard honeytoken service
- [MITRE ATT&CK T1056](https://attack.mitre.org/techniques/T1056/) — credential access techniques
- [Vercel Python Serverless Functions](https://vercel.com/docs/functions/runtimes/python)
- [Doppler Secrets Manager](https://doppler.com)

---

*Built as a cybersecurity portfolio project. Demonstrates: threat deception, serverless architecture, secrets management, and real-time incident alerting.*
