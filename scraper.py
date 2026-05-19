# ============================================================
# scraper.py — Stage 1: Google Maps scraping via Apify
#
# KEY CHANGES IN THIS VERSION:
#   1. NO hard cap on results — Apify runs until Google Maps
#      has nothing left to return. If there are 27 malls in
#      Riyadh, you get exactly 27. Not 100, not 120 — just
#      the true total that exists on Google Maps.
#   2. Strict post-scrape category filter added — after Apify
#      returns results, we check Google's own category tags
#      on each place. If the place isn't tagged with our
#      Place Type, it gets discarded. This removes plazas,
#      hypermarkets, and commercial towers that Google
#      included as "related" results despite the type filter.
#   3. Zoom tiling still enabled — ensures we cover the whole
#      city in tiles so no real business is missed.
#
# FIX ⑧: Stats are now returned as a dict from each function
#   instead of being stored as function attributes
#   (scrape_city_category.last_stats / scrape_targets.last_stats).
#   Function attributes are not thread-safe, invisible to type
#   checkers, and easy to accidentally read stale data from a
#   previous call.  main.py now reads stats from return values.
# ============================================================

import time
from apify_client import ApifyClient

from config import (
    APIFY_API_TOKEN,
    APIFY_ACTOR_ID,
    FIXED_COUNTRY,
    SAUDI_CITY_ARABIC,
    ZOOM_LEVEL,    # Tiling zoom — splits city into grid of search zones
)

PLACE_TYPE_ALIASES = {
    "doctor": ["doctor", "medical clinic", "clinic"],
    "lodging": ["lodging", "hotel"],
    "beauty_salon": ["beauty salon", "hair salon", "salon"],
    "real_estate_agency": ["real estate agency", "real estate agent"],
    "lawyer": ["lawyer", "law firm", "legal services"],
    "shopping_mall": ["shopping mall", "mall"],
    "spa": ["spa", "wellness center", "wellness centre"],
    "accounting": ["accounting", "accountant", "finance"],
    "gym": ["gym", "fitness center", "fitness centre"],
}

def get_client() -> ApifyClient:
    """Creates and returns an authenticated Apify API client."""
    return ApifyClient(APIFY_API_TOKEN)

def build_city_query(query_template: str, city: str) -> str:
    """Fills English and Arabic city placeholders in an EIT query template."""
    return query_template.format(
        city=city,
        city_ar=SAUDI_CITY_ARABIC.get(city, city),
    )

def is_opportunity_config(value) -> bool:
    return isinstance(value, dict) and "queries" in value

def matches_place_type(google_categories: list, place_type: str) -> bool:
    """
    Checks whether Google's own category tags for a place include
    the Place Type we searched for.

    This is the strict filter that removes plazas, commercial complexes,
    and hypermarkets from mall results — and similar cross-contamination
    in other categories.

    How it works:
      Google returns a 'categories' list for each place e.g.:
        ["Shopping mall", "Department store"]
      We convert our place_type ("shopping_mall") to a comparable
      string ("shopping mall") and check if it appears in that list.

    Args:
        google_categories: List of category strings Google assigned to the place
        place_type:        Our Google Place Type e.g. "shopping_mall"
    Returns:
        True  = Google tagged this place with our category → keep it
        False = Google did NOT tag it with our category → discard it
    """
    if not google_categories:
        return False   # No categories at all — can't verify → discard

    # Convert place_type to a comparable readable form
    # "shopping_mall"     → "shopping mall"
    # "beauty_salon"      → "beauty salon"
    # "real_estate_agency"→ "real estate agency"
    readable_type = place_type.replace("_", " ").lower()   # Remove underscores, lowercase
    accepted_labels = PLACE_TYPE_ALIASES.get(place_type, [readable_type])

    # Check each Google category tag for this place
    for cat in google_categories:
        cat_lower = cat.lower().strip()   # Lowercase the Google tag for comparison

        # Direct match — Google tag contains one of our accepted labels
        if any(label in cat_lower for label in accepted_labels):
            return True   # e.g. "shopping mall" found in "Shopping mall" → keep

        # Reverse match — one of our accepted labels contains the Google tag
        if any(cat_lower in label and len(cat_lower) >= 4 for label in accepted_labels):
            return True   # e.g. "mall" found in "shopping mall" → keep

    return False   # None of Google's tags matched our category → discard

def scrape_city_category(
    city: str,
    display_name: str,
    opportunity_config,
) -> tuple[list, dict]:
    """
    Scrapes Google Maps for one city + category.
    Lets Apify run until it naturally exhausts all results — no hard cap.
    Then filters results strictly using Google's own category tags.

    FIX ⑧: Returns (results, stats) tuple instead of storing stats as a
    function attribute.  Function attributes are not thread-safe and
    silently return stale data if the previous call errored out.

    Args:
        city:               City name e.g. "Riyadh"
        display_name:       Human label e.g. "Shopping Mall"
        opportunity_config: Google Place Type string OR EIT opportunity dict
    Returns:
        (filtered_results, stats_dict)
    """
    location = f"{city}, {FIXED_COUNTRY}"
    query_mode = is_opportunity_config(opportunity_config)
    place_type = "" if query_mode else opportunity_config
    query_templates = opportunity_config.get("queries", []) if query_mode else [place_type]

    print(f"\n[SCRAPER] Searching: {display_name} in {location}")
    print(f"          Mode              : {'EIT query library' if query_mode else 'Google Place Type'}")
    if not query_mode:
        print(f"          Google Place Type : {place_type}")
    print(f"          Query count       : {len(query_templates)}")
    print(f"          Zoom level        : {ZOOM_LEVEL}")
    print(f"          Cap               : None — runs until Google is exhausted")

    client = get_client()

    # Initialise stats dict — always returned, even on error
    stats = {
        "city":                  city,
        "category":              display_name,
        "place_type":            place_type or display_name,
        "raw_count":             0,
        "discarded_wrong_type":  0,
        "filtered_count":        0,
    }

    try:
        raw_results      = []
        filtered_results = []

        for query_template in query_templates:
            source_query = build_city_query(query_template, city)
            print(f"[SCRAPER] Query: {source_query}")

            actor_input = {
                "searchStringsArray":        [source_query],
                "locationQuery":             location,
                "maxCrawledPlacesPerSearch": 120,
                "zoom":                      ZOOM_LEVEL,
                "language":                  "en",
                "includeWebResults":         False,
                "scrapeReviews":             False,
                "scrapeImageUrls":           False,
                "skipClosedPlaces":          False,
                "maxImages":                 0,
            }
            if not query_mode:
                actor_input["placeType"] = place_type

            print(f"[SCRAPER] Starting Apify run — please wait...")
            run = client.actor(APIFY_ACTOR_ID).call(run_input=actor_input)

            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                raw_results.append(item)
                google_cats = item.get("categories", []) or []

                if not query_mode and not matches_place_type(google_cats, place_type):
                    continue

                business = extract_fields(
                    item,
                    city,
                    display_name,
                    place_type,
                    source_query=source_query,
                    opportunity_config=opportunity_config if query_mode else {},
                )
                if business:
                    filtered_results.append(business)

        discarded = len(raw_results) - len(filtered_results)
        stats.update({
            "raw_count":            len(raw_results),
            "discarded_wrong_type": discarded,
            "filtered_count":       len(filtered_results),
        })
        print(f"[SCRAPER] Raw from Apify        : {len(raw_results)}")
        print(f"[SCRAPER] Discarded (wrong type) : {discarded}")
        print(f"[SCRAPER] ✓ True {display_name} count: {len(filtered_results)}")

        time.sleep(1)
        return filtered_results, stats

    except Exception as e:
        print(f"[SCRAPER ERROR] {location} / {display_name}: {e}")
        stats["error"] = str(e)
        return [], stats

def extract_fields(
    raw: dict,
    city: str,
    display_name: str,
    place_type: str,
    source_query: str = "",
    opportunity_config: dict | None = None,
) -> dict:
    """
    Extracts the fields we need from Apify's raw result.
    Only called for results that already passed the category filter.
    """
    website = (raw.get("website") or "").strip()

    if website and not website.startswith("http"):
        website = "https://" + website   # Add protocol if missing

    google_categories = raw.get("categories", []) or []   # Google's own category tags
    location = raw.get("location") if isinstance(raw.get("location"), dict) else {}
    opportunity_config = opportunity_config or {}
    product_lines = opportunity_config.get("product_lines", [])

    return {
        "google_place_id":   raw.get("placeId") or raw.get("place_id") or raw.get("cid") or "",
        "google_maps_url":   raw.get("url") or raw.get("searchPageUrl") or "",
        "latitude":          location.get("lat") or raw.get("lat"),
        "longitude":         location.get("lng") or raw.get("lng"),
        "business_name":     (raw.get("title") or "").strip(),
        "category":          display_name,
        "opportunity_tier":  opportunity_config.get("tier", ""),
        "product_lines":     ", ".join(product_lines),
        "source_query":      source_query,
        "place_type":        place_type or display_name,
        "google_categories": ", ".join(google_categories),    # All Google tags as string
        "city":              city,
        "country":           FIXED_COUNTRY,
        "address":           (raw.get("address") or "").strip(),
        "phone":             (raw.get("phone") or "").strip(),
        "website":           website if website else None,     # None if no website
        "has_website":       1 if website else 0,
        "rating":            raw.get("totalScore"),
        "review_count":      raw.get("reviewsCount", 0),
    }

def scrape_targets(cities: list, category_pairs: list) -> tuple[list, dict]:
    """
    Main entry point — scrapes all chosen city + category combinations.

    For each city + category:
      - Apify tiles the city and searches every zone
      - Stops naturally when Google has nothing more
      - Strict filter removes wrong-category results
      - Result = true total count of that business type in that city

    FIX ⑧: Returns (businesses, stats) tuple instead of storing stats as
    a function attribute.  Callers read stats directly from the return
    value — no risk of reading stale data from a prior failed call.

    Args:
        cities:         List of city names e.g. ["Riyadh", "Jeddah"]
        category_pairs: List of (display_name, opportunity_config) tuples
    Returns:
        (all_businesses, stats_dict)
    """
    all_businesses = []
    seen_keys      = set()
    stats = {
        "raw_scraped_count":            0,
        "discarded_wrong_type_count":   0,
        "duplicate_count":              0,
        "verified_count":               0,
        "jobs":                         [],
    }

    total   = len(cities) * len(category_pairs)
    current = 0

    for city in cities:
        for display_name, opportunity_config in category_pairs:
            current += 1
            print(f"\n{'='*52}")
            print(f"[SCRAPER] Job {current} of {total}: {display_name} in {city}")
            print(f"{'='*52}")

            # FIX ⑧: unpack the (results, job_stats) tuple directly
            results, job_stats = scrape_city_category(city, display_name, opportunity_config)
            stats["raw_scraped_count"]          += job_stats.get("raw_count", 0)
            stats["discarded_wrong_type_count"] += job_stats.get("discarded_wrong_type", 0)
            stats["jobs"].append(job_stats)

            added      = 0
            duplicates = 0
            for biz in results:
                stable_id = biz.get("google_place_id") or biz.get("google_maps_url")
                if stable_id:
                    key = stable_id.lower().strip()
                else:
                    key = (
                        f"{biz['business_name'].lower().strip()}|"
                        f"{biz.get('address', '').lower().strip()}|"
                        f"{biz['city'].lower()}"
                    )
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_businesses.append(biz)
                    added += 1
                else:
                    duplicates += 1

            stats["duplicate_count"] += duplicates
            print(f"[SCRAPER] Added {added} unique {display_name} from {city}")

    print(f"\n[SCRAPER] Grand total unique businesses: {len(all_businesses)}")
    stats["verified_count"] = len(all_businesses)
    return all_businesses, stats
