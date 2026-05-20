import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project folder before reading any env vars.
# This means you never need to manually export variables in your terminal —
# just keep your keys in .env and they are automatically available.
_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env")

# ============================================================
# config.py — Central configuration
#
# KEY CHANGES IN THIS VERSION:
#   1. ALL_BUSINESS_CATEGORIES now maps display names to Google's
#      official Place Types — so "Mall" only returns actual malls,
#      not plazas or commercial complexes.
#   2. ZOOM_LEVEL and MAX_TOTAL_RESULTS_PER_RUN added — controls
#      how thoroughly Apify tiles a city to find every business.
#   3. DB_PATH now uses pathlib — always relative to this file,
#      not the working directory, so the DB is always found.
#   4. SAUDI_PHONE_PATTERN unified — single authoritative regex
#      used by both validator.py and contact_utils.py.
#   5. PSI_CONCURRENT_LIMIT added — controls parallel PageSpeed
#      API calls in the new async audit batch.
# ============================================================

# ── API KEYS — EDIT THESE BEFORE RUNNING ─────────────────────

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")   # apify.com → Account → Integrations
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")      # console.groq.com → API Keys
PSI_API_KEY     = os.getenv("PSI_API_KEY", "")       # console.cloud.google.com → PageSpeed Insights API
HUNTER_API_KEY  = os.getenv("HUNTER_API_KEY", "")    # hunter.io → API keys

# ── FIXED COUNTRY ─────────────────────────────────────────────
 
FIXED_COUNTRY = "Saudi Arabia"   # Hardcoded — no country menu shown
 
# ── APIFY ACTOR ───────────────────────────────────────────────
 
APIFY_ACTOR_ID = "compass/crawler-google-places"   # Official Apify Google Maps actor
 
# ── GROQ MODEL ────────────────────────────────────────────────
 
GROQ_MODEL = "llama-3.1-8b-instant"   # Fastest + cheapest — 840 tokens/sec
 
# ── SCRAPING LIMITS ───────────────────────────────────────────
 
ZOOM_LEVEL = 15    # City tiling zoom — splits city into a grid of search zones
                   # zoom 12 = ~4 zones  (small cities)
                   # zoom 14 = ~16 zones (medium cities)
                   # zoom 15 = ~36 zones (large cities — good for Riyadh, Jeddah)
                   # zoom 16 = ~80 zones (very dense cities — slower, use carefully)
                   # No result cap — Apify stops when Google has nothing left
                   # You get the TRUE total count of that category in the city
 
MAX_CONCURRENT_VALIDATIONS = 50    # Parallel website checks at once
WEBSITE_TIMEOUT_SECONDS    = 8     # Give up on sites that don't respond in 8 seconds
PSI_CONCURRENT_LIMIT       = 5     # Parallel PageSpeed Insights API calls
                                   # PSI quota is 240/4 min — 5 concurrent is safe
 
# ── LEAD SCORING THRESHOLDS ───────────────────────────────────
 
MIN_ACCEPTABLE_SCORE     = 70   # Businesses at or above this are treated as acceptable
MIN_ACCEPTABLE_UIUX      = 7    # AI UI/UX score is 1-10, so 7 == 70%

SEO_SCORE_THRESHOLD      = MIN_ACCEPTABLE_SCORE
PERFORMANCE_THRESHOLD    = MIN_ACCEPTABLE_SCORE
ACCESSIBILITY_THRESHOLD  = MIN_ACCEPTABLE_SCORE
BEST_PRACTICES_THRESHOLD = MIN_ACCEPTABLE_SCORE
 
# ── BLOCKED DOMAINS ───────────────────────────────────────────
 
BLOCKED_DOMAINS = [
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "linkedin.com",
    "youtube.com",
    "tripadvisor.com",
    "yelp.com",
    "zomato.com",
    "talabat.com",
    "booking.com",
    "airbnb.com",
    "wikipedia.org",
    "google.com",
    "restaurantguru.com",
    "ksa.directory",
    "yellowpages",
    "foursquare.com",
    "whatsapp",
    ".pdf",
    "snapchat.com",
]
 
# ── SAUDI PHONE REGEX ─────────────────────────────────────────
# Single authoritative pattern used by both validator.py and contact_utils.py.
# Prefix (+966 / 00966 / 0) is OPTIONAL so numbers already normalised to
# 9 bare digits are still matched.
# Handles:
#   5xxxxxxxx  — mobile numbers (05x series)
#   1[1-7]xxxxxxx — landline city codes (011 Riyadh, 012 Jeddah, etc.)
#   any 9-digit number as a catch-all fallback

SAUDI_PHONE_PATTERN = r"(?:\+966|00966|0)?(?:5[0-9]{8}|1[1-7][0-9]{7}|[0-9]{9})"
 
# ── OUTPUT PATHS ──────────────────────────────────────────────
# Use pathlib so paths are always relative to THIS file, not the
# working directory at runtime.  This prevents the DB from being
# created in a random location when the script is run from a
# different directory or via a cron job.

DB_PATH  = str(_HERE / "leads.db")
CSV_PATH = str(_HERE / "leads.csv")
 
# ── PAGESPEED API ─────────────────────────────────────────────
 
PSI_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
 
# ── SAUDI CITIES ──────────────────────────────────────────────
 
SAUDI_CITIES = [
    "Riyadh",
    "Jeddah",
    "Dammam",
    "Mecca",
    "Medina",
    "Khobar",
    "Abha",
    "Tabuk",
    "Najran",
    "Hail",
    "Taif",
    "Yanbu",
]
 
# ── EIT QUERY LIBRARY ────────────────────────────────────────
# Organized by EIT product opportunity, not only industry.
# {city} is replaced with the selected English city name.
# {city_ar} is replaced with the Arabic city name when configured.

SAUDI_CITY_ARABIC = {
    "Riyadh": "الرياض",
    "Jeddah": "جدة",
    "Dammam": "الدمام",
    "Mecca": "مكة",
    "Medina": "المدينة",
    "Khobar": "الخبر",
    "Abha": "أبها",
    "Tabuk": "تبوك",
    "Najran": "نجران",
    "Hail": "حائل",
    "Taif": "الطائف",
    "Yanbu": "ينبع",
}

EIT_QUERY_LIBRARY = {
    "Construction & Contracting": {
        "tier": "A",
        "product_lines": ["SSL", "ERP", "GPS Fleet", "Computer Vision Safety"],
        "queries": [
            "construction company {city}", "contracting company {city}", "building contractor {city}",
            "civil engineering contractor {city}", "mep contractor {city}", "landscape contractor {city}",
            "demolition contractor {city}", "شركة مقاولات {city_ar}", "مقاول عام {city_ar}", "مقاول بناء {city_ar}",
        ],
    },
    "Engineering Consultancies": {
        "tier": "A",
        "product_lines": ["SSL", "ERP", "Custom Software"],
        "queries": [
            "engineering consultancy {city}", "structural engineering firm {city}", "mep engineering {city}",
            "civil engineering consultants {city}", "architectural firm {city}", "مكتب هندسي {city_ar}",
            "مكتب استشارات هندسية {city_ar}", "شركة هندسة معمارية {city_ar}",
        ],
    },
    "Logistics & Transportation": {
        "tier": "A",
        "product_lines": ["GPS Fleet Tracking", "ERP", "Custom Apps"],
        "queries": [
            "transportation company {city}", "logistics company {city}", "freight company {city}",
            "trucking company {city}", "delivery company {city}", "courier company {city}",
            "moving company {city}", "warehouse {city}", "شركة نقل {city_ar}", "شركة شحن {city_ar}",
            "شركة توصيل {city_ar}",
        ],
    },
    "Manufacturing": {
        "tier": "A",
        "product_lines": ["ERP", "IoT", "Computer Vision"],
        "queries": [
            "manufacturing company {city}", "factory {city}", "food manufacturing {city}",
            "plastics manufacturing {city}", "metal works {city}", "furniture manufacturing {city}",
            "chemical company {city}", "مصنع {city_ar}", "شركة تصنيع {city_ar}",
        ],
    },
    "Healthcare": {
        "tier": "B",
        "product_lines": ["SSL", "SBOSS ERP", "Custom Apps"],
        "queries": [
            "medical clinic {city}", "dental clinic {city}", "hospital {city}", "medical center {city}",
            "diagnostic center {city}", "pharmacy {city}", "مستشفى {city_ar}", "عيادة طبية {city_ar}",
            "صيدلية {city_ar}",
        ],
    },
    "Retail & Wholesale": {
        "tier": "B",
        "product_lines": ["SSL", "ERP", "POS Integration"],
        "queries": [
            "retail company {city}", "wholesale company {city}", "clothing store {city}",
            "electronics store {city}", "auto parts store {city}", "furniture store {city}",
            "home appliances {city}", "شركة تجارة {city_ar}", "متجر {city_ar}", "محل تجاري {city_ar}",
        ],
    },
    "Food & Beverage / Hospitality": {
        "tier": "B",
        "product_lines": ["SSL", "ERP", "Custom Apps"],
        "queries": [
            "restaurant chain {city}", "cafe chain {city}", "catering company {city}", "hotel {city}",
            "fast food chain {city}", "food delivery {city}", "مطعم {city_ar}", "مقهى {city_ar}",
            "فندق {city_ar}", "شركة تموين {city_ar}",
        ],
    },
    "Professional Services": {
        "tier": "B",
        "product_lines": ["SSL", "ERP", "AI Office Automation"],
        "queries": [
            "accounting firm {city}", "law firm {city}", "marketing agency {city}", "consulting firm {city}",
            "human resources company {city}", "recruitment agency {city}", "مكتب محاماة {city_ar}",
            "مكتب محاسبة {city_ar}", "وكالة تسويق {city_ar}",
        ],
    },
    "Telecom & ICT": {
        "tier": "C",
        "product_lines": ["Telecom Power Monitoring", "Computer Vision"],
        "queries": [
            "telecom company {city}", "internet service provider {city}", "data center {city}",
            "network services {city}", "شركة اتصالات {city_ar}", "مزود خدمة الإنترنت {city_ar}",
        ],
    },
    "Energy & Utilities": {
        "tier": "C",
        "product_lines": ["Solar Grid Monitoring", "Transformer Monitoring", "Oil Field"],
        "queries": [
            "solar energy company {city}", "solar panel installation {city}", "electrical contractor {city}",
            "power generation {city}", "oil and gas services {city}", "شركة طاقة شمسية {city_ar}",
            "شركة كهرباء {city_ar}", "شركة بترول {city_ar}",
        ],
    },
    "Real Estate & Property": {
        "tier": "C",
        "product_lines": ["SSL", "No-Code Apps", "Custom Software"],
        "queries": [
            "real estate company {city}", "property management {city}", "real estate developer {city}",
            "property maintenance {city}", "شركة عقارية {city_ar}", "شركة إدارة عقارات {city_ar}",
            "مطور عقاري {city_ar}",
        ],
    },
    "Security & Safety": {
        "tier": "C",
        "product_lines": ["Computer Vision", "IoT Monitoring", "GPS"],
        "queries": [
            "security services {city}", "security company {city}", "fire safety company {city}",
            "cctv installation {city}", "شركة أمن {city_ar}", "شركة حراسة {city_ar}",
        ],
    },
    "Education": {
        "tier": "C",
        "product_lines": ["SSL", "SBOSS ERP", "Custom Apps"],
        "queries": [
            "private school {city}", "training center {city}", "language institute {city}",
            "educational consulting {city}", "مدرسة خاصة {city_ar}", "معهد تدريب {city_ar}",
            "مركز تعليمي {city_ar}",
        ],
    },
    "Automotive": {
        "tier": "C",
        "product_lines": ["GPS Fleet", "ERP", "Custom Apps"],
        "queries": [
            "car dealership {city}", "auto service {city}", "car rental {city}", "auto repair shop {city}",
            "معرض سيارات {city_ar}", "ورشة سيارات {city_ar}", "تأجير سيارات {city_ar}",
        ],
    },
}

BUSINESS_CATEGORIES = EIT_QUERY_LIBRARY
 
# ── WEBSITE QUALITY LABEL ─────────────────────────────────────
# Used in the CSV to label each business with a human-readable quality tier.
# Determined by lead_score in main.py.
 
QUALITY_LABELS = {
    (80, 100): "Critical — No website or severe issues",
    (60,  79): "High — Multiple serious problems",
    (40,  59): "Medium — Several improvements needed",
    (20,  39): "Low — Minor issues",
    ( 0,  19): "Good — Website quality is acceptable",
}
