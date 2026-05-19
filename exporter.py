# ============================================================
# exporter.py — Stage 5: Export leads to CSV
# Reads all leads from SQLite, formats every column,
# and writes a client-ready CSV file
# ============================================================

import csv                                           # Python built-in CSV writer
import json                                          # For parsing stored JSON strings back to text
from datetime import datetime                        # For adding timestamp to output filename
from database import get_all_leads, get_lead_count  # Our DB read functions
from config import CSV_PATH                          # Default output path from config

# ── CSV COLUMN HEADERS ────────────────────────────────────────
# These become Row 1 in the CSV file — the column labels the client sees

CSV_HEADERS = [
    "Run ID",
    "Google Place ID",
    "Google Maps URL",
    "Business Name",
    "Category",
    "Opportunity Tier",
    "Product Lines",
    "Source Query",
    "Place Type",
    "City",
    "Country",
    "Address",
    "Raw Phone",
    "Contact Phone",
    "Landline Number",
    "WhatsApp Number",
    "Primary Email",
    "Email Status",
    "Email Confidence",
    "Email Verification Provider",
    "Email Checked At",
    "Hunter Status",
    "Hunter Score",
    "Email Source URL",
    "Emails Found",
    "LinkedIn Company URL",
    "Decision Maker LinkedIn",
    "Website",
    "Rating",
    "Review Count",
    "Has Website",
    "HTTPS",
    "SSL Valid",
    "SEO Score",
    "Performance Score",
    "Accessibility Score",
    "Best Practices",
    "Mobile Friendly",
    "AI UI/UX Score",
    "Lead Type",
    "Issues Found",
    "Bad Reason",
    "Root Causes & Fixes",  # NEW — each issue with why + exactly how to fix it
    "Improvement Roadmap",  # NEW — prioritised step-by-step improvement plan
    "Recommended Services",
    "Industry Sales Pitch",
    "WhatsApp Message",
    "Lead Score",
    "Status",
    "Last Checked At",
    "Scraped At",
]

# ── FORMATTERS ────────────────────────────────────────────────

def fmt_yes_no(value) -> str:
    """Converts 1/0/True/False/None to readable YES, NO, or N/A for CSV cells."""
    if value is None:          return "N/A"   # No data was collected for this field
    if value in (1, True):     return "YES"
    if value in (0, False):    return "NO"
    return str(value)                         # Fallback — convert anything else to string

def fmt_score(value) -> str:
    """Formats a numeric score as a string with 1 decimal. Returns empty string if None."""
    if value is None:  return ""              # No score — leave cell blank in CSV
    return str(round(float(value), 1))        # Round to 1 decimal then convert to string

def fmt_social_links(json_str: str) -> str:
    """
    Converts the stored JSON social links dict into a readable pipe-separated string.
    Example output: "Instagram: https://... | Facebook: https://..."
    """
    if not json_str:  return ""              # Empty input — return blank
    try:
        links = json.loads(json_str)         # Parse the JSON string back to a Python dict
        if not links:  return ""             # Empty dict — no social links found
        parts = []                           # List to build the formatted output
        for platform, url in links.items():
            parts.append(f"{platform.capitalize()}: {url}")   # "Instagram: https://..."
        return " | ".join(parts)             # Join all platforms with a | separator
    except Exception:
        return json_str                      # If JSON parse fails, return the raw string

def fmt_issues(json_str: str) -> str:
    """
    Converts the stored JSON issues list into a readable semicolon-separated string.
    Example output: "Poor SEO score (43/100); No HTTPS; Missing meta description"
    """
    if not json_str:  return ""              # Empty input — return blank
    try:
        issues = json.loads(json_str)        # Parse JSON string back to Python list
        if not issues:  return ""            # Empty list — no issues found
        return "; ".join(issues)             # Join issue strings with semicolons
    except Exception:
        return json_str                      # Return raw string on parse failure

def fmt_detailed_issues(issues_list: list) -> str:
    """
    Converts the detailed_issues list into a readable multi-line string for the CSV.
    Each issue becomes:
      ISSUE: [name]
      WHY: [root cause]
      IMPACT: [business impact]
      FIX: [exact fix steps]
    """
    if not issues_list:
        return ""
    parts = []
    for item in issues_list:
        if isinstance(item, dict):
            block = (
                f"ISSUE: {item.get('issue', '')}\n"
                f"WHY: {item.get('root_cause', '')}\n"
                f"IMPACT: {item.get('business_impact', '')}\n"
                f"FIX: {item.get('exact_fix', '')}"
            )
            parts.append(block)
        else:
            parts.append(str(item))   # Fallback for plain strings
    return "\n\n".join(parts)   # Double newline between each issue block

def fmt_roadmap(roadmap_list: list) -> str:
    """Converts improvement_roadmap list into a numbered readable string."""
    if not roadmap_list:
        return ""
    return "\n".join(roadmap_list)   # One step per line

def parse_ai_analysis(json_str: str) -> tuple:
    """
    Parses the AI analysis JSON and extracts all display fields.
    Returns a tuple of 6 values matching the new CSV columns:
      (summary, root_causes_and_fixes, roadmap, services, priority, reason)
    """
    if not json_str or json_str == "{}":
        return ("", "", "", "", "", "")   # Six empty strings — one per new column

    try:
        data = json.loads(json_str)

        summary  = data.get("summary", "")

        # Format detailed issues — each with root cause + exact fix
        detailed = fmt_detailed_issues(data.get("detailed_issues", []))

        # Format improvement roadmap — ordered steps
        roadmap  = fmt_roadmap(data.get("improvement_roadmap", []))

        # Recommended services as comma-separated string
        services     = data.get("recommended_services", [])
        services_txt = ", ".join(services) if services else ""

        priority = data.get("redesign_priority", "")
        reason   = data.get("redesign_reason", "")

        return (summary, detailed, roadmap, services_txt, priority, reason)

    except Exception:
        return (json_str, "", "", "", "", "")

# ── ROW BUILDER ───────────────────────────────────────────────

def lead_to_row(lead: dict) -> list:
    """
    Converts one database lead record into a flat list for one CSV row.
    Order MUST match CSV_HEADERS exactly.
    """
    _ai_summary, ai_detailed, ai_roadmap, ai_services, _ai_priority, _ai_reason = \
        parse_ai_analysis(lead.get("ai_analysis", ""))
    # Unpack all 6 AI analysis fields

    return [
        lead.get("run_id", ""),
        lead.get("google_place_id", ""),
        lead.get("google_maps_url", ""),
        lead.get("business_name", ""),
        lead.get("category", ""),
        lead.get("opportunity_tier", ""),
        lead.get("product_lines", ""),
        lead.get("source_query", ""),
        lead.get("place_type", ""),
        lead.get("city", ""),
        lead.get("country", ""),
        lead.get("address", ""),
        lead.get("phone", ""),
        lead.get("contact_phone", ""),
        lead.get("landline_number", ""),
        lead.get("whatsapp_number", ""),
        lead.get("primary_email", ""),
        lead.get("email_status", ""),
        lead.get("email_confidence", ""),
        lead.get("email_verification_provider", ""),
        lead.get("email_checked_at", ""),
        lead.get("hunter_status", ""),
        fmt_score(lead.get("hunter_score")),
        lead.get("email_source_url", ""),
        lead.get("emails", ""),
        lead.get("linkedin_company_url", ""),
        lead.get("decision_maker_linkedin", ""),
        lead.get("website", ""),
        fmt_score(lead.get("rating")),
        lead.get("review_count", ""),
        fmt_yes_no(lead.get("has_website")),
        fmt_yes_no(lead.get("https_enabled")),
        fmt_yes_no(lead.get("ssl_valid")),
        fmt_score(lead.get("seo_score")),
        fmt_score(lead.get("performance_score")),
        fmt_score(lead.get("accessibility_score")),
        fmt_score(lead.get("best_practices_score")),
        fmt_yes_no(lead.get("mobile_friendly")),
        fmt_score(lead.get("ai_uiux_score")),
        lead.get("lead_type", ""),
        fmt_issues(lead.get("issues_found", "")),
        lead.get("bad_reason", ""),
        ai_detailed,      # Root Causes & Fixes — new detailed breakdown
        ai_roadmap,       # Improvement Roadmap — prioritised steps
        ai_services,      # Recommended Services
        lead.get("industry_sales_pitch", ""),
        lead.get("ai_whatsapp_msg", ""),
        fmt_score(lead.get("lead_score")),
        lead.get("status", "new"),
        lead.get("last_checked_at", ""),
        lead.get("scraped_at", ""),
    ]

# ── EXPORT FUNCTIONS ──────────────────────────────────────────

def export_to_csv(output_path: str = None) -> str:
    """
    Exports ALL leads from the database to a CSV file.
    Returns the path of the created file.
    """
    if not output_path:
        ts          = datetime.now().strftime("%Y%m%d_%H%M%S")   # e.g. "20250514_143022"
        output_path = f"leads_export_{ts}.csv"                   # Unique timestamped filename

    print(f"[EXPORT] Fetching leads from database...")
    leads = get_all_leads()           # Get all leads sorted by lead_score descending

    if not leads:
        print("[EXPORT] No leads found — nothing to export")
        return None                   # Nothing to write

    print(f"[EXPORT] Writing {len(leads)} leads to {output_path}")

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        # "utf-8-sig" adds a BOM byte at the start — makes Arabic text render correctly in Excel
        writer = csv.writer(f)        # Create the CSV writer object
        writer.writerow(CSV_HEADERS)  # Write the header row first (Row 1)
        for lead in leads:
            writer.writerow(lead_to_row(lead))   # Write one data row per lead

    print(f"[EXPORT] Done: {output_path}")
    return output_path                # Return file path so main.py can display it

def export_top_leads(min_score: float = 70.0) -> str:
    """
    Exports only the highest-priority leads (score at or above min_score).
    Creates a second shorter CSV — useful as a quick-action list for the client.
    """
    all_leads = get_all_leads()       # Fetch all leads from database
    top       = [l for l in all_leads if (l.get("lead_score") or 0) >= min_score]
    # List comprehension: keep only leads with score >= the minimum threshold

    if not top:
        print(f"[EXPORT] No leads found with score >= {min_score}")
        return None

    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"top_leads_{int(min_score)}plus_{ts}.csv"   # e.g. "top_leads_70plus_20250514.csv"

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)          # Same headers as full export
        for lead in top:
            writer.writerow(lead_to_row(lead))   # Write only the high-score leads

    print(f"[EXPORT] {len(top)} top leads exported to: {output_path}")
    return output_path

# ── TERMINAL REPORT ───────────────────────────────────────────

def print_summary_report():
    """
    Prints a formatted summary of all leads to the terminal.
    Shows counts by type and a ranked top-10 list.
    No file is created — this is for terminal review only.
    """
    leads = get_all_leads()   # Fetch all leads from DB
    total = len(leads)        # Count them

    if not total:
        print("[REPORT] Database is empty — no leads yet")
        return

    # Count by category
    no_website  = sum(1 for l in leads if not l.get("website"))
    # How many businesses had absolutely no website

    high_prio   = sum(1 for l in leads if (l.get("lead_score") or 0) >= 70)
    # How many leads scored 70 or above

    med_prio    = sum(1 for l in leads if 40 <= (l.get("lead_score") or 0) < 70)
    # How many leads scored between 40 and 69

    print("\n" + "=" * 55)
    print(" SAUDI ARABIA LEAD INTELLIGENCE — SUMMARY REPORT")
    print("=" * 55)
    print(f"  Total leads in database : {total}")
    print(f"  No website (instant)    : {no_website}")
    print(f"  High priority (70+)     : {high_prio}")
    print(f"  Medium priority (40-69) : {med_prio}")
    print("=" * 55)

    print("\n  TOP 10 LEADS BY SCORE:")
    print("  " + "-" * 52)
    print(f"  {'SCORE':>5}  {'BUSINESS':<28}  {'CITY':<12}")
    print("  " + "-" * 52)

    for lead in leads[:10]:   # leads is already sorted descending by score from DB query
        score = lead.get("lead_score") or 0
        name  = (lead.get("business_name") or "?")[:27]   # Truncate long names for display
        city  = (lead.get("city") or "").split(",")[0][:11]  # Just city name, not country
        print(f"  {score:5.1f}  {name:<28}  {city:<12}")

    print("  " + "-" * 52 + "\n")
