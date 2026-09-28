"""
Business Lead Generator — Master Data Scraper
backend/app/config.py: central settings, paths, industry map, dynamic city codes.
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import re

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
BACKEND_DIR = _HERE.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load environment from root .env or backend/.env
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")

DB_PATH = str(DATA_DIR / "master.db")
XLSX_PATH = str(DATA_DIR / "MasterDB.xlsx")
MASTERDATABASE_DIR = DATA_DIR  # Alias for backward compatibility

# ── Universal Database Connection (Supports SQLite, PostgreSQL, MySQL, etc.) ──
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def get_database_url(sheet_name: str | None = None) -> str:
    """
    Returns the active database connection URL.
    If DATABASE_URL is set (e.g. PostgreSQL, MySQL), returns that URL.
    Otherwise defaults to local SQLite file for the given sheet (or active sheet).
    """
    if DATABASE_URL:
        return DATABASE_URL
    target_sheet = sheet_name or CURRENT_SHEET_NAME
    p, _ = get_sheet_paths(target_sheet)
    return f"sqlite:///{p}"


def is_sqlite() -> bool:
    """Returns True if the current active database is an embedded SQLite database."""
    url = get_database_url().lower()
    return url.startswith("sqlite")


def get_database_type() -> str:
    """Returns the type/engine name of the active database (e.g. 'sqlite', 'postgresql', 'mysql')."""
    url = get_database_url().lower()
    if url.startswith("postgres"):
        return "postgresql"
    if url.startswith("mysql") or url.startswith("mariadb"):
        return "mysql"
    if url.startswith("sqlite"):
        return "sqlite"
    if url.startswith("mssql"):
        return "mssql"
    if url.startswith("oracle"):
        return "oracle"
    return "custom"


def mask_database_url(url: str | None = None) -> str:
    """Masks database user password for secure display in UI and API responses."""
    target = url or get_database_url()
    if not target:
        return "sqlite:///master.db (Default)"
    if target.startswith("sqlite:///"):
        # Show clean filename for sqlite
        return f"sqlite://.../{Path(target.replace('sqlite:///', '')).name}"
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(target)
        if parsed.password:
            netloc = f"{parsed.username}:••••••••@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse(parsed._replace(netloc=netloc))
        return target
    except Exception:
        return "Configured Database"


def set_database_url(new_url: str) -> None:
    """Updates the active DATABASE_URL in memory."""
    global DATABASE_URL
    DATABASE_URL = (new_url or "").strip()


# ── Multi-Sheet / Workspace Management ─────────────────────────────────────────
DEFAULT_SHEET_NAME = "MasterDB"
CURRENT_SHEET_NAME = DEFAULT_SHEET_NAME


def clean_sheet_name(raw_name: str) -> str:
    """Sanitize sheet name to safe alphanumeric characters and underscores."""
    cleaned = re.sub(r'[^\w\-]', '_', (raw_name or "").strip()).strip('_')
    if not cleaned or cleaned.lower() in ("master", "masterdb", "default"):
        return DEFAULT_SHEET_NAME
    return cleaned


def get_sheet_paths(sheet_name: str) -> tuple[Path, Path]:
    """Returns (db_path, xlsx_path) for a given sheet name."""
    clean = clean_sheet_name(sheet_name)
    if clean == DEFAULT_SHEET_NAME:
        return DATA_DIR / "master.db", DATA_DIR / "MasterDB.xlsx"
    return DATA_DIR / f"{clean}.db", DATA_DIR / f"{clean}.xlsx"


def get_sheet_db_path(sheet_name: str) -> Path:
    """Returns db_path for a given sheet name."""
    return get_sheet_paths(sheet_name)[0]


def get_sheet_xlsx_path(sheet_name: str) -> Path:
    """Returns xlsx_path for a given sheet name."""
    return get_sheet_paths(sheet_name)[1]


def set_active_sheet(sheet_name: str) -> str:
    """Sets the active master sheet and updates global DB_PATH and XLSX_PATH."""
    global CURRENT_SHEET_NAME, DB_PATH, XLSX_PATH
    clean = clean_sheet_name(sheet_name)
    CURRENT_SHEET_NAME = clean
    db_p, xlsx_p = get_sheet_paths(clean)
    DB_PATH = str(db_p)
    XLSX_PATH = str(xlsx_p)
    return CURRENT_SHEET_NAME


def get_active_sheet() -> str:
    """Returns the current active sheet name."""
    return CURRENT_SHEET_NAME


def list_available_sheets() -> list[dict]:
    """Scans for all available master sheet databases and returns metadata."""
    if not is_sqlite():
        try:
            import sqlalchemy as sa
            eng = sa.create_engine(get_database_url(), pool_pre_ping=True)
            with eng.connect() as conn:
                res = conn.execute(sa.text("SELECT sheet_name, COUNT(*) FROM master_records GROUP BY sheet_name")).fetchall()
                found_sheets = {r[0]: r[1] for r in res if r[0]}
                names = set(found_sheets.keys()) | {DEFAULT_SHEET_NAME, CURRENT_SHEET_NAME}
                result = []
                for s_name in sorted(names):
                    cnt = found_sheets.get(s_name, 0)
                    result.append({
                        "name": s_name,
                        "is_default": (s_name == DEFAULT_SHEET_NAME),
                        "is_active": (s_name == CURRENT_SHEET_NAME),
                        "db_path": mask_database_url(),
                        "xlsx_path": str(DATA_DIR / f"{s_name}.xlsx"),
                        "has_xlsx": (DATA_DIR / f"{s_name}.xlsx").exists(),
                        "records_count": cnt,
                        "updated_at": None,
                    })
                return result
        except Exception:
            # Fallback if table not yet created
            return [{
                "name": DEFAULT_SHEET_NAME,
                "is_default": True,
                "is_active": True,
                "db_path": mask_database_url(),
                "xlsx_path": str(DATA_DIR / "MasterDB.xlsx"),
                "has_xlsx": (DATA_DIR / "MasterDB.xlsx").exists(),
                "records_count": 0,
                "updated_at": None,
            }]

    import sqlite3
    from datetime import datetime

    sheets: list[dict] = []

    # 1. Always ensure MasterDB is listed first
    master_db, master_xlsx = get_sheet_paths(DEFAULT_SHEET_NAME)
    master_count = 0
    master_updated = None
    if master_db.exists():
        master_updated = datetime.fromtimestamp(master_db.stat().st_mtime).isoformat()
        conn = None
        try:
            conn = sqlite3.connect(master_db)
            cur = conn.execute("SELECT COUNT(*) FROM master_records")
            row = cur.fetchone()
            master_count = row[0] if row else 0
        except Exception:
            pass
        finally:
            if conn:
                conn.close()

    sheets.append({
        "name": DEFAULT_SHEET_NAME,
        "is_default": True,
        "is_active": (CURRENT_SHEET_NAME == DEFAULT_SHEET_NAME),
        "db_path": str(master_db),
        "xlsx_path": str(master_xlsx),
        "has_xlsx": master_xlsx.exists(),
        "records_count": master_count,
        "updated_at": master_updated,
    })

    # 2. Scan for any other *.db files in DATA_DIR
    for p in sorted(DATA_DIR.glob("*.db")):
        if p.name.endswith(("-shm", "-wal")) or p.name == "master.db":
            continue
        sheet_name = p.stem
        _, xlsx_path = get_sheet_paths(sheet_name)
        count = 0
        updated = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
        conn = None
        try:
            conn = sqlite3.connect(p)
            cur = conn.execute("SELECT COUNT(*) FROM master_records")
            row = cur.fetchone()
            count = row[0] if row else 0
        except Exception:
            pass
        finally:
            if conn:
                conn.close()

        sheets.append({
            "name": sheet_name,
            "is_default": False,
            "is_active": (CURRENT_SHEET_NAME == sheet_name),
            "db_path": str(p),
            "xlsx_path": str(xlsx_path),
            "has_xlsx": xlsx_path.exists(),
            "records_count": count,
            "updated_at": updated,
        })

    return sheets


def delete_sheet(sheet_name: str) -> dict:
    """
    Permanently deletes a custom master sheet's SQLite database, WAL/SHM files,
    XLSX workbook, and any associated export files.
    Returns details of deleted items.
    Raises ValueError if attempting to delete DEFAULT_SHEET_NAME.
    Raises FileNotFoundError if the sheet doesn't exist.
    """
    clean = clean_sheet_name(sheet_name)
    if clean == DEFAULT_SHEET_NAME:
        raise ValueError(f"The default '{DEFAULT_SHEET_NAME}' master sheet is protected and cannot be deleted.")

    db_path, xlsx_path = get_sheet_paths(clean)
    if not db_path.exists() and not xlsx_path.exists():
        switched = False
        if get_active_sheet() == clean:
            set_active_sheet(DEFAULT_SHEET_NAME)
            switched = True
        return {
            "sheet_name": clean,
            "deleted_files": [],
            "active_sheet": get_active_sheet(),
            "switched_to_default": switched,
            "message": f"Sheet '{clean}' files were already removed.",
        }

    switched_to_default = False
    if get_active_sheet() == clean:
        set_active_sheet(DEFAULT_SHEET_NAME)
        switched_to_default = True

    deleted_files: list[str] = []

    # 1. Unlink database and sqlite journal/wal files
    for ext in (".db", ".db-wal", ".db-shm", ".xlsx"):
        f = DATA_DIR / f"{clean}{ext}"
        if f.exists():
            try:
                f.unlink(missing_ok=True)
                deleted_files.append(f.name)
            except Exception as e:
                logger.warning("Could not delete file %s: %s", f, e)

    # 2. Unlink any custom exports or CSVs associated with this sheet
    for pattern in (f"{clean}_custom_*.xlsx", f"{clean}_leads_*.csv"):
        for f in DATA_DIR.glob(pattern):
            if f.is_file():
                try:
                    f.unlink(missing_ok=True)
                    deleted_files.append(f.name)
                except Exception as e:
                    logger.warning("Could not delete export file %s: %s", f, e)

    return {
        "sheet_name": clean,
        "deleted_files": deleted_files,
        "active_sheet": get_active_sheet(),
        "switched_to_default": switched_to_default,
    }


# ── API Keys ──────────────────────────────────────────────────────────────────
APIFY_API_TOKEN  = os.getenv("APIFY_API_TOKEN", "")
APOLLO_API_KEY   = os.getenv("APOLLO_API_KEY", "")

# ── Apify Actors ──────────────────────────────────────────────────────────────
APIFY_ACTOR_ID = "compass/crawler-google-places"

# ── Decision Maker Classification Helpers ─────────────────────────────────────
def classify_dm_authority(title: str) -> str:
    """Classifies job title into standard authority level."""
    t = f" {(title or '').lower()} "
    if any(k in t for k in ("ceo", "chief executive", "managing director", "general manager", "founder", "owner", "president", "partner", "principal", "co-founder")):
        return "C-Suite / Owner"
    if any(k in t for k in ("director", "head of", "vp", "vice president", "executive director")):
        return "VP / Director"
    if "manager" in t or "lead" in t:
        return "Manager"
    return "Executive"

def classify_dm_department(title: str) -> str:
    """Classifies job title into functional department using exact token matching."""
    t = f" {(title or '').lower()} "
    # Specific departments first if title contains specialized function
    if any(k in t for k in ("recruit", "staffing", "talent", "human resources")) or re.search(r'\bhr\b', t):
        return "Recruiting / HR"
    if any(k in t for k in ("commercial", "business development", "sales", "account executive", "account manager")):
        return "Commercial / Sales"
    if any(k in t for k in ("operations", "branch manager", "logistics", "supply chain")):
        return "Operations"
    if any(k in t for k in ("technology", "digital", "software", "engineering", "technical")) or re.search(r'\b(it|cio|cto)\b', t):
        return "Technology"
    if any(k in t for k in ("marketing", "communications", "brand", "growth")):
        return "Marketing"
    # General Executive Leadership
    if any(k in t for k in ("chief", "ceo", "managing director", "founder", "owner", "president", "partner", "co-founder", "principal")):
        return "Executive Leadership"
    return "Management"

# ── Concurrency ───────────────────────────────────────────────────────────────
MAX_CONCURRENT_WEBSITE_CHECKS = 20
WEBSITE_TIMEOUT_SEC           = 12

# ── Crawl depth presets ───────────────────────────────────────────────────────
CRAWL_DEPTH_PRESETS = {
    "quick":    {"max_records": 100,  "label": "Quick",    "time": "~2 min",  "cost_per": "$0.10"},
    "standard": {"max_records": 300,  "label": "Standard", "time": "~5 min",  "cost_per": "$0.35"},
    "deep":     {"max_records": 500,  "label": "Deep",     "time": "~8 min",  "cost_per": "$0.55"},
    "complete": {"max_records": 5000, "label": "Complete", "time": "20+ min", "cost_per": "$2.00+"},
}

# ── Global target hubs & country presets ───────────────────────────────────────
GLOBAL_BUSINESS_HUBS = [
    "New York", "London", "Dubai", "Riyadh", "Singapore",
    "San Francisco", "Toronto", "Sydney", "Berlin", "Tokyo",
    "Chicago", "Frankfurt", "Paris", "Zurich", "Mumbai",
]

COUNTRY_CITIES: dict[str, list[str]] = {
    "united states": ["New York", "Los Angeles", "Chicago", "Houston", "San Francisco", "Austin", "Miami", "Dallas"],
    "usa": ["New York", "Los Angeles", "Chicago", "Houston", "San Francisco", "Austin", "Miami", "Dallas"],
    "united kingdom": ["London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Leeds", "Bristol"],
    "uk": ["London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Leeds", "Bristol"],
    "united arab emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah"],
    "uae": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah"],
    "saudi arabia": ["Riyadh", "Jeddah", "Dammam", "Khobar", "Makkah", "Medina", "NEOM", "Jubail"],
    "ksa": ["Riyadh", "Jeddah", "Dammam", "Khobar", "Makkah", "Medina", "NEOM", "Jubail"],
    "canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton"],
    "australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "germany": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Stuttgart", "Düsseldorf"],
    "singapore": ["Singapore", "Jurong East", "Tampines", "Woodlands"],
    "india": ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune", "Chennai"],
    "france": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Bordeaux"],
}

SAUDI_CITIES = COUNTRY_CITIES["saudi arabia"]

def get_preset_cities(country: str = "") -> list[str]:
    """Return preset cities for a given country, or global hubs by default."""
    if country:
        c = country.strip().lower()
        if c in COUNTRY_CITIES:
            return COUNTRY_CITIES[c]
        for k, v in COUNTRY_CITIES.items():
            if k in c or c in k:
                return v
    return GLOBAL_BUSINESS_HUBS

CITY_CODES: dict[str, str] = {
    # Global hubs
    "new york": "NYC", "london": "LON", "dubai": "DXB", "singapore": "SIN",
    "san francisco": "SFO", "chicago": "CHI", "toronto": "TOR", "sydney": "SYD",
    "berlin": "BER", "tokyo": "TYO", "frankfurt": "FRA", "paris": "PAR",
    "zurich": "ZRH", "mumbai": "BOM", "bengaluru": "BLR", "los angeles": "LAX",
    "austin": "ATX", "miami": "MIA", "dallas": "DFW", "houston": "HOU",
    "melbourne": "MEL", "vancouver": "YVR", "abu dhabi": "AUH",
    # Regional
    "riyadh":     "RYD", "jeddah":      "JED", "dammam":   "DAM",
    "makkah":     "MKH", "mecca":        "MKH", "medina":  "MDN",
    "al madinah": "MDN", "khobar":       "KHB", "al khobar":"KHB",
    "abha":       "ABH", "taif":         "TAF", "tabuk":   "TBK",
    "buraidah":   "BRD", "hail":         "HAL", "najran":  "NJR",
    "jubail":     "JUB", "yanbu":        "YNB", "dhahran": "DHR",
    "neom":       "NOM",
    # Arabic aliases
    "الرياض": "RYD", "جدة": "JED", "الدمام": "DAM",
    "مكة": "MKH", "مكة المكرمة": "MKH", "المدينة": "MDN", "المدينة المنورة": "MDN",
    "الخبر": "KHB", "أبها": "ABH", "الطائف": "TAF", "تبوك": "TBK",
    "بريدة": "BRD", "حائل": "HAL", "نجران": "NJR", "الجبيل": "JUB",
    "ينبع": "YNB", "الظهران": "DHR", "نيوم": "NOM",
}

def get_city_code(city: str) -> str:
    """
    Returns a standardized 3-4 letter uppercase code for any location name.
    Matches known static codes first, and dynamically derives a clean code
    for arbitrary places, districts, or international cities.
    """
    if not city:
        return "LOC"

    clean = city.strip().lower()
    if clean in CITY_CODES:
        return CITY_CODES[clean]

    # Check comma-separated tokens (e.g., 'Al Olaya, Riyadh' -> 'RYD')
    parts = [p.strip() for p in clean.split(",") if p.strip()]
    for p in reversed(parts):  # Check city first before district if 'District, City'
        if p in CITY_CODES:
            return CITY_CODES[p]
    for p in parts:
        if p in CITY_CODES:
            return CITY_CODES[p]

    # Algorithmic code generator for arbitrary places:
    base_name = parts[0]
    normalized = re.sub(r'^(al[\s\-]|el[\s\-])', '', base_name).strip()
    words = [w for w in re.split(r'[\s\-]+', normalized) if w]

    if len(words) >= 3:
        code = "".join(w[0] for w in words[:3]).upper()
    elif len(words) == 2:
        code = (words[0][:2] + words[1][0]).upper()
    elif len(words) == 1:
        w = re.sub(r'[^a-zA-Z0-9]', '', words[0])
        if len(w) >= 3:
            code = w[:3].upper()
        elif len(w) > 0:
            code = w.ljust(3, 'X').upper()
        else:
            code = "LOC"
    else:
        code = "LOC"

    return code[:4]


# ── Industries ────────────────────────────────────────────────────────────────
INDUSTRIES: dict[str, dict] = {

    "construction": {
        "name": "Construction & Contracting",
        "queries": [
            "construction company",
            "general contractor",
            "building contractor",
            "civil engineering company",
        ],
        "sub_map": {
            "General contractor":    "General Contracting",
            "Building contractor":   "General Contracting",
            "Construction company":  "General Contracting",
            "Civil engineering":     "Civil Engineering",
            "Electrical contractor": "Electrical Works",
            "Mechanical contractor": "MEP Contracting",
            "Road construction":     "Infrastructure",
            "Interior design":       "Fit-Out & Interior",
            "Steel fabricator":      "Steel & Metal Works",
            "Concrete contractor":   "Concrete & Structural",
        },
        "default_sub": "General Contracting",
    },

    "engineering": {
        "name": "Engineering & Consultancy",
        "queries": [
            "engineering consultancy",
            "consulting engineer",
            "architecture firm",
            "structural engineering",
        ],
        "sub_map": {
            "Engineering consultant": "Engineering Consultancy",
            "Architectural firm":     "Architecture",
            "Structural engineer":    "Structural Engineering",
            "Environmental consultant":"Environmental",
            "Geotechnical engineer":  "Geotechnical",
        },
        "default_sub": "Engineering Consultancy",
    },

    "software_and_it_services": {
        "name": "Software & IT Services",
        "queries": [
            "software company",
            "information technology company",
            "computer consultant",
            "data processing service",
            "custom software development",
            "it consulting firm"
        ],
        "sub_map": {
            "Software company": "Software Development",
            "Information technology company": "IT Services",
            "Computer consultant": "IT Consulting",
            "Data processing service": "Data & Backend Infrastructure",
            "Web designer": "Web & Frontend Development",
            "Internet marketing service": "Digital Agency"
        },
        "default_sub": "Software Development"
    },

    "logistics": {
        "name": "Logistics & Transportation",
        "queries": [
            "logistics company",
            "freight forwarding company",
            "transportation company",
            "shipping company",
            "customs clearance",
        ],
        "sub_map": {
            "Freight forwarding service": "Freight Forwarding",
            "Transportation service":     "Land Transport",
            "Shipping company":           "Shipping",
            "Customs broker":             "Customs Clearance",
            "Warehousing":                "Warehousing",
            "Courier service":            "Last-Mile Delivery",
            "Moving company":             "Moving & Relocation",
        },
        "default_sub": "Logistics",
    },

    "manufacturing": {
        "name": "Manufacturing",
        "queries": [
            "manufacturing company",
            "factory",
            "industrial manufacturer",
            "food manufacturing",
        ],
        "sub_map": {
            "Manufacturing plant":    "General Manufacturing",
            "Food manufacturer":      "Food & Beverage Manufacturing",
            "Chemical manufacturer":  "Chemical Manufacturing",
            "Plastic manufacturer":   "Plastics & Rubber",
            "Metal fabricator":       "Metal Fabrication",
            "Furniture manufacturer": "Furniture Manufacturing",
        },
        "default_sub": "General Manufacturing",
    },

    "healthcare": {
        "name": "Healthcare & Clinics",
        "queries": [
            "medical clinic",
            "private hospital",
            "dental clinic",
            "polyclinic",
            "diagnostic center",
        ],
        "sub_map": {
            "Medical clinic":    "General Practice",
            "Hospital":          "Hospital",
            "Dental clinic":     "Dental",
            "Ophthalmologist":   "Ophthalmology",
            "Dermatologist":     "Dermatology",
            "Diagnostic center": "Diagnostics & Imaging",
            "Pharmacy":          "Pharmacy",
        },
        "default_sub": "Healthcare Services",
    },

    "retail": {
        "name": "Retail & Wholesale",
        "queries": [
            "wholesale supplier",
            "retail store",
            "trading company",
            "distributor",
        ],
        "sub_map": {
            "Wholesaler":               "Wholesale Distribution",
            "Retail store":             "Retail",
            "Trading company":          "General Trading",
            "Distributor":              "Distribution",
            "Electronics store":        "Electronics Retail",
            "Building materials store": "Building Materials",
            "Auto parts store":         "Auto Parts",
        },
        "default_sub": "General Trading",
    },

    "fnb": {
        "name": "F&B & Restaurants",
        "queries": [
            "restaurant",
            "cafe",
            "catering company",
            "bakery",
        ],
        "sub_map": {
            "Restaurant":          "Restaurant",
            "Café":                "Café",
            "Fast food restaurant": "Fast Food",
            "Catering":            "Catering",
            "Bakery":              "Bakery",
        },
        "default_sub": "Restaurant",
    },

    "professional_services": {
        "name": "Professional Services",
        "queries": [
            "law firm",
            "accounting firm",
            "management consulting",
            "IT consulting company",
            "HR consulting",
        ],
        "sub_map": {
            "Law firm":                       "Legal Services",
            "Accounting firm":                "Accounting & Audit",
            "Business management consultant": "Management Consulting",
            "IT service":                     "IT Consulting",
            "Human resources consulting":     "HR Consulting",
            "Financial consultant":           "Financial Advisory",
        },
        "default_sub": "Professional Services",
    },

    "real_estate": {
        "name": "Real Estate",
        "queries": [
            "real estate company",
            "property developer",
            "real estate agency",
        ],
        "sub_map": {
            "Real estate agency":           "Real Estate Agency",
            "Real estate developer":        "Property Development",
            "Property management company":  "Property Management",
            "Commercial real estate":       "Commercial Real Estate",
            "Real estate consultant":       "Real Estate Advisory",
        },
        "default_sub": "Real Estate",
    },

    "education": {
        "name": "Education",
        "queries": [
            "private school",
            "international school",
            "training center",
            "university",
            "language school",
        ],
        "sub_map": {
            "Private school":      "Private School",
            "International school":"International School",
            "University":          "University",
            "Training center":     "Training & Vocational",
            "Language school":     "Language Institute",
            "Kindergarten":        "Early Childhood",
        },
        "default_sub": "Education",
    },

    "telecom": {
        "name": "Telecom & Technology",
        "queries": [
            "technology company",
            "telecom company",
            "software company",
            "IT company",
            "cybersecurity company",
        ],
        "sub_map": {
            "Software company":                        "Software Development",
            "Telecommunications service provider":     "Telecom",
            "IT service":                              "IT Services",
            "Cybersecurity company":                   "Cybersecurity",
            "Internet service provider":               "ISP",
        },
        "default_sub": "Technology",
    },

    "staffing_and_recruitment": {
        "name": "Staffing & Recruitment",
        "queries": [
            "recruitment agency",
            "staffing agency",
            "employment agency",
            "manpower supply company",
            "executive search firm",
            "hr recruitment consultancy",
        ],
        "sub_map": {
            "Recruiter":                   "Recruitment & Placement",
            "Employment agency":           "Employment Agency",
            "Executive search firm":       "Executive Search",
            "Human resource consulting":   "HR Consulting & Staffing",
            "Temporary employment agency": "Temporary & Contract Staffing",
            "Employment consultant":       "Talent Advisory",
        },
        "default_sub": "Staffing & Recruitment",
    },

    "business_consulting": {
        "name": "Business Consulting Firms",
        "queries": [
            "business management consultant",
            "management consulting firm",
            "business consulting firm",
            "strategy consulting firm",
            "corporate advisory firm",
        ],
        "sub_map": {
            "Business management consultant": "Management Consulting",
            "Corporate office":              "Corporate Advisory",
            "Financial consultant":           "Financial Advisory",
            "Business development service":   "Business Development",
            "Consultant":                     "General Business Consulting",
            "Marketing consultant":           "Marketing & Strategy",
        },
        "default_sub": "Business Consulting",
    },

    "bfsi": {
        "name": "BFSI (Banking & Financial Services)",
        "queries": [
            "commercial bank",
            "investment bank",
            "insurance company",
            "financial services company",
            "fintech company",
            "wealth management firm",
        ],
        "sub_map": {
            "Bank":                  "Commercial Banking",
            "Investment bank":       "Investment Banking",
            "Insurance company":     "Insurance",
            "Financial institution": "Financial Services",
            "Fintech":               "Fintech",
            "Financial planner":     "Wealth Management",
            "Mortgage lender":       "Lending & Credit",
            "Stock broker":          "Brokerage & Securities",
            "Accounting firm":       "Financial Advisory",
        },
        "default_sub": "Banking & Financial Services",
    },

    "airport": {
        "name": "Airport & Aviation",
        "queries": [
            "international airport",
            "regional airport",
            "airport terminal",
            "airport operator",
            "aviation services company",
            "air cargo terminal",
            "ground handling service",
            "aircraft maintenance company",
        ],
        "sub_map": {
            "International airport":        "Airport Operations",
            "Airport":                      "Airport Operations",
            "Aviation service":             "Aviation Services",
            "Airlines":                     "Airlines & Carriers",
            "Airline":                      "Airlines & Carriers",
            "Air cargo service":            "Air Cargo & Logistics",
            "Aerospace company":            "Aerospace & Defense",
            "Aircraft maintenance company": "Aircraft Maintenance & MRO",
            "Charter service":              "Private Charter & Aviation",
            "Helicopter charter":           "Private Charter & Aviation",
            "Airport shuttle service":      "Ground Transportation",
        },
        "default_sub": "Airport Operations",
    },
}


# ── Sub-industry lookup ───────────────────────────────────────────────────────
def get_sub_industry(google_categories: list[str], industry_key: str) -> str:
    industry = INDUSTRIES.get(industry_key, {})
    sub_map  = industry.get("sub_map", {})
    for cat in google_categories:
        if cat in sub_map:
            return sub_map[cat]
        for key, val in sub_map.items():
            if key.lower() in cat.lower() or cat.lower() in key.lower():
                return val
    return industry.get("default_sub", "General")


# ── B2B / B2C keyword signals ─────────────────────────────────────────────────
B2B_KEYWORDS = [
    "wholesale", "distributor", "supplier", "contractor", "enterprise",
    "corporate", "industrial", "manufacturer", "b2b", "procurement",
    "tender", "rfq", "fleet", "consultancy", "oem",
]
B2C_KEYWORDS = [
    "retail", "shop", "store", "appointment", "booking", "walk-in",
    "customer service", "consumer", "b2c", "delivery", "order online",
    "menu", "price list", "buy now", "add to cart",
]

# ── Tech stack detection patterns ─────────────────────────────────────────────
TECH_PATTERNS = {
    "WordPress":        ["wp-content", "wp-includes", "wordpress"],
    "WooCommerce":      ["woocommerce", "wc-ajax"],
    "Shopify":          ["cdn.shopify.com", "myshopify.com", "shopify"],
    "Magento":          ["mage/cookies", "static/_requirejs", "magento"],
    "Salla":            ["salla.sa", "salla.cloud", "salla-theme"],
    "Zid":              ["zid.store", "zid.sa", "assets.zid.store"],
    "Next.js":          ["_next/static", "__NEXT_DATA__"],
    "Nuxt.js":          ["_nuxt/", "__NUXT__"],
    "Laravel":          ["csrf-token", "laravel_session", "XSRF-TOKEN"],
    "HubSpot":          ["js.hs-scripts.com", "hbspt.forms"],
    "Salesforce":       ["salesforce", "pardot"],
    "Zoho":             ["zoho.com", "zohocdn.com"],
    "Google Analytics": ["gtag(", "google-analytics.com", "ga("],
    "Google Tag Mgr":   ["googletagmanager.com/gtm.js"],
    "Meta Pixel":       ["fbevents.js", "fbq("],
    "TikTok Pixel":     ["analytics.tiktok.com"],
    "Snapchat Pixel":   ["sc-static.net/scevent.min.js"],
    "Hotjar":           ["static.hotjar.com"],
    "Cloudflare":       ["cloudflare", "__cfduid"],
}
