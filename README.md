# Saudi Arabia Lead Intelligence System

AI-powered system that finds Saudi businesses needing digital services
and generates outreach-ready leads with AI sales pitches.

---

## Quick Setup

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Get your API keys

| Key | Where to get it | Cost |
|-----|----------------|------|
| `APIFY_API_TOKEN` | apify.com → Account → Integrations | ~$4/1000 results |
| `GROQ_API_KEY` | console.groq.com → API Keys | Near free |
| `PSI_API_KEY` | console.cloud.google.com → PageSpeed Insights API | Free (25k/day) |
| `HUNTER_API_KEY` | hunter.io → API Keys | Depends on plan |

### Step 3 — Add keys as environment variables

Do not hardcode real keys in `config.py`. Use environment variables:

```bash
export APIFY_API_TOKEN="<your-apify-token>"
export GROQ_API_KEY="<your-groq-key>"
export PSI_API_KEY="<your-google-pagespeed-key>"
export HUNTER_API_KEY="<your-hunter-key>"
```

You can copy `.env.example` to `.env` for local reference, but `.env` is ignored by Git.

### Step 4 — Run
```bash
python main.py
```

---

## Commands

| Command | What it does |
|---------|-------------|
| `python main.py` | Opens the city and industry selection menus |
| `python main.py --export-only` | Re-export CSV from existing database |
| `python main.py --report` | Print summary to terminal |
| `python main.py --top-leads 70` | Export only leads with score 70+ |

---

## Output Files

| File | Description |
|------|-------------|
| `leads.db` | SQLite database — runs, scraped businesses, actionable leads, and ignored-good audit trail |
| `leads_export_TIMESTAMP.csv` | Full CSV export of all leads |
| `top_leads_70plus_TIMESTAMP.csv` | High-priority leads only |

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `runs` | One row per pipeline run with raw scraped, wrong-type discarded, duplicate, saved, ignored, skipped, and error counts |
| `businesses` | Every verified business scraped for the chosen city + industry, even if it is not a lead |
| `leads` | Only actionable businesses worth contacting |
| `ignored_businesses` | Businesses ignored because their website passed the quality gate |

---

## Query Library

The scraper uses the EIT opportunity query library in `config.py`.
The menu is organized by product opportunity groups, not only industry.

| Tier | Opportunity Examples | Product Lines |
|------|----------------------|---------------|
| A | Construction, Engineering, Logistics, Manufacturing | Multi-product opportunities such as SSL, ERP, GPS Fleet, IoT, Computer Vision, Custom Software |
| B | Healthcare, Retail, Food & Hospitality, Professional Services | Strong single/dual-product opportunities such as SSL, SBOSS ERP, POS, AI Office Automation |
| C | Telecom, Energy, Real Estate, Security, Education, Automotive | Specialized opportunities such as monitoring, no-code apps, GPS, computer vision |

Each saved lead includes:

```text
opportunity_tier
product_lines
source_query
```

---

## File Structure

```
lead_intel/
├── main.py           Run this — orchestrates all 5 stages
├── config.py         API keys, cities, thresholds (edit before running)
├── database.py       SQLite setup and all read/write operations
├── scraper.py        Stage 1 — Apify Google Maps scraping
├── validator.py      Stage 2 — Async website validation
├── auditor.py        Stage 3 — PageSpeed Insights + HTML parsing
├── ai_engine.py      Stage 4 — Groq AI analysis + sales pitch
├── exporter.py       Stage 5 — CSV export
└── requirements.txt  Python packages to install
```

---

## Lead Score Guide

| Outcome | What happens |
|---------|-------------|
| No website | Saved to database |
| Social/directory URL only | Saved as no proper business website |
| Website unreachable | Saved to database |
| Missing HTTPS or invalid SSL | Saved to database |
| HTTPS + valid SSL but any measured score under 70% | AI analyzed and saved |
| HTTPS + valid SSL and all measured scores 70%+ with AI UI/UX 7/10+ | Ignored as good and counted in the terminal summary |

---

## Estimated Cost Per 1,000 Businesses

| Service | Cost |
|---------|------|
| Apify (Google Maps scraping) | ~$4.00 |
| PageSpeed Insights API | Free |
| Groq AI (runs on ~30% of leads) | ~$0.05 |
| **Total** | **~$4.05** |
