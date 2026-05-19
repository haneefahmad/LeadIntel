# ============================================================
# exporter.py — Stage 5: Export leads to XLSX
# Reads all leads from SQLite, formats every column,
# and writes a client-ready Excel file with styled headers.
#
# CHANGES IN THIS VERSION:
#   - export_to_xlsx() replaces export_to_csv() — Excel output only
#   - export_top_leads() removed — only one output file per run
#   - Dynamic output_path passed in from main.py (named after
#     the selected categories and cities)
# ============================================================

import json                                          # For parsing stored JSON strings back to text
import openpyxl                                      # Excel file creation — pip install openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from database import get_all_leads, get_lead_count  # Our DB read functions

# ── CSV COLUMN HEADERS ────────────────────────────────────────
# These become Row 1 in the XLSX file — the column labels the client sees

HEADERS = [
    "Run ID",
    "Google Place ID",
    "Google Maps URL",
    "Business Name",
    "Category",
    "Google Categories",
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
    "Website Quality",
    "Lead Type",
    "Issues Found",
    "Bad Reason",
    "Root Causes & Fixes",
    "Improvement Roadmap",
    "Recommended Services",
    "Industry Sales Pitch",
    "WhatsApp Message",
    "Lead Score",
    "Has Changes",
    "Changes Detected",
    "Status",
    "Last Checked At",
    "Scraped At",
]

# ── FORMATTERS ────────────────────────────────────────────────

def fmt_yes_no(value) -> str:
    """Converts 1/0/True/False/None to readable YES, NO, or N/A."""
    if value is None:          return "N/A"
    if value in (1, True):     return "YES"
    if value in (0, False):    return "NO"
    return str(value)

def fmt_score(value) -> str:
    """Formats a numeric score as a string with 1 decimal. Returns empty string if None."""
    if value is None:  return ""
    return str(round(float(value), 1))

def fmt_issues(json_str: str) -> str:
    """
    Converts the stored JSON issues list into a readable semicolon-separated string.
    Example output: "Poor SEO score (43/100); No HTTPS; Missing meta description"
    """
    if not json_str:  return ""
    try:
        issues = json.loads(json_str)
        if not issues:  return ""
        return "; ".join(issues)
    except Exception:
        return json_str

def fmt_detailed_issues(issues_list: list) -> str:
    """
    Converts the detailed_issues list into a readable multi-line string.
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
            parts.append(str(item))
    return "\n\n".join(parts)

def fmt_roadmap(roadmap_list: list) -> str:
    """Converts improvement_roadmap list into a numbered readable string."""
    if not roadmap_list:
        return ""
    return "\n".join(roadmap_list)

def parse_ai_analysis(json_str: str) -> tuple:
    """
    Parses the AI analysis JSON and extracts all display fields.
    Returns a tuple of 6 values:
      (summary, root_causes_and_fixes, roadmap, services, priority, reason)
    """
    if not json_str or json_str == "{}":
        return ("", "", "", "", "", "")

    try:
        data = json.loads(json_str)
        summary  = data.get("summary", "")
        detailed = fmt_detailed_issues(data.get("detailed_issues", []))
        roadmap  = fmt_roadmap(data.get("improvement_roadmap", []))
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
    Converts one database lead record into a flat list for one XLSX row.
    Order MUST match HEADERS exactly.
    """
    _ai_summary, ai_detailed, ai_roadmap, ai_services, _ai_priority, _ai_reason = \
        parse_ai_analysis(lead.get("ai_analysis", ""))

    return [
        lead.get("run_id", ""),
        lead.get("google_place_id", ""),
        lead.get("google_maps_url", ""),
        lead.get("business_name", ""),
        lead.get("category", ""),
        lead.get("google_categories", ""),
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
        lead.get("website_quality", ""),
        lead.get("lead_type", ""),
        fmt_issues(lead.get("issues_found", "")),
        lead.get("bad_reason", ""),
        ai_detailed,
        ai_roadmap,
        ai_services,
        lead.get("industry_sales_pitch", ""),
        lead.get("ai_whatsapp_msg", ""),
        fmt_score(lead.get("lead_score")),
        lead.get("has_changes", 0),
        lead.get("changes_detected", ""),
        lead.get("status", "new"),
        lead.get("last_checked_at", ""),
        lead.get("scraped_at", ""),
    ]

# ── EXPORT FUNCTION ───────────────────────────────────────────

# Header row style — dark navy background, white bold text
_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
_HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Columns that contain long text — given more width and wrap_text
_WIDE_COLS = {
    "Bad Reason", "Root Causes & Fixes", "Improvement Roadmap",
    "Industry Sales Pitch", "WhatsApp Message", "Issues Found",
    "Recommended Services", "Changes Detected", "Google Categories",
    "Source Query", "Address",
}

def export_to_xlsx(output_path: str) -> str:
    """
    Exports ALL leads from the database to a formatted Excel (.xlsx) file.
    - Frozen header row (row 1 stays visible while scrolling)
    - Bold white headers on navy background
    - Column widths fitted to content (capped at 50 chars for wide columns,
      30 chars for narrow ones)
    - Text wrapping enabled for long-text columns
    - Returns the output path, or None if no leads exist.
    """
    print(f"[EXPORT] Fetching leads from database...")
    leads = get_all_leads()

    if not leads:
        print("[EXPORT] No leads found — nothing to export")
        return None

    print(f"[EXPORT] Writing {len(leads)} leads to {output_path}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads"

    # ── Write and style the header row ────────────────────────
    ws.append(HEADERS)
    for col_idx, cell in enumerate(ws[1], start=1):
        cell.font  = _HEADER_FONT
        cell.fill  = _HEADER_FILL
        cell.alignment = _HEADER_ALIGN

    # Freeze header row so it stays visible while scrolling
    ws.freeze_panes = "A2"

    # ── Write data rows ───────────────────────────────────────
    for lead in leads:
        ws.append(lead_to_row(lead))

    # ── Size columns to fit content ───────────────────────────
    for col_idx, header in enumerate(HEADERS, start=1):
        col_letter  = get_column_letter(col_idx)
        is_wide_col = header in _WIDE_COLS

        # Measure max content width in this column (header + data)
        max_len = len(header)
        for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
            val = str(row[0].value or "")
            # For multiline values, use the longest single line
            line_max = max((len(line) for line in val.split("\n")), default=0)
            max_len = max(max_len, line_max)

        if is_wide_col:
            # Long-text columns: cap at 60, enable text wrap on data cells
            ws.column_dimensions[col_letter].width = min(max_len + 2, 60)
            for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
                row[0].alignment = Alignment(wrap_text=True, vertical="top")
        else:
            # Standard columns: cap at 30 chars for readability
            ws.column_dimensions[col_letter].width = min(max_len + 2, 30)

    # Set a comfortable row height for header (auto-height would clip wrapping)
    ws.row_dimensions[1].height = 30

    wb.save(output_path)
    print(f"[EXPORT] Done: {output_path}")
    return output_path

# ── TERMINAL REPORT ───────────────────────────────────────────

def print_summary_report():
    """
    Prints a formatted summary of all leads to the terminal.
    Shows counts by type and a ranked top-10 list.
    No file is created — this is for terminal review only.
    """
    leads = get_all_leads()
    total = len(leads)

    if not total:
        print("[REPORT] Database is empty — no leads yet")
        return

    no_website  = sum(1 for l in leads if not l.get("website"))
    high_prio   = sum(1 for l in leads if (l.get("lead_score") or 0) >= 70)
    med_prio    = sum(1 for l in leads if 40 <= (l.get("lead_score") or 0) < 70)

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

    for lead in leads[:10]:
        score = lead.get("lead_score") or 0
        name  = (lead.get("business_name") or "?")[:27]
        city  = (lead.get("city") or "").split(",")[0][:11]
        print(f"  {score:5.1f}  {name:<28}  {city:<12}")

    print("  " + "-" * 52 + "\n")
