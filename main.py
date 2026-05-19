# ============================================================
# main.py — Master orchestrator
#
# KEY CHANGES IN THIS VERSION:
#   1. Category menu now shows display names ("Shopping Mall")
#      and passes the Google Place Type to scraper internally.
#      User never sees "shopping_mall" — they just pick from
#      a clean numbered list.
#   2. All businesses are checked, but only actionable leads are saved:
#      no website, bad HTTPS/SSL, unreachable sites, or audited websites
#      below the 70% quality gate.
#   3. Good websites are ignored and counted in the final summary.
#   4. Full error tracebacks printed so nothing fails silently.
# ============================================================

import time
import argparse
import traceback
from datetime import datetime

from database import (
    initialize_database,
    save_lead,
    get_lead_count,
    is_already_scraped,
    create_run,
    finalize_run,
    save_business_observation,
    save_ignored_business,
)
from scraper   import scrape_targets
from validator import run_validation, classify_website_status, extract_saudi_phones
from auditor   import audit_website
from ai_engine import (
    analyze_business,
    calculate_lead_score,
    build_bad_reason,
    build_industry_sales_pitch,
)
from exporter  import export_to_csv, export_top_leads, print_summary_report
from contact_utils import build_contact_fields

from config import (
    FIXED_COUNTRY,
    SAUDI_CITIES,
    BUSINESS_CATEGORIES,    # Now a dict: {display_name: place_type}
    QUALITY_LABELS,
    MIN_ACCEPTABLE_SCORE,
    MIN_ACCEPTABLE_UIUX,
)

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
    Runs stages 2–4 for ONE business.

    Saves only actionable leads:
      - No proper website
      - Website unreachable
      - Missing HTTPS or invalid SSL
      - HTTPS + valid SSL website that fails SEO/performance/accessibility/
        best-practices/mobile/UI-UX quality gates

    Good websites are ignored and counted in the pipeline summary.
    """
    name       = business.get("business_name", "?")
    validation = business.get("validation", {})
    status     = classify_website_status(business)

    if status == "blocked_domain":
        audit = {
            "is_weak":      True,
            "issues_found": ["No proper business website — listing points to a social/directory domain"],
            "should_audit": False,
            "html_data":    {},
        }
    else:
        audit = {}

    # Extract Saudi phone numbers from website HTML (if website exists)
    phones = extract_saudi_phones(
        validation.get("html_content", ""),
        business.get("phone", ""),
    )

    # ── Stage 3: Technical audit ──────────────────────────────
    if status in ("valid", "no_https"):
        # Website is reachable — run full PageSpeed + HTML audit
        audit = audit_website(business)

    elif status == "no_website":
        audit = {
            "is_weak":      True,
            "issues_found": ["No website — zero online presence"],
            "should_audit": False,
            "html_data":    {},
        }

    elif status == "unreachable":
        audit = {
            "is_weak":      True,
            "issues_found": ["Website unreachable — server down or domain expired"],
            "should_audit": False,
            "html_data":    {},
        }

    # ── Stage 4: AI analysis ─────────────────────────────────
    # Per your workflow: only sites with HTTPS + valid SSL go through AI.
    has_secure_website = (
        status == "valid"
        and validation.get("https")
        and validation.get("ssl_valid")
        and business.get("website")
    )

    ai_result = {}
    if has_secure_website:
        ai_result = analyze_business(business, audit)
        print(f"  [AI] Analysis generated for secure website")
    else:
        print(f"  [AI] Skipped — no website, unreachable, missing HTTPS, or invalid SSL")

    if has_secure_website and audit_passed(audit, ai_result, validation):
        print(
            f"  [IGNORE] Good website — all measured scores >= {MIN_ACCEPTABLE_SCORE}% "
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

    print("\n" + "=" * 55)
    print("  PIPELINE STARTING")
    print(f"  Country : {FIXED_COUNTRY}")
    print(f"  Cities  : {', '.join(cities)}")
    print(f"  Types   : {', '.join(p[0] for p in category_pairs)}")
    print("=" * 55 + "\n")

    # Init DB
    initialize_database()
    run_id = create_run(cities, category_pairs, FIXED_COUNTRY)
    print(f"[RUN] Started run #{run_id}")

    # Stage 1: Scrape with zoom tiling
    print("[STAGE 1] Scraping Google Maps with zoom tiling...\n")
    businesses = scrape_targets(cities, category_pairs)
    scrape_stats = getattr(scrape_targets, "last_stats", {})
    # scrape_targets() uses zoom to get full city coverage
    # category_pairs are (display_name, place_type) tuples

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

    for business in businesses:
        save_business_observation(business, run_id)

    # Stage 2: Validate all websites in parallel
    print(f"[STAGE 2] Validating {total} websites in parallel...")
    businesses = run_validation(businesses)
    print("[STAGE 2] Validation complete\n")

    # Stages 3 + 4: Audit every business, save only actionable leads
    print("[STAGES 3+4] Auditing all businesses and filtering good websites...\n")
    saved        = 0
    skipped      = 0
    ignored_good = 0
    errors       = 0

    for idx, business in enumerate(businesses):
        name = business.get("business_name", "?")
        print(f"[{idx + 1}/{total}] {name}")

        if is_already_scraped(
            name,
            business.get("city", ""),
            business.get("google_place_id", ""),
        ):
            print(f"  [DUP] Already in database")
            skipped += 1
            continue

        try:
            lead, action, context = process_one(business, run_id)
            if lead:
                if save_lead(lead):
                    saved += 1
                else:
                    skipped += 1
            else:
                if action == "ignored_good":
                    save_ignored_business(
                        business,
                        run_id,
                        context.get("reason", "ignored_good"),
                        context.get("audit", {}),
                        context.get("ai_result", {}),
                    )
                    ignored_good += 1
                else:
                    skipped += 1

        except Exception as e:
            errors += 1
            print(f"  [ERROR] {e}")
            print(traceback.format_exc())   # Full traceback for debugging

    finalize_run(
        run_id=run_id,
        scraped_count=total,
        saved_leads_count=saved,
        ignored_good_count=ignored_good,
        skipped_count=skipped,
        error_count=errors,
        raw_scraped_count=scrape_stats.get("raw_scraped_count", total),
        discarded_wrong_type_count=scrape_stats.get("discarded_wrong_type_count", 0),
        duplicate_count=scrape_stats.get("duplicate_count", 0),
    )

    # Stage 5: Export
    print(f"\n[STAGE 5] Exporting to CSV...")
    csv_all = export_to_csv()
    csv_top = export_top_leads(60)   # Top leads = score 60+ (needs attention)

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
    print(f"  Saved        : {saved}")
    print(f"  Ignored good : {ignored_good}")
    print(f"  Skipped      : {skipped}")
    print(f"  Errors       : {errors}")
    print(f"  Total in DB  : {get_lead_count()}")
    print(f"  Full CSV     : {csv_all}")
    print(f"  Top CSV      : {csv_top or 'None'}")
    print("=" * 55 + "\n")

# ═══════════════════════════════════════════════════════════
# CLI FLAGS
# ═══════════════════════════════════════════════════════════

def build_parser():
    parser = argparse.ArgumentParser(description=f"Lead Intelligence — {FIXED_COUNTRY}")
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--top-leads", type=float, default=None)
    return parser

if __name__ == "__main__":
    parser = build_parser()
    args   = parser.parse_args()

    if args.report:
        initialize_database()
        print_summary_report()
    elif args.export_only:
        initialize_database()
        print(f"Exported: {export_to_csv()}")
    elif args.top_leads is not None:
        initialize_database()
        print(f"Top leads: {export_top_leads(args.top_leads)}")
    else:
        cities, category_pairs = run_interactive_setup()
        run_pipeline(cities, category_pairs)
