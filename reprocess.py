# ============================================================
# reprocess.py — Re-run Stages 2–5 on existing database records
#
# USE THIS when your dataset is inconsistent because:
#   - Groq API wasn't working (no real AI pitches, UI/UX = 0)
#   - PSI quota ran out (missing SEO/Performance scores)
#   - Any API was misconfigured on the first run
#
# Skips Stage 1 (Apify) entirely — zero scraping cost.
# Reads all existing leads from the DB, re-validates websites,
# re-audits with PSI, re-generates AI analysis, and updates
# every record in-place.
#
# Usage:
#   python reprocess.py construction_contracting_riyadh
#
# The slug must match an existing .db file in the project folder.
# ============================================================

import sys
import json
import traceback
from datetime import datetime

# ── Must set DB path BEFORE importing database ───────────────
import config
from pathlib import Path

if len(sys.argv) < 2:
    print("\nUsage: python reprocess.py <slug>")
    print("Example: python reprocess.py construction_contracting_riyadh\n")
    print("The slug must match an existing database file, e.g.")
    print("  construction_contracting_riyadh.db\n")
    sys.exit(1)

slug = sys.argv[1].strip()
db_path = config._HERE / f"{slug}.db"

if not db_path.exists():
    print(f"\n[ERROR] Database not found: {db_path}")
    print("Check the slug matches one of these files:")
    for f in config._HERE.glob("*.db"):
        print(f"  {f.stem}")
    sys.exit(1)

config.DB_PATH = str(db_path)
xlsx_path      = str(config._HERE / f"{slug}.xlsx")

# ── Now safe to import everything ────────────────────────────
from database import (
    initialize_database,
    get_all_leads,
    update_lead,
    log_lead_changes,
    get_lead_count,
)
from validator    import run_validation, classify_website_status, extract_saudi_phones
from auditor      import run_audit_all
from ai_engine    import (
    analyze_business,
    calculate_lead_score,
    build_bad_reason,
    build_industry_sales_pitch,
)
from exporter     import export_to_xlsx, print_summary_report
from contact_utils import build_contact_fields
from config        import FIXED_COUNTRY, QUALITY_LABELS, MIN_ACCEPTABLE_SCORE, MIN_ACCEPTABLE_UIUX


# ── HELPERS (mirrors main.py) ─────────────────────────────────

def get_quality_label(lead_score: float) -> str:
    for (low, high), label in QUALITY_LABELS.items():
        if low <= lead_score <= high:
            return label
    return "Unknown"


def get_lead_type(status: str, validation: dict, audit: dict) -> str:
    if status == "blocked_domain":  return "no_proper_website"
    if status == "no_website":      return "no_website"
    if status == "unreachable":     return "unreachable_website"
    if not validation.get("https"): return "no_https"
    if validation.get("https") and not validation.get("ssl_valid"): return "invalid_ssl"
    if audit.get("is_weak"):        return "weak_website"
    return "needs_review"


TRACKED_FIELDS = [
    "website", "https_enabled", "ssl_valid",
    "seo_score", "performance_score", "accessibility_score", "best_practices_score",
    "mobile_friendly", "phone", "contact_phone", "whatsapp_number",
    "primary_email", "email_status", "rating", "review_count",
    "lead_score", "lead_type", "issues_found", "ai_uiux_score",
]


def detect_changes(existing: dict, new_lead: dict) -> tuple:
    changes = []
    for field in TRACKED_FIELDS:
        old_val = existing.get(field)
        new_val = new_lead.get(field)
        if str(old_val) != str(new_val):
            changes.append({"field": field, "old": old_val, "new": new_val})
    summary = "; ".join(f"{c['field']}: {c['old']} → {c['new']}" for c in changes)
    return changes, summary


# ── CONVERT DB LEAD BACK TO BUSINESS DICT ────────────────────

def lead_to_business(lead: dict) -> dict:
    """
    Converts a stored lead record back into the business dict format
    that Stages 2–4 expect as input.
    Attaches _lead_id so we know which DB row to update afterwards.
    """
    return {
        "_lead_id":          lead["id"],          # Internal: which row to update
        "google_place_id":   lead.get("google_place_id", ""),
        "google_maps_url":   lead.get("google_maps_url", ""),
        "business_name":     lead.get("business_name", ""),
        "category":          lead.get("category", ""),
        "opportunity_tier":  lead.get("opportunity_tier", ""),
        "product_lines":     lead.get("product_lines", ""),
        "source_query":      lead.get("source_query", ""),
        "place_type":        lead.get("place_type", ""),
        "google_categories": lead.get("google_categories", ""),
        "city":              lead.get("city", ""),
        "country":           lead.get("country", FIXED_COUNTRY),
        "address":           lead.get("address", ""),
        "phone":             lead.get("phone", ""),
        "website":           lead.get("website"),      # May be None
        "has_website":       lead.get("has_website", 0),
        "rating":            lead.get("rating"),
        "review_count":      lead.get("review_count"),
    }


# ── MAIN REPROCESS FUNCTION ───────────────────────────────────

def reprocess():
    start = datetime.now()

    print("\n" + "=" * 55)
    print("  REPROCESS — Stages 2–5 only (Apify skipped)")
    print(f"  Database : {slug}.db")
    print(f"  Output   : {slug}.xlsx")
    print("=" * 55 + "\n")

    initialize_database()

    # Load all existing leads and convert to business dicts
    existing_leads = get_all_leads()
    total = len(existing_leads)

    if not total:
        print("[ERROR] Database is empty. Run the full pipeline first.")
        sys.exit(1)

    print(f"[DB] Loaded {total} existing leads\n")

    businesses = [lead_to_business(l) for l in existing_leads]

    # ── Stage 2: Validate all websites in parallel ────────────
    print(f"[STAGE 2] Validating {total} websites in parallel...")
    businesses = run_validation(businesses)
    print("[STAGE 2] Done\n")

    # ── Stage 3: PSI audits concurrently ─────────────────────
    print(f"[STAGE 3] Running concurrent PSI audits...")
    businesses = run_audit_all(businesses)
    print("[STAGE 3] Done\n")

    # ── Stage 4: AI analysis + scoring + update ───────────────
    print("[STAGE 4] AI analysis, scoring, updating records...\n")

    updated   = 0
    unchanged = 0
    errors    = 0

    # Build a lookup of original lead records by id for comparison
    leads_by_id = {l["id"]: l for l in existing_leads}

    for idx, business in enumerate(businesses):
        lead_id = business["_lead_id"]
        name    = business.get("business_name", "?")
        print(f"[{idx + 1}/{total}] {name}")

        try:
            validation = business.get("validation", {})
            status     = classify_website_status(business)
            audit      = business.get("audit", {})

            # Extract phone numbers from re-validated HTML
            phones = extract_saudi_phones(
                validation.get("html_content", ""),
                business.get("phone", ""),
            )

            # Decide whether to run AI
            should_run_ai = (
                status in ("no_website", "blocked_domain", "unreachable")
                or audit.get("is_weak")
                or (status in ("valid", "no_https") and audit.get("should_audit"))
            )

            ai_result = {}
            if should_run_ai:
                ai_result = analyze_business(business, audit)
                print(f"  [AI] Done ({status})")
            else:
                print(f"  [AI] Skipped — site appears healthy")

            lead_score    = calculate_lead_score(business, audit, ai_result)
            quality_label = get_quality_label(lead_score)
            html_data     = audit.get("html_data", {})
            contact_fields = build_contact_fields(business, html_data, phones)

            bad_reason = (
                ai_result.get("bad_reason")
                or build_bad_reason(business, audit, ai_result)
            )
            industry_sales_pitch = (
                ai_result.get("industry_sales_pitch")
                or build_industry_sales_pitch(business, audit, ai_result)
            )

            # Build full updated field set
            new_fields = {
                "phone":                 ", ".join(phones) if phones else business.get("phone", ""),
                "contact_phone":         contact_fields["contact_phone"],
                "landline_number":       contact_fields["landline_number"],
                "whatsapp_number":       contact_fields["whatsapp_number"],
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
                "emails":                ", ".join(html_data.get("emails", [])),
                "https_enabled":         1 if validation.get("https") else 0,
                "ssl_valid":             1 if validation.get("ssl_valid") else 0,
                "seo_score":             audit.get("seo_score"),
                "performance_score":     audit.get("performance_score"),
                "accessibility_score":   audit.get("accessibility_score"),
                "best_practices_score":  audit.get("best_practices_score"),
                "mobile_friendly":       audit.get("mobile_friendly"),
                "issues_found":          json.dumps(audit.get("issues_found", [])),
                "website_quality":       quality_label,
                "bad_reason":            bad_reason,
                "ai_uiux_score":         ai_result.get("ai_uiux_score"),
                "ai_analysis":           ai_result.get("ai_analysis"),
                "industry_sales_pitch":  industry_sales_pitch,
                "ai_sales_pitch":        ai_result.get("ai_sales_pitch", ""),
                "ai_whatsapp_msg":       ai_result.get("ai_whatsapp_msg", ""),
                "lead_score":            lead_score,
                "lead_type":             get_lead_type(status, validation, audit),
                "last_checked_at":       datetime.now().isoformat(timespec="seconds"),
            }

            # Compare against original record to detect changes
            original   = leads_by_id[lead_id]
            changes, summary = detect_changes(original, new_fields)

            if changes:
                new_fields["has_changes"] = 1
                update_lead(lead_id, new_fields, summary)
                log_lead_changes(lead_id, run_id=0, changes=changes)
                updated += 1
                print(f"  [UPDATED] {len(changes)} change(s) | Score: {lead_score} | {quality_label}")
            else:
                unchanged += 1
                print(f"  [UNCHANGED] No changes detected")

        except Exception as e:
            errors += 1
            print(f"  [ERROR] {e}")
            traceback.print_exc()

    # ── Stage 5: Export ───────────────────────────────────────
    print(f"\n[STAGE 5] Exporting to Excel...")
    xlsx_out = export_to_xlsx(xlsx_path)

    elapsed = round((datetime.now() - start).total_seconds(), 1)
    print_summary_report()

    print("=" * 55)
    print("  REPROCESS COMPLETE")
    print(f"  Runtime     : {elapsed}s")
    print(f"  Total leads : {total}")
    print(f"  Updated     : {updated}  (something changed)")
    print(f"  Unchanged   : {unchanged}  (no changes detected)")
    print(f"  Errors      : {errors}")
    print(f"  Database    : {config.DB_PATH}")
    print(f"  Excel       : {xlsx_out or 'None'}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    reprocess()
