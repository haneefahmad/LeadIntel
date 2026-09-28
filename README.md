# 🌐 LeadIntel — Universal B2B Lead Intelligence Platform

> Enterprise-grade Lead Generation, Multi-Market Intelligence, and Decision-Maker Extraction Platform. Built with an asynchronous **FastAPI backend** and a high-performance **React 18 (Vite) Single-Page Application**, backed by a **SQLAlchemy Universal Database Layer** supporting SQLite, PostgreSQL, MySQL, and cloud databases.

---

## 🏛️ Project Architecture

```text
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Package marker
│   │   ├── config.py             # 15 industries, dynamic geo codes, path management
│   │   ├── database.py           # Universal SQLAlchemy DB layer (SQLite WAL, PostgreSQL, MySQL)
│   │   ├── scraper.py            # Apify Google Maps crawler & bilingual Arabic/English parser
│   │   ├── apollo_client.py      # Apollo.io API client for verified decision makers & emails
│   │   ├── contact_enricher.py   # Web scraper for contact discovery (email/phone)
│   │   ├── enrichment_service.py # Non-destructive enrichment engine & credit optimizer
│   │   ├── exporter.py           # Custom XLSX and streaming CSV generator
│   │   ├── field_presets.py      # Canonical 39-column taxonomy & field mapping presets
│   │   ├── geo_data.py           # Country, state, and city hierarchical taxonomy
│   │   └── main.py               # FastAPI REST & SSE server (serves production React bundle)
│   └── data/                     # Local storage directory (git-ignored)
├── frontend-react/               # Modern React 18 + Vite Web Dashboard
│   ├── src/
│   │   ├── api/client.js         # Centralized API & SSE stream client
│   │   ├── components/
│   │   │   ├── common/           # Header (Theme Toggle, Server Stop), ToastContainer
│   │   │   ├── pipeline/         # LeadsTable, KpiCards, PipelineToolbar, Pagination
│   │   │   ├── modals/           # DossierModal, EnrichModal, SheetsModal, ColumnsModal, SettingsModal
│   │   │   ├── settings/         # DatabaseConfigCard (Postgres/MySQL/SQLite switcher)
│   │   │   └── views/            # PipelineView, MissionControl, AuditorView, RunLogsView
│   │   ├── context/              # AppContext (Theme, Sheets) & PipelineContext state stores
│   │   ├── index.css             # Dual-theme tokenized design system (Light & Dark modes)
│   │   ├── App.jsx               # Root router and modal manager
│   │   └── main.jsx              # React DOM entry point
│   ├── dist/                     # Pre-compiled production bundle (served directly by FastAPI)
│   ├── package.json
│   └── vite.config.js            # Vite configuration with proxy to FastAPI (port 8000)
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git exclusions (*.db, *.xlsx, .env protected)
├── main.py                       # Root launcher (starts Web Dashboard & API)
├── run_web.py                    # Dedicated launcher with port monitoring and stop flag
└── requirements.txt              # Production Python dependencies
```

---

## 🚀 Quick Start

### 1. Environment Setup

Python 3.11+ is recommended. Activate your virtual environment:

```bash
# Clone or navigate to the repository
cd LeadIntel

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` (or configure directly in the Web Dashboard under **Settings**):

```bash
cp .env.example .env
```

Edit `.env`:
```ini
# Scraping & Enrichment API Keys
APIFY_API_TOKEN=your_apify_token_here
APOLLO_API_KEY=your_apollo_api_key_here

# Universal Database (Optional - defaults to local embedded SQLite)
# DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/leadintel
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/leadintel
```

> **API Credentials**:
> * **Apify Token**: Required for Google Places lead extraction ([console.apify.com](https://console.apify.com/account/integrations)).
> * **Apollo.io API Key**: Required for B2B decision-maker and verified email enrichment ([apollo.io](https://app.apollo.io/#/settings/integrations/api)).

---

## 🖥️ Running the Application

### Starting the Dashboard

Launch the application using either launcher:

```bash
python main.py
# or
python run_web.py
```

* **Dashboard UI**: [http://localhost:8000](http://localhost:8000)
* **Interactive OpenAPI/Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Stopping the Server

You can stop the server and release port 8000 at any time:
* **Via Web UI**: Click the red **Stop Server** button in the top header.
* **Via Terminal**: Run `python run_web.py --stop`

---

## 💻 Frontend Development Mode (Hot-Reloading)

To make live frontend code changes with Vite HMR:

```bash
# Terminal 1: Backend API
python run_web.py

# Terminal 2: React Vite dev server
cd frontend-react
npm run dev
# Access http://localhost:5173 with instant Hot Module Replacement (HMR)
```

To build production assets served by FastAPI:
```bash
cd frontend-react && npm run build
```

---

## 🌟 Key Capabilities

1. **Mission Control (Lead Scraper)**:
   * Select target country, dynamic custom locations (cities, regions, provinces), industries, and crawl limit.
   * Real-time Server-Sent Events (SSE) stream execution logs live directly into the console drawer.
   * Bilingual normalization: Automatically separates Latin and Arabic business titles cleanly.

2. **Decision-Maker & Email Enrichment (Apollo.io)**:
   * Enriches leads with verified C-level Decision Makers (CEO, Founder, Managing Director, VP).
   * **Credit Optimization**: Automatically detects existing contact information and only queries Apollo for missing data, preventing wasted API credits.

3. **Universal Database Layer**:
   * Out of the box: Embedded SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) for high concurrency.
   * Instant database connection: Connect to PostgreSQL, MySQL, Supabase, Neon, or AWS RDS via the in-app Settings modal or `DATABASE_URL`.
   * Strict non-destructive merge semantics: Existing records and manual edits are never overwritten.

4. **Multi-Sheet Campaign Workspaces**:
   * Switch between isolated client campaigns directly from the header dropdown.
   * Create or delete workspaces on the fly.

5. **Dual-Theme Design System**:
   * Toggle between **Dark Mode** (Linear/Vercel slate theme) and **Light Mode** (high-contrast crisp theme) with one click in the header or settings.
   * Automatically remembers preference in `localStorage` with OS `prefers-color-scheme` fallback.

6. **Lead Intelligence Vault & Mini-CRM**:
   * Search and filter by city, industry, presence of verified email, website, phone, and outreach status.
   * Full lead dossier modal showing all 39 standardized firmographic and CRM fields.
   * Update outreach statuses, assign sales owners, add tags, and record opt-out suppressions.

7. **Custom XLSX & Streaming CSV Export**:
   * Download datasets with visible columns or export full 39-column dossiers.
   * Streaming CSV responses prevent memory exhaustion on large datasets.

---

## ⚙️ Supported Industry Verticals

Pre-tuned, high-precision search query clusters across 15 B2B sectors:

1. **Staffing & Recruitment** (HR consultancy, headhunters, executive search)
2. **IT & Technology Solutions** (software houses, cloud providers, ERP, cyber security)
3. **Business & Management Consulting** (corporate advisory, strategy consulting)
4. **Manufacturing & Industrial** (plants, factories, heavy equipment)
5. **Logistics, Freight & Supply Chain** (3PL, customs clearance, warehousing)
6. **Banking, Financial Services & Insurance (BFSI)** (fintech, investment banking)
7. **Legal, Audit & Professional Services** (law firms, tax advisory)
8. **Construction & Civil Contracting** (general contractors, EPC firms)
9. **Facility Management & Operations** (commercial cleaning, HVAC, security)
10. **Healthcare, Clinics & Medical Supplies** (polyclinics, medical devices)
11. **Hospitality, Tourism & Catering** (business hotels, corporate event catering)
12. **Real Estate & Property Development** (commercial real estate, asset management)
13. **Marketing, Advertising & Media** (digital marketing, PR agencies)
14. **Education, EdTech & Corporate Training** (professional academies)
15. **Oil, Gas & Energy Services** (drilling contractors, petroleum engineering)

---

## 🛠️ Testing & Verification

Run backend sanity verification:

```bash
python -c "
from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)
res = client.get('/api/settings')
assert res.status_code == 200
print('Backend API is healthy:', res.json())
"
```
