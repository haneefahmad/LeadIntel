# ============================================================
# main.py — Master orchestrator
#
# KEY CHANGES IN THIS VERSION:
#   1. Category menu shows display names ("Shopping Mall") and
#      passes the Google Place Type to scraper internally.
#   2. Only actionable leads are saved: no website, bad HTTPS/SSL,
#      unreachable sites, or sites below the 70% quality gate.
#   3. Good websites are ignored and counted in the final summary.
#   4. Full error tracebacks printed so nothing fails silently.
#
# FIXES IN THIS VERSION:
#   ④  Audit routing consolidated into one clean if/elif block
#      inside process_one — no more split logic across two chains.
#   ①  AI analysis now runs for ALL lead types: no-website leads
#      get the "build a site" pitch; weak/insecure sites get the
#      full technical analysis. build_no_website_prompt() is no
#      longer dead code.
#   ⑦  Stage 3 now calls run_audit_all() which batches all PSI
#      requests concurrently before the per-business loop — audits
#      run in parallel instead of one by one.
#   ⑥  save_business_observation replaced with batch insert:
#      save_business_observations_batch() — one DB connection for
#      all scraped businesses instead of one per business.
# ============================================================

import re
import time
import argparse
import traceback
from datetime import datetime

from database import (
    initialize_database,
    save_lead,
    get_lead_count,
    find_existing_lead,                  # Change detection: returns full record or None
    update_lead,                         # Change detection: update fields in-place
    log_lead_changes,                    # Change detection: write audit trail
    create_run,
    finalize_run,
    save_business_observations_batch,
    save_ignored_business,
)
from scraper   import scrape_targets
from validator import run_validation, classify_website_status, extract_saudi_phones
from auditor   import run_audit_all   # FIX ⑦: concurrent PSI batch
from ai_engine import (
    analyze_business,
    calculate_lead_score,
    build_bad_reason,
    build_industry_sales_pitch,
)
from exporter  import export_to_xlsx, print_summary_report
from contact_utils import build_contact_fields

import config   # Imported as module so we can override config.DB_PATH at runtime
from config import (
    FIXED_COUNTRY,
    SAUDI_CITIES,
    BUSINESS_CATEGORIES,    # Now a dict: {display_name: opportunity_config}
    QUALITY_LABELS,
    MIN_ACCEPTABLE_SCORE,
    MIN_ACCEPTABLE_UIUX,
    PSI_CONCURRENT_LIMIT,   # For progress logging in run_pipeline
)

# ═══════════════════════════════════════════════════════════
# RUN SLUG — dynamic file naming
# ═══════════════════════════════════════════════════════════

def generate_run_slug(cities: list, category_pairs: list) -> str:
    """
    Creates a clean filename slug from the selected categories and cities.

    Examples:
      cities = ["Riyadh", "Jeddah"],
      categories = [("Construction & Contracting", ...), ("Healthcare", ...)]
      → "construction_contracting_healthcare_riyadh_jeddah"

    Used as the base name for both the SQLite DB and the XLSX export:
      construction_contracting_healthcare_riyadh_jeddah.db
      construction_contracting_healthcare_riyadh_jeddah.xlsx
    """
    def slugify(text: str) -> str:
        """Lowercases and replaces non-alphanumeric runs with underscores."""
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

    parts = [slugify(display_name) for display_name, _ in category_pairs]
    parts += [slugify(city) for city in cities]
    slug = "_".join(parts)
    return slug[:80]   # Safety cap — keeps filenames reasonable on all OS


# ═══════════════════════════════════════════════════════════
# QUALITY LABEL HELPER
# ═══════════════════════════════════════════════════════════

def get_quality_label(lead_score: float) -> str:
    """
    Returns a human-readable quality label based on the lead score.
    Defined in QUALITY_LABELS in config.py.
    Used in the CSV so the client can filter instantly.
    """
    for (low, high), label in QUALITY_LABELS.items():
        if low <= lead_score <= high:
            return label
    return "Unknown"

# ═══════════════════════════════════════════════════════════
# CHANGE DETECTION
# ═══════════════════════════════════════════════════════════

# Fields compared on every re-run to detect meaningful changes.
# Excludes internal IDs, timestamps, and static identifiers.
TRACKED_FIELDS = [
    "website",
    "https_enabled",
    "ssl_valid",
    "seo_score",
    "performance_score",
    "accessibility_score",
    "best_practices_score",
    "mobile_friendly",
    "phone",
    "contact_phone",
    "whatsapp_number",
    "primary_email",
    "email_status",
    "rating",
    "review_count",
    "lead_score",
    "lead_type",
    "issues_found",
    "ai_uiux_score",
]


def detect_changes(existing: dict, new_lead: dict) -> tuple[list, str]:
    """
    Compares TRACKED_FIELDS between the stored record and the freshly
    processed lead.  Returns:
      - changes: list of {field, old, new} dicts for every field that differs
      - summary: human-readable string for the changes_detected column
                 e.g. "https_enabled: NO→YES; seo_score: 43.0→71.0"

    String-casts both sides before comparing so 1 == "1" does not
    falsely trigger a change (SQLite returns ints, Python may produce
    a bool or float for the same field).
    """
    changes = []
    for field in TRACKED_FIELDS:
        old_val = existing.get(field)
        new_val = new_lead.get(field)
        if str(old_val) != str(new_val):
            changes.append({"field": field, "old": old_val, "new": new_val})

    summary = "; ".join(
        f"{c['field']}: {c['old']} → {c['new']}" for c in changes
    ) if changes else ""

    return changes, summary


# ═══════════════════════════════════════════════════════════
# INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════

def divider():
    print("\n" + "─" * 55)

def ask_cities() -> list:
    """
    Shows numbered Saudi city list.
    Returns list of chosen city name strings.
    """
    divider()
    print(f"  STEP 1 — Choose cities in {FIXED_COUNTRY}\n")

    for i, city in enumerate(SAUDI_CITIES, start=1):
        print(f"  {i:>2}. {city}")
    print(f"\n  all. All {len(SAUDI_CITIES)} cities")

    while True:
        raw = input("\n  Enter number(s) e.g. 1 or 1,3,5 or 'all': ").strip().lower()
        if not raw:
            print("  Please make a selection.")
            continue

        if raw == "all":
            print(f"  Selected all {len(SAUDI_CITIES)} cities.")
            return list(SAUDI_CITIES)

        parts  = [p.strip() for p in raw.split(",")]
        chosen = []
        valid  = True
        for part in parts:
            if not part.isdigit():
                print(f"  '{part}' is not valid. Enter numbers only.")
                valid = False
                break
            idx = int(part)
            if 1 <= idx <= len(SAUDI_CITIES):
                city = SAUDI_CITIES[idx - 1]
                if city not in chosen:
                    chosen.append(city)
            else:
                print(f"  {part} out of range (1–{len(SAUDI_CITIES)}).")
                valid = False
                break

        if valid and chosen:
            print(f"  Selected: {', '.join(chosen)}")
            return chosen

def ask_categories() -> list:
    """
    Shows numbered EIT opportunity groups.
    Returns list of (display_name, opportunity_config) tuples.
    """
    divider()
    print("  STEP 2 — Choose EIT product opportunity groups\n")

    display_names = list(BUSINESS_CATEGORIES.keys())
    opportunity_configs = list(BUSINESS_CATEGORIES.values())

    # Print in two columns
    half = (len(display_names) + 1) // 2
    for i in range(half):
        left_i  = i
        right_i = i + half
        left_s  = f"  {left_i + 1:>2}. {display_names[left_i]:<28}"
        if right_i < len(display_names):
            right_s = f"{right_i + 1:>2}. {display_names[right_i]}"
            print(left_s + right_s)
        else:
            print(left_s)

    print(f"\n  all. All {len(display_names)} opportunity groups")

    while True:
        raw = input("\n  Enter number(s) e.g. 1 or 1,3,5 or 'all': ").strip().lower()
        if not raw:
            print("  Please make a selection.")
            continue

        if raw == "all":
            pairs = list(BUSINESS_CATEGORIES.items())   # All (display, type) pairs
            print(f"  Selected all {len(pairs)} opportunity groups.")
            return pairs

        parts  = [p.strip() for p in raw.split(",")]
        chosen = []
        valid  = True
        for part in parts:
            if not part.isdigit():
                print(f"  '{part}' is not valid. Enter numbers only.")
                valid = False
                break
            idx = int(part)
            if 1 <= idx <= len(display_names):
                pair = (display_names[idx - 1], opportunity_configs[idx - 1])
                if pair not in chosen:
                    chosen.append(pair)
            else:
                print(f"  {part} out of range (1–{len(display_names)}).")
                valid = False
                break

        if valid and chosen:
            labels = [p[0] for p in chosen]
            print(f"  Selected: {', '.join(labels)}")
            return chosen

def confirm_run(cities: list, category_pairs: list) -> bool:
    """Shows summary and asks for confirmation before running."""
    divider()
    print("  CONFIRM YOUR SELECTIONS\n")
    print(f"  Country        : {FIXED_COUNTRY}")
    print(f"  Cities         : {', '.join(cities)}")
    print(f"  Opportunities  : {', '.join(p[0] for p in category_pairs)}")
    runs = sum(len(p[1].get("queries", [])) for p in category_pairs) * len(cities)
    print(f"\n  Apify queries  : {runs}")
    print(f"  Est. Apify cost: ~${runs * 0.50:.2f} – ${runs * 2.00:.2f}")
    print(f"  (Cost is higher with zoom tiling — more results per run)")

    while True:
        ans = input("\n  Proceed? (yes / no / restart): ").strip().lower()
        if ans in ("yes", "y"): return True
        if ans in ("no", "n"):
            print("  Cancelled.")
            exit(0)
        if ans in ("restart", "r"): return False
        print("  Type yes, no, or restart.")

def run_interactive_setup() -> tuple:
    """Runs the two-step menu and returns (cities, category_pairs) once confirmed."""
    print("\n" + "=" * 55)
    print(f"  LEAD INTELLIGENCE — {FIXED_COUNTRY.upper()}")
    print("=" * 55)

    while True:
        cities         = ask_cities()
        category_pairs = ask_categories()
        if confirm_run(cities, category_pairs):
            return cities, category_pairs

# ═══════════════════════════════════════════════════════════
# SINGLE BUSINESS PROCESSOR
# ═══════════════════════════════════════════════════════════

def audit_passed(audit: dict, ai_result: dict, validation: dict) -> bool:
    """
    Returns True only when the business website clears the "ignore good sites" gate.
    All required numeric scores must be at least MIN_ACCEPTABLE_SCORE, SSL must be
    valid, mobile friendliness must pass, and AI UI/UX must be at least 7/10.
    Missing scores are treated as not passing because the audit is incomplete.
    """
    required_scores = [
        audit.get("seo_score"),
        audit.get("performance_score"),
        audit.get("accessibility_score"),
        audit.get("best_practices_score"),
    ]

    scores_ok = all(
        score is not None and score >= MIN_ACCEPTABLE_SCORE
        for score in required_scores
    )
    mobile_ok = audit.get("mobile_friendly") == 1
    ssl_ok = validation.get("https") and validation.get("ssl_valid")
    uiux_ok = (ai_result.get("ai_uiux_score") or 0) >= MIN_ACCEPTABLE_UIUX

    return bool(scores_ok and mobile_ok and ssl_ok and uiux_ok)


def get_lead_type(status: str, validation: dict, audit: dict) -> str:
    """Classifies the lead into a sales-friendly reason bucket."""
    if status == "blocked_domain":
        return "no_proper_website"
    if status == "no_website":
        return "no_website"
    if status == "unreachable":
        return "unreachable_website"
    if not validation.get("https"):
        return "no_https"
    if validation.get("https") and not validation.get("ssl_valid"):
        return "invalid_ssl"
    if audit.get("is_weak"):
        return "weak_website"
    return "needs_review"


def process_one(business: dict, run_id: int) -> tuple[dict | None, str, dict]:
    """
    Runs stages 3–4 for ONE business.
    Stage 3 (PSI audit) is pre-computed by run_audit_all() and attached
    as business["audit"] before this function is called.

    Saves only actionable leads:
      - No proper website
      - Website unreachable
      - Missing HTTPS or invalid SSL
      - HTTPS + valid SSL website that fails SEO/performance/accessibility/
        best-practices/mobile/UI-UX quality gates

    Good websites are ignored and counted in the pipeline summary.

    FIX ④: Audit routing consolidated into one clean if/elif block —
    no more split logic between the old if/else and the later elif chain.

    FIX ①: AI now runs for ALL lead types.  no_website / blocked /
    unreachable leads get the "build a site" pitch via
    build_no_website_prompt().  Weak / insecure sites get the full
    technical analysis via build_weak_site_prompt().
    build_no_website_prompt() is no longer dead code.
    """
    name       = business.get("business_name", "?")
    validation = business.get("validation", {})
    status     = classify_website_status(business)

    # ── Stage 3: Use pre-computed audit (attached by run_audit_all) ──
    # FIX ④: Single consolidated routing — no split chains.
    audit = business.get("audit")
    if audit is None:
        # Safety fallback: should not happen if run_audit_all was called,
        # but we guard defensively so the pipeline never crashes here.
        if status in ("valid", "no_https"):
            # Import here only as a fallback to avoid circular import issues
            from auditor import audit_website as _audit_website
            audit = _audit_website(business)
        elif status == "no_website":
            audit = {
                "is_weak": True,
                "issues_found": ["No website — zero online presence"],
                "should_audit": False, "html_data": {},
                "seo_score": None, "performance_score": None,
                "accessibility_score": None, "best_practices_score": None,
                "mobile_friendly": None,
            }
        elif status == "unreachable":
            audit = {
                "is_weak": True,
                "issues_found": ["Website unreachable — server down or domain expired"],
                "should_audit": False, "html_data": {},
                "seo_score": None, "performance_score": None,
                "accessibility_score": None, "best_practices_score": None,
                "mobile_friendly": None,
            }
        elif status == "blocked_domain":
            audit = {
                "is_weak": True,
                "issues_found": ["No proper business website — listing points to a social/directory domain"],
                "should_audit": False, "html_data": {},
                "seo_score": None, "performance_score": None,
                "accessibility_score": None, "best_practices_score": None,
                "mobile_friendly": None,
            }
        else:
            audit = {
                "is_weak": False, "issues_found": [], "should_audit": False,
                "html_data": {}, "seo_score": None, "performance_score": None,
                "accessibility_score": None, "best_practices_score": None,
                "mobile_friendly": None,
            }

    # Extract Saudi phone numbers from website HTML (if website exists)
    phones = extract_saudi_phones(
        validation.get("html_content", ""),
        business.get("phone", ""),
    )

    # ── Stage 4: AI analysis ─────────────────────────────────
    # FIX ①: Run AI for ALL actionable lead types, not just secure sites.
    #
    #  no_website / blocked_domain → build_no_website_prompt()
    #    → tailored "build a site" pitch with specific digital risks
    #  unreachable               → build_no_website_prompt()
    #    → "your site is down" pitch
    #  no_https / valid (weak)   → build_weak_site_prompt()
    #    → full technical analysis with root causes + roadmap
    #
    # analyze_business() already picks the right prompt internally based on
    # has_website + was_audited — we just need to always call it.
    #
    # Only skip AI for sites that pass the quality gate (good websites).

    should_run_ai = (
        status in ("no_website", "blocked_domain", "unreachable")  # needs pitch prompt
        or audit.get("is_weak")                                    # failed quality checks
        or (status in ("valid", "no_https") and audit.get("should_audit"))  # audited site
    )

    ai_result = {}
    if should_run_ai:
        ai_result = analyze_business(business, audit)
        print(f"  [AI] Analysis generated ({status})")
    else:
        print(f"  [AI] Skipped — website appears healthy, checking quality gate")

    # ── Quality gate: ignore genuinely good websites ──────────
    # Only applies to sites that are reachable, HTTPS, valid SSL,
    # AND passed all score thresholds AND AI UI/UX >= minimum.
    is_secure = (
        status == "valid"
        and validation.get("https")
        and validation.get("ssl_valid")
    )
    if is_secure and audit_passed(audit, ai_result, validation):
        print(
            f"  [IGNORE] Good website — all scores >= {MIN_ACCEPTABLE_SCORE}% "
            f"and AI UI/UX >= {MIN_ACCEPTABLE_UIUX}/10"
        )
        return None, "ignored_good", {
            "reason": "all_quality_scores_passed",
            "audit": audit,
            "ai_result": ai_result,
        }

    lead_score    = calculate_lead_score(business, audit, ai_result)
    quality_label = get_quality_label(lead_score)   # Human-readable label for CSV

    html_data = audit.get("html_data", {})
    contact_fields = build_contact_fields(business, html_data, phones)
    bad_reason = ai_result.get("bad_reason") or build_bad_reason(business, audit, ai_result)
    industry_sales_pitch = (
        ai_result.get("industry_sales_pitch")
        or build_industry_sales_pitch(business, audit, ai_result)
    )

    # Build record only for actionable businesses
    lead = {
        "run_id":                run_id,
        "google_place_id":      business.get("google_place_id", ""),
        "google_maps_url":      business.get("google_maps_url", ""),
        "business_name":         business.get("business_name", ""),
        "category":              business.get("category", ""),
        "opportunity_tier":      business.get("opportunity_tier", ""),
        "product_lines":         business.get("product_lines", ""),
        "source_query":          business.get("source_query", ""),
        "place_type":            business.get("place_type", ""),
        "google_categories":     business.get("google_categories", ""),
        "city":                  business.get("city", ""),
        "country":               business.get("country", FIXED_COUNTRY),
        "address":               business.get("address", ""),
        "phone":                 ", ".join(phones) if phones else business.get("phone", ""),
        "contact_phone":         contact_fields["contact_phone"],
        "landline_number":       contact_fields["landline_number"],
        "whatsapp_number":       contact_fields["whatsapp_number"],
        "website":               business.get("website") or None,
        "primary_email":         contact_fields["primary_email"],
        "email_status":          contact_fields["email_status"],
        "email_confidence":      contact_fields["email_confidence"],
        "email_source_url":      contact_fields["email_source_url"],
        "email_verification_provider": contact_fields["email_verification_provider"],
        "email_checked_at":      contact_fields["email_checked_at"],
        "hunter_status":         contact_fields["hunter_status"],
        "hunter_score":          contact_fields["hunter_score"],
        "hunter_result":         contact_fields["hunter_result"],
        "linkedin_company_url":  contact_fields["linkedin_company_url"],
        "decision_maker_linkedin": contact_fields["decision_maker_linkedin"],
        "rating":                business.get("rating"),
        "review_count":          business.get("review_count"),
        "has_website":           1 if business.get("website") else 0,
        "emails":                ", ".join(html_data.get("emails", [])),
        "social_links":          html_data.get("social_links", {}),
        "https_enabled":         1 if validation.get("https") else 0,
        "ssl_valid":             1 if validation.get("ssl_valid") else 0,
        "seo_score":             audit.get("seo_score"),
        "performance_score":     audit.get("performance_score"),
        "accessibility_score":   audit.get("accessibility_score"),
        "best_practices_score":  audit.get("best_practices_score"),
        "mobile_friendly":       audit.get("mobile_friendly"),
        "issues_found":          audit.get("issues_found", []),
        "website_quality":       quality_label,     # e.g. "High — Multiple serious problems"
        "bad_reason":            bad_reason,
        "ai_uiux_score":         ai_result.get("ai_uiux_score"),
        "ai_analysis":           ai_result.get("ai_analysis"),
        "industry_sales_pitch":  industry_sales_pitch,
        "ai_sales_pitch":        ai_result.get("ai_sales_pitch"),    # Empty if good website
        "ai_whatsapp_msg":       ai_result.get("ai_whatsapp_msg"),   # Empty if good website
        "lead_score":            lead_score,
        "lead_type":             get_lead_type(status, validation, audit),
        "has_changes":           0,     # 0 on first insert; set to 1 if updated on re-run
        "changes_detected":      "",    # Empty on first run; filled on re-runs
        "status":                "new",
        "last_checked_at":       datetime.now().isoformat(timespec="seconds"),
    }

    print(f"  [ACTIONABLE] Score: {lead_score} | Quality: {quality_label}")
    return lead, "actionable", {
        "reason": "actionable_lead",
        "audit": audit,
        "ai_result": ai_result,
    }

# ═══════════════════════════════════════════════════════════
# FULL PIPELINE
# ═══════════════════════════════════════════════════════════

def run_pipeline(cities: list, category_pairs: list):
    """
    Runs all 5 stages. Saves actionable leads and counts ignored good websites.
    """
    start = time.time()

    # ── Dynamic file naming ──────────────────────────────────
    # Both the database and the XLSX export are named after the
    # selected categories and cities, so different runs never
    # overwrite each other.
    #
    # e.g. "construction_contracting_healthcare_riyadh.db"
    #      "construction_contracting_healthcare_riyadh.xlsx"
    run_slug     = generate_run_slug(cities, category_pairs)
    here         = config._HERE   # Same directory as config.py (the project folder)
    config.DB_PATH  = str(here / f"{run_slug}.db")    # Override BEFORE initialize_database()
    xlsx_path    = str(here / f"{run_slug}.xlsx")

    print("\n" + "=" * 55)
    print("  PIPELINE STARTING")
    print(f"  Country   : {FIXED_COUNTRY}")
    print(f"  Cities    : {', '.join(cities)}")
    print(f"  Types     : {', '.join(p[0] for p in category_pairs)}")
    print(f"  Database  : {run_slug}.db")
    print(f"  Output    : {run_slug}.xlsx")
    print("=" * 55 + "\n")

    # Init DB (uses the overridden config.DB_PATH set above)
    initialize_database()
    run_id = create_run(cities, category_pairs, FIXED_COUNTRY)
    print(f"[RUN] Started run #{run_id}")

    # Stage 1: Scrape with zoom tiling
    print("[STAGE 1] Scraping Google Maps with zoom tiling...\n")
    # FIX ⑧: unpack (businesses, stats) — no more function attribute
    businesses, scrape_stats = scrape_targets(cities, category_pairs)

    total = len(businesses)
    print(f"\n[STAGE 1] Total scraped: {total}\n")

    if not total:
        print("[ERROR] Nothing scraped. Check APIFY_API_TOKEN in config.py")
        finalize_run(
            run_id=run_id,
            scraped_count=0,
            saved_leads_count=0,
            ignored_good_count=0,
            skipped_count=0,
            error_count=1,
            raw_scraped_count=scrape_stats.get("raw_scraped_count", 0),
            discarded_wrong_type_count=scrape_stats.get("discarded_wrong_type_count", 0),
            duplicate_count=scrape_stats.get("duplicate_count", 0),
            notes="No businesses scraped",
        )
        return

    # FIX ⑥: One batch insert instead of one DB connection per business
    save_business_observations_batch(businesses, run_id)

    # Stage 2: Validate all websites in parallel
    print(f"[STAGE 2] Validating {total} websites in parallel...")
    businesses = run_validation(businesses)
    print("[STAGE 2] Validation complete\n")

    # Stage 3: Audit all websites concurrently (PSI calls in parallel)
    # FIX ⑦: run_audit_all batches all PSI requests with a semaphore
    # instead of calling them one at a time inside process_one.
    print(f"[STAGE 3] Running concurrent PSI audits (max {PSI_CONCURRENT_LIMIT} parallel)...")
    businesses = run_audit_all(businesses)
    print("[STAGE 3] Audits complete\n")

    # Stage 4: AI analysis + scoring + save/update — one business at a time
    print("[STAGES 4+5] AI analysis, scoring, and saving...\n")
    saved        = 0   # Genuinely new leads added
    updated      = 0   # Existing leads where something changed
    unchanged    = 0   # Existing leads with no changes — skipped
    ignored_good = 0   # Good websites ignored by quality gate
    errors       = 0

    for idx, business in enumerate(businesses):
        name = business.get("business_name", "?")
        print(f"[{idx + 1}/{total}] {name}")

        try:
            lead, action, context = process_one(business, run_id)

            # ── Good website — ignore, don't save ────────────────
            if action == "ignored_good":
                save_ignored_business(
                    business,
                    run_id,
                    context.get("reason", "ignored_good"),
                    context.get("audit", {}),
                    context.get("ai_result", {}),
                )
                ignored_good += 1
                continue

            if not lead:
                continue

            # ── Check if this business already exists in the DB ──
            existing = find_existing_lead(
                name,
                business.get("city", ""),
                business.get("google_place_id", ""),
            )

            if existing:
                # Business already in DB — detect what changed
                changes, summary = detect_changes(existing, lead)
                if changes:
                    # Build dict of only the changed fields to update
                    changed_fields = {c["field"]: lead.get(c["field"]) for c in changes}
                    # Also refresh scores and pitches even if not in TRACKED_FIELDS
                    for always_refresh in (
                        "ai_analysis", "ai_sales_pitch", "ai_whatsapp_msg",
                        "industry_sales_pitch", "bad_reason", "website_quality",
                        "issues_found", "lead_score",
                    ):
                        changed_fields[always_refresh] = lead.get(always_refresh)

                    changed_fields["has_changes"] = 1   # Flag: something changed this run

                    update_lead(existing["id"], changed_fields, summary)
                    log_lead_changes(existing["id"], run_id, changes)
                    updated += 1
                    print(f"  [UPDATED] {len(changes)} change(s): {summary[:100]}")
                else:
                    unchanged += 1
                    print(f"  [UNCHANGED] No changes detected")
            else:
                # Brand new business — insert as new lead
                if save_lead(lead):
                    saved += 1
                    print(f"  [NEW] Score: {lead.get('lead_score')} | {lead.get('website_quality', '')}")

        except Exception as e:
            errors += 1
            print(f"  [ERROR] {e}")
            print(traceback.format_exc())   # Full traceback for debugging

    finalize_run(
        run_id=run_id,
        scraped_count=total,
        saved_leads_count=saved,
        ignored_good_count=ignored_good,
        skipped_count=unchanged,         # "skipped" now means "unchanged existing"
        error_count=errors,
        raw_scraped_count=scrape_stats.get("raw_scraped_count", total),
        discarded_wrong_type_count=scrape_stats.get("discarded_wrong_type_count", 0),
        duplicate_count=scrape_stats.get("duplicate_count", 0),
        notes=f"updated={updated}",
    )

    # Stage 5: Export to XLSX (single file — no top-leads split)
    print(f"\n[STAGE 5] Exporting results to Excel...")
    xlsx_out = export_to_xlsx(xlsx_path)

    elapsed = round(time.time() - start, 1)
    print_summary_report()

    print("=" * 55)
    print("  PIPELINE COMPLETE")
    print(f"  Runtime      : {elapsed}s")
    print(f"  Run ID       : {run_id}")
    print(f"  Scraped      : {total}")
    print(f"  Raw scraped  : {scrape_stats.get('raw_scraped_count', total)}")
    print(f"  Wrong type   : {scrape_stats.get('discarded_wrong_type_count', 0)}")
    print(f"  Duplicates   : {scrape_stats.get('duplicate_count', 0)}")
    print(f"  ── Results ──────────────────────────")
    print(f"  New leads    : {saved}")
    print(f"  Updated      : {updated}  (existing — something changed)")
    print(f"  Unchanged    : {unchanged}  (existing — no changes)")
    print(f"  Ignored good : {ignored_good}")
    print(f"  Errors       : {errors}")
    print(f"  Total in DB  : {get_lead_count()}")
    print(f"  Database     : {config.DB_PATH}")
    print(f"  Excel export : {xlsx_out or 'None'}")
    print("=" * 55 + "\n")

# ═══════════════════════════════════════════════════════════
# CLI FLAGS
# ═══════════════════════════════════════════════════════════

def build_parser():
    parser = argparse.ArgumentParser(description=f"Lead Intelligence — {FIXED_COUNTRY}")
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Re-export the existing DB to XLSX without scraping. "
             "Requires --slug to identify which DB to open.",
    )
    parser.add_argument(
        "--slug",
        type=str,
        default=None,
        help="Run slug used to locate the database and name the XLSX output. "
             "e.g. construction_contracting_riyadh",
    )
    parser.add_argument("--report", action="store_true", help="Print summary report to terminal.")
    return parser

if __name__ == "__main__":
    parser = build_parser()
    args   = parser.parse_args()

    if args.report:
        # Use slug if provided, otherwise default DB path from config
        if args.slug:
            config.DB_PATH = str(config._HERE / f"{args.slug}.db")
        initialize_database()
        print_summary_report()

    elif args.export_only:
        if not args.slug:
            print("[ERROR] --export-only requires --slug  e.g. --slug construction_riyadh")
            raise SystemExit(1)
        config.DB_PATH = str(config._HERE / f"{args.slug}.db")
        xlsx_path      = str(config._HERE / f"{args.slug}.xlsx")
        initialize_database()
        out = export_to_xlsx(xlsx_path)
        print(f"Exported: {out}")

    else:
        cities, category_pairs = run_interactive_setup()
        run_pipeline(cities, category_pairs)
