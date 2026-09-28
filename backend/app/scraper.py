"""
EIT Saudi Lead Intelligence — Apify Google Maps runner.
scraper.py: run the Apify actor, normalise results, yield records.

City-aware: query becomes "{search_term} in {city}".
Cost estimate: ~$0.011 per record (compass/crawler-google-places).
"""

import asyncio
import logging
import re
from typing import AsyncGenerator, Any

from apify_client import ApifyClient

try:
    from backend.app import config
    from backend.app.config import get_sub_industry
except ImportError:
    import config
    from config import get_sub_industry

logger = logging.getLogger(__name__)

ACTOR_ID = getattr(config, "APIFY_ACTOR_ID", "compass/crawler-google-places")

# Precompiled patterns for robust naming separation
ARABIC_CHAR_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]')
LATIN_CHAR_PATTERN  = re.compile(r'[a-zA-Z]')
DELIMITERS_PATTERN  = re.compile(r'\s+[-|/—•:]+\s+')
PAREN_PATTERN       = re.compile(r'[\(\[\{]([^\)\]\}]+)[\)\]\}]')
CLEAN_STRIP_CHARS   = " -|/—•:;,()[]{}\"'`\t\n\r"


# ── Cost helper ───────────────────────────────────────────────────────────────

def estimate_cost(max_records: int, num_industries: int = 1, num_cities: int = 1) -> dict:
    total_records = max_records * num_industries * num_cities
    apify_total   = round(total_records * 0.011, 2)
    return {
        "total_records_est": total_records,
        "apify_total_usd":   apify_total,
        "website_usd":       0.00,
        "part1_total_usd":   apify_total,
    }


# ── Helper Inference Functions for Automated Filling ──────────────────────────

def _handle_arabic_naming(title: str) -> tuple[str, str]:
    """
    Separates English and Arabic characters. If Google Maps returns an Arabic 
    or mixed name, cleanly segments it across the respective language columns
    without retaining dangling delimiters or parentheses.
    """
    title = (title or "").strip()
    if not title:
        return "", ""

    has_ar = bool(ARABIC_CHAR_PATTERN.search(title))
    has_en = bool(LATIN_CHAR_PATTERN.search(title))

    # Case 1: Pure Arabic
    if has_ar and not has_en:
        return title, title

    # Case 2: Pure English / Latin
    if has_en and not has_ar:
        return title, ""

    # Case 3: Mixed — check for parenthesized expression: "Name_EN (Name_AR)"
    paren_match = PAREN_PATTERN.search(title)
    if paren_match:
        inside = paren_match.group(1).strip().strip(CLEAN_STRIP_CHARS)
        outside = (title[:paren_match.start()] + " " + title[paren_match.end():]).strip().strip(CLEAN_STRIP_CHARS)
        if ARABIC_CHAR_PATTERN.search(inside) and not LATIN_CHAR_PATTERN.search(inside):
            return outside, inside
        elif LATIN_CHAR_PATTERN.search(inside) and not ARABIC_CHAR_PATTERN.search(inside):
            return inside, outside

    # Case 4: Mixed — structured separator: "Name_AR - Name_EN" or "Name_EN | Name_AR"
    sep_match = DELIMITERS_PATTERN.search(title)
    if sep_match:
        part1 = title[:sep_match.start()].strip().strip(CLEAN_STRIP_CHARS)
        part2 = title[sep_match.end():].strip().strip(CLEAN_STRIP_CHARS)
        if ARABIC_CHAR_PATTERN.search(part1) and LATIN_CHAR_PATTERN.search(part2):
            return part2, part1
        elif LATIN_CHAR_PATTERN.search(part1) and ARABIC_CHAR_PATTERN.search(part2):
            return part1, part2

    # Case 5: Word-by-word fallback
    words = title.split()
    ar_words = [w.strip(CLEAN_STRIP_CHARS) for w in words if ARABIC_CHAR_PATTERN.search(w)]
    en_words = [w.strip(CLEAN_STRIP_CHARS) for w in words if LATIN_CHAR_PATTERN.search(w)]

    name_ar = " ".join(w for w in ar_words if w).strip()
    name_en = " ".join(w for w in en_words if w).strip()

    if not name_en:
        name_en = title
    if not name_ar:
        name_ar = ""

    return name_en, name_ar


def _detect_company_type(title: str, categories: list[str]) -> str:
    """
    Infers business legal structure/type (LLC, Corporation, Establishment, etc.)
    from company name, title suffixes, or Google categories.
    """
    t = (title or "").lower()
    
    if any(k in t for k in [" llc", " l.l.c", " ذ.م.م", "ذ م م", " w.l.l", " wll"]):
        return "Limited Liability Company (LLC)"
    if any(k in t for k in [" corp", " corporation", " inc", " inc.", " incorporated", " ش.م.م"]):
        return "Corporation"
    if any(k in t for k in [" plc", " p.l.c", " public limited", " cjsc", " jsc", "مساهمة"]):
        return "Public Joint Stock Company"
    if any(k in t for k in [" ltd", " ltd.", " limited", "محدودة"]):
        return "Private Limited Company"
    if any(k in t for k in [" group", " holding", " holdings", "مجموعة", "قابضة"]):
        return "Corporate Group / Holding"
    if any(k in t for k in ["est", "est.", "establishment", "مؤسسة"]):
        return "Establishment / Sole Proprietorship"
    if any(k in t for k in ["branch", "فرع"]):
        return "Branch Office"
    if any(k in t for k in ["partnership", "شراكة", " lp", " l.p."]):
        return "Partnership"
    
    cat_str = " ".join(categories).lower()
    if "corporate office" in cat_str or "headquarters" in cat_str:
        return "Corporate Headquarters"
    if "holding" in cat_str:
        return "Holding Company"

    return "Private Corporate Entity"


# ── Record normaliser ─────────────────────────────────────────────────────────

def _normalize(
    raw: dict,
    query: str,
    country: str,
    added_by: str,
    industry_key: str,
    city_hint: str = "",
) -> dict | None:
    """Map raw Apify result → master schema dict. Returns None for unusable records."""
    if raw.get("permanentlyClosed") or raw.get("businessStatus") == "CLOSED_PERMANENTLY":
        return None

    place_id = (raw.get("placeId") or "").strip()
    if not place_id:
        return None

    # Location (handles 0.0 truthiness safely)
    loc = raw.get("location") if isinstance(raw.get("location"), dict) else {}
    lat = loc.get("lat") if loc.get("lat") is not None else raw.get("lat")
    lng = loc.get("lng") if loc.get("lng") is not None else raw.get("lng")

    # Phone — strip all formatting and non-numeric delimiters
    phone = (raw.get("phone") or raw.get("phoneUnformatted") or "").strip()
    phone = re.sub(r'[\s\-()./]+', '', phone)

    # Website
    website = (raw.get("website") or "").strip()
    if website and website.lower() not in ("none", "null", "n/a"):
        if not website.startswith(("http://", "https://")):
            website = "https://" + website
    else:
        website = ""

    # Categories — primary first, deduplicated
    categories: list[str] = list(dict.fromkeys(
        ([raw["categoryName"]] if raw.get("categoryName") else [])
        + (raw.get("categories") or [])
    ))

    # City — prefer English hint to guarantee standard KSA city code matching
    city = (city_hint or raw.get("city") or "").strip()
    if not city:
        addr = raw.get("address") or ""
        parts = addr.split(",")
        if len(parts) >= 2:
            # Drop trailing postal code digits if attached to the city part
            raw_city_part = parts[-2].strip()
            city = re.sub(r'\d+', '', raw_city_part).strip()

    sub           = get_sub_industry(categories, industry_key)
    industry_cfg  = config.INDUSTRIES.get(industry_key, {})
    industry_name = categories[0] if categories else industry_cfg.get("name", "")

    # Clean and split string languages out of the raw Title name
    raw_title = (raw.get("title") or "").strip()
    name_en, name_ar = _handle_arabic_naming(raw_title)

    company_type = _detect_company_type(raw_title, categories)

    # Dynamic Country resolution: explicit country -> parsed from address -> fallback
    formatted_country = country.strip().title() if country else ""
    if not formatted_country:
        addr = raw.get("address") or ""
        parts = [p.strip() for p in addr.split(",") if p.strip()]
        if parts:
            candidate_country = parts[-1]
            if not re.search(r'^\d+$', candidate_country):
                formatted_country = candidate_country.title()
    if not formatted_country:
        formatted_country = "Global"

    return {
        "Company_Name":          name_en,
        "Company_Name_EN":       name_en,
        "Company_Name_AR":       name_ar,
        "Company_Type":          company_type,
        "Country":               formatted_country,
        "City":                  city,
        "District":              (raw.get("neighborhood") or "").strip(),
        "Postal_Code":           (raw.get("postalCode") or "").strip(),
        "Full_Address":          (raw.get("address") or "").strip(),
        "Google_Maps_URL":       (raw.get("url") or "").strip(),
        "Latitude":              lat,
        "Longitude":             lng,
        "Google_Rating":         raw.get("totalScore"),
        "Reviews_Count":         raw.get("reviewsCount") or 0,
        "Google_Reviews_Count":  raw.get("reviewsCount") or 0,
        "Primary_Phone":         phone,
        "Phone_Primary":         phone,
        "General_Email":         "",
        "Email_General":         "",
        "Website_URL":           website,
        "Has_Website":           "Yes" if website else "No",
        "Company_LinkedIn":      "",
        "Company_LinkedIn_URL":  "",
        "Primary_Industry":      industry_name,
        "Industry_Primary":      industry_name,
        "Secondary_Industry":    sub,
        "Sub_Industry":          sub,
        # Metadata
        "Added_By":              added_by,
        "Updated_By":            added_by,
        # Internal / Deduplication key
        "google_place_id":       place_id,
        "_raw_categories":       categories,
    }


# ── Scraper ───────────────────────────────────────────────────────────────────

async def scrape(
    query: str | list[str],
    city: str,
    country: str,
    max_records: int,
    industry_key: str,
    added_by: str = "System",
    language: str = "en",
) -> AsyncGenerator[dict, None]:
    """
    Async generator. Runs Apify actor in a thread pool executor
    (blocking call), then yields normalised records one by one.
    Accepts a single query string or a list of queries to consolidate into a single actor run.
    """
    token = (config.APIFY_API_TOKEN or "").strip()
    if not token or token.lower() in ("your_apify_token_here", "your_token_here"):
        raise ValueError(
            "APIFY_API_TOKEN is not configured in .env.\n"
            "Please add your Apify token to .env or backend/.env (get one at https://console.apify.com/account/integrations)."
        )

    place_str   = (city or "").strip()
    country_str = (country or "").strip()

    # Deduplicate locationQuery so "Dubai, UAE" + "UAE" doesn't become "Dubai, UAE, UAE"
    if place_str and country_str and country_str.lower() in place_str.lower():
        full_location = place_str
    elif place_str and country_str:
        full_location = f"{place_str}, {country_str}"
    else:
        full_location = place_str or country_str

    if isinstance(query, list):
        query_list = [q.strip() for q in query if q.strip()]
        query_label = ", ".join(query_list)
        search_strings_array = [
            f"{q} in {place_str}" if place_str else (f"{q} in {country_str}" if country_str else q)
            for q in query_list
        ]
    else:
        query_label = query
        search_string = f"{query} in {place_str}" if place_str else (f"{query} in {country_str}" if country_str else query)
        search_strings_array = [search_string]

    # Dynamic country code inference from country_str or place_str
    country_code = _country_code(country_str) or _country_code(place_str)

    # Respect optional industry-specific caps.
    industry_cfg = config.INDUSTRIES.get(industry_key, {})
    if "max_override" in industry_cfg:
        max_records = min(max_records, industry_cfg["max_override"])

    actor_input: dict[str, Any] = {
        "searchStringsArray":        search_strings_array,
        "locationQuery":             full_location,
        "maxCrawledPlacesPerSearch": max_records,
        "language":                  language,
        "countryCode":               country_code,
        "includeHistogram":          False,
        "includeOpeningHours":       True,
        "includeImages":             False,
        "includePeopleAlsoSearch":   False,
        "exportPlaceUrls":           False,
        "additionalInfo":            False,
        "scrapeDirectories":         False,
        "deeperCityScrape":          False,
        "startUrls":                 [],
    }

    logger.info("Apify | %s | location=%s | max=%d", query_label, full_location, max_records)

    loop   = asyncio.get_running_loop()
    client = ApifyClient(token)

    def _run() -> list[dict]:
        try:
            run = client.actor(ACTOR_ID).call(run_input=actor_input)
        except Exception as e:
            err_str = str(e)
            if "UnauthorizedError" in type(e).__name__ or "authentication token is not valid" in err_str or "401" in err_str:
                raise PermissionError(
                    "Apify API Token is invalid or expired. Please check APIFY_API_TOKEN in .env or backend/.env."
                ) from None
            raise
        if not run:
            logger.error("Apify actor run failed to initialize for %s", query_label)
            return []
        if run.status != "SUCCEEDED":
            logger.warning(
                "Apify run %s finished with status: %s (msg: %s)",
                run.id, run.status, getattr(run, "status_message", "")
            )
        dataset_id = run.default_dataset_id
        if not dataset_id:
            return []
        return list(client.dataset(dataset_id).iterate_items())

    raw_items = await loop.run_in_executor(None, _run)
    logger.info("Apify returned %d raw items for %s", len(raw_items), query_label)

    for raw in raw_items:
        norm = _normalize(raw, query_label, country, added_by, industry_key, city)
        if norm:
            yield norm


def _country_code(country: str | None) -> str:
    if not country:
        return ""
    clean = country.strip().lower()
    mapping = {
        "saudi arabia": "sa", "sa": "sa", "ksa": "sa",
        "uae": "ae", "united arab emirates": "ae",
        "kuwait": "kw", "bahrain": "bh", "qatar": "qa", "oman": "om",
        "egypt": "eg", "jordan": "jo", "india": "in",
        "us": "us", "usa": "us", "united states": "us", "united states of america": "us",
        "uk": "gb", "united kingdom": "gb", "britain": "gb",
        "germany": "de", "singapore": "sg", "malaysia": "my",
        "pakistan": "pk", "turkey": "tr", "morocco": "ma",
        "canada": "ca", "australia": "au", "france": "fr", "italy": "it", "spain": "es",
    }
    if clean in mapping:
        return mapping[clean]
    for name, code in mapping.items():
        if clean.endswith(name) or f", {name}" in clean:
            return code
    return ""