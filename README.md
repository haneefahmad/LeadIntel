# 🌐 Universal B2B Lead Intelligence System

> Enterprise-grade Lead Generation, Multi-Market Intelligence, and Decision-Maker Extraction Platform. Built with an industry-standard modular architecture (`backend/` + `frontend/`), supporting both an interactive Terminal CLI and an Executive Web Dashboard across any global country or region.

---

## 🏛️ Project Architecture

The system is organized into a clean, decoupled structure:

```text
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Package marker
│   │   ├── config.py             # 15 industries, dynamic geo codes, path management
│   │   ├── database.py           # SQLite persistence layer, dedup & queries
│   │   ├── scraper.py            # Apify Google Maps crawler & bilingual parser
│   │   ├── sales_nav_client.py   # LinkedIn Sales Navigator scraper & 45-column normalizer
│   │   ├── apollo_client.py      # Apollo API enrichment client
│   │   ├── contact_enricher.py   # Multi-engine contact discovery & enricher
│   │   ├── enrichment_service.py # Unified enrichment service & preview calculator
│   │   ├── dm_pipeline.py        # Executive decision maker discovery & scoring
│   │   ├── exporter.py           # Color-coded enterprise Excel & CSV generator
│   │   ├── field_presets.py      # 39-column taxonomy & default presets
│   │   ├── cli.py                # Rich + Questionary interactive terminal wizard
│   │   ├── orchestrator.py       # Multi-stage async pipeline controller
│   │   └── main.py               # FastAPI REST & SSE real-time server (serves React build)
│   ├── data/
│   │   ├── master.db             # Verified SQLite database (persistent storage)
│   │   └── MasterDB.xlsx         # Color-coded enterprise Excel export
│   └── .env                      # Backend environment configuration
├── frontend-react/               # Modern React 18 + Vite Web Dashboard
│   ├── src/
│   │   ├── api/client.js         # Centralized API & SSE client
│   │   ├── components/
│   │   │   ├── common/           # Header, ToastContainer
│   │   │   ├── pipeline/         # LeadsTable, KpiCards, PipelineToolbar, Pagination
│   │   │   ├── modals/           # DossierModal, EnrichModal, SheetsModal, ColumnsModal
│   │   │   └── views/            # PipelineView, MissionControl, AuditorView, RunLogsView, SettingsView
│   │   ├── context/              # AppContext & PipelineContext state stores
│   │   ├── index.css             # Glassmorphic dark design system
│   │   ├── App.jsx               # Root tab router & modal manager
│   │   └── main.jsx              # React DOM entry point
│   ├── dist/                     # Optimized production bundle (served by FastAPI)
│   ├── package.json
│   └── vite.config.js            # Vite configuration with proxy to FastAPI (port 8000)
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git exclusions
├── main.py                       # Root launcher for CLI Wizard
├── run_web.py                    # Root launcher for Web Dashboard & API
└── requirements.txt              # Production dependencies
```


---

## 🚀 Quick Start

### 1. Environment Setup

Make sure you are using Python 3.11+ and activate your virtual environment:

```bash
# Clone or navigate to the repository
cd "Saudi Arabia Lead Intelligence System"

# Activate the existing virtual environment (or create a new one)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` (or configure directly in the Web Dashboard UI under **Settings**):

```bash
cp .env.example .env
```

Edit `.env`:
```ini
APIFY_API_TOKEN=your_apify_token_here
LINKEDIN_COOKIE=your_li_at_cookie_here
```
> *Apify tokens can be obtained at [console.apify.com](https://console.apify.com/account/integrations).*

---

## 🖥️ Running the Application

### Option A: Executive Web Dashboard (Recommended)

Launch the FastAPI web server with automatic live reload:

```bash
python run_web.py
```

- **Dashboard UI**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Frontend Development Mode (Hot-Reloading):
For active frontend development with Vite HMR:
```bash
# In terminal 1 (Backend API):
python run_web.py

# In terminal 2 (Vite React dev server with reverse-proxy):
cd frontend-react
npm run dev
# Vite runs at http://localhost:5173 with hot reload and proxies API calls to port 8000
```


#### Key Dashboard Capabilities:
- **Master Sheet Management**: Seamlessly switch between active sheets or spin up new isolated sheets (`.db` + `.xlsx`) per campaign directly from the top bar or scraper form.
- **Mission Control**: Select target country, dynamic custom locations (cities, districts, regions), industries, and crawl depth. Watch the live terminal console stream real-time SSE progress.
- **Lead Intelligence Vault**: Search, filter by city, industry, status, presence of email/website, view paginated records, and inspect full lead detail modals.
- **Mini-CRM & Pipeline**: Update outreach statuses, assign sales reps, log deal sizes, add tags, and record PDPL opt-out suppressions.
- **KPI Metrics**: Real-time stats on company counts, website coverage %, phone %, email discovery %, and cost tracking.
- **Excel & CSV One-Click Export**: Download the active sheet's color-coded 6-sheet `MasterDB.xlsx` or CRM-compatible CSV anytime.
- **In-App Settings**: View API key status and update keys safely without touching files.

---

### Option B: Interactive Terminal CLI

Run the full interactive command-line wizard:

```bash
python main.py
```

The CLI steps through:
1. **Master Sheet / Workspace**: Choose to continue with an existing sheet or create a new sheet.
2. **Target Country**: Enter Saudi Arabia, USA, UAE, UK, or any country.
3. **Target Location(s)**: Choose presets (Riyadh, Jeddah, NEOM...) or type any custom location(s).
4. **Industries**: Select from 15 high-value B2B industry verticals (or all).
5. **Crawl Depth**: Quick Test (10), Standard (25), Deep Dive (50), or Enterprise Max (100).
6. **Cost Approval**: Review estimated cost and confirm before starting.

---

## ⚙️ Supported Industry Verticals

The system includes pre-tuned, high-precision search query clusters across 15 B2B sectors:

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

## 🔒 Data Preservation & Integrity

- **Database**: `backend/data/master.db` persists all lead intelligence with SHA-256 duplicate detection and Google Place ID uniqueness.
- **Spreadsheet**: `backend/data/MasterDB.xlsx` contains 6 formatted worksheets:
  1. *Instructions* (field definitions & PDPL rules)
  2. *Master_Database* (color-coded records with frozen headers)
  3. *Suppression_List* (opt-outs)
  4. *Apify_Run_Log* (execution audit trail)
  5. *Enrichment_Log* (manual enrichments)
  6. *Reference_Data* (lookup tables)

---

## 🛠️ Testing & Verification

Run the test suite to verify all backend modules, database records, and API endpoints:

```bash
python -c "
from backend.app import database as db
print('Total records in master.db:', db.get_total_count())
"
```
