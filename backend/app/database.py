"""
Universal Database layer supporting ANY database (SQLite, PostgreSQL, MySQL, MariaDB, MSSQL, Oracle).

Powered by SQLAlchemy Core:
- Defaults to embedded high-performance SQLite (WAL mode, multi-sheet files).
- Supports external databases (PostgreSQL, Supabase, Neon, AWS RDS, MySQL, etc.)
  via connection strings (e.g. postgresql+psycopg://..., mysql+pymysql://...).
- Automatic table creation and column migrations.
- Strict non-destructive merge semantics: existing data is never wiped out.
"""

import json
import logging
import re
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy import (
    Column,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    case,
    func,
    or_,
    select,
    text,
)

try:
    from backend.app import config
    from backend.app.config import get_city_code
except ImportError:
    import config
    from config import get_city_code

logger = logging.getLogger("leadintel.database")

_local = threading.local()
_engine_cache: dict[str, sa.Engine] = {}
_cache_lock = threading.Lock()


# ── Canonical 39 Business Data Fields ─────────────────────────────────────────

MASTER_COLUMNS = [
    # 1. Identity & System
    "Record_ID",
    "Date_Added",
    "Added_By",
    "Lead_Status",

    # 2. Company Firmographics
    "Company_Name",
    "Company_Type",
    "Primary_Industry",
    "Secondary_Industry",
    "Employee_Count",

    # 3. Location & Maps
    "Country",
    "State",
    "City",
    "Full_Address",
    "Postal_Code",
    "Google_Maps_URL",

    # 4. Reputation
    "Google_Rating",
    "Reviews_Count",

    # 5. General Contact & Digital Presence
    "Primary_Phone",
    "General_Email",
    "WhatsApp_Number",
    "Website_URL",
    "Has_Website",
    "Company_LinkedIn",

    # 6. Primary Decision Maker
    "DM_Full_Name",
    "DM_Title",
    "DM_Authority_Level",
    "DM_Direct_Email",
    "DM_Email_Status",
    "DM_Email_Score",
    "DM_Direct_Phone",
    "DM_LinkedIn_URL",

    # 7. Pipeline & CRM
    "Pipeline_Stage",
    "Outreach_Status",
    "Assigned_To",
    "Deal_Value",
    "CRM_Notes",
    "Tags",
    "Last_Updated",
    "Updated_By",
]

COLUMN_DISPLAY_MAP = {
    "Record_ID": "Record id",
    "Date_Added": "Date added",
    "Added_By": "Added by",
    "Lead_Status": "Lead status",
    "Company_Name": "Company Name",
    "Company_Type": "Company type",
    "Primary_Industry": "Primary Industry",
    "Secondary_Industry": "Secondary Industry",
    "Employee_Count": "Employee count",
    "Country": "Country",
    "State": "State",
    "City": "City",
    "Full_Address": "Full Address",
    "Postal_Code": "Postal code",
    "Google_Maps_URL": "Google maps url",
    "Google_Rating": "Google Rating",
    "Reviews_Count": "Reviews count",
    "Primary_Phone": "Primary phone",
    "General_Email": "General Email",
    "WhatsApp_Number": "Whatsapp number",
    "Website_URL": "Website URL",
    "Has_Website": "Has Website",
    "Company_LinkedIn": "Company Linkedin",
    "DM_Full_Name": "DM Full name",
    "DM_Title": "DM Title",
    "DM_Authority_Level": "DM Authority Level",
    "DM_Direct_Email": "DM Direct Email",
    "DM_Email_Status": "DM Email Status",
    "DM_Email_Score": "DM Email Score",
    "DM_Direct_Phone": "DM Direct phone",
    "DM_LinkedIn_URL": "DM Linkedin URL",
    "Pipeline_Stage": "Pipeline Stage",
    "Outreach_Status": "Outreach Status",
    "Assigned_To": "Assigned to",
    "Deal_Value": "Deal Value",
    "CRM_Notes": "CRM Notes",
    "Tags": "Tags",
    "Last_Updated": "Last Updated",
    "Updated_By": "Updated by",
}

COLUMN_ALIASES = {
    # System / Meta
    "Status": "Lead_Status",
    "lead_status": "Lead_Status",
    "Lead status": "Lead_Status",
    "Record id": "Record_ID",
    "Date added": "Date_Added",
    "Added by": "Added_By",
    # Firmographics
    "Company": "Company_Name",
    "company": "Company_Name",
    "Business Name": "Company_Name",
    "business_name": "Company_Name",
    "Organization": "Company_Name",
    "organization": "Company_Name",
    "Organization Name": "Company_Name",
    "organization_name": "Company_Name",
    "Company_Name_EN": "Company_Name",
    "Company_Name_AR": "Company_Name",
    "company_name": "Company_Name",
    "Company Name": "Company_Name",
    "Company_Type": "Company_Type",
    "Company type": "Company_Type",
    "Type": "Company_Type",
    "Industry": "Primary_Industry",
    "industry": "Primary_Industry",
    "Sector": "Primary_Industry",
    "sector": "Primary_Industry",
    "Category": "Primary_Industry",
    "category": "Primary_Industry",
    "Industry_Primary": "Primary_Industry",
    "primary_industry": "Primary_Industry",
    "Primary Industry": "Primary_Industry",
    "Sub_Industry": "Secondary_Industry",
    "secondary_industry": "Secondary_Industry",
    "Secondary Industry": "Secondary_Industry",
    "Sub Industry": "Secondary_Industry",
    "Employee_Count_Est": "Employee_Count",
    "employee_count": "Employee_Count",
    "Employee count": "Employee_Count",
    "Employees": "Employee_Count",
    "employees": "Employee_Count",
    "Staff": "Employee_Count",
    "Team Size": "Employee_Count",
    # Location
    "City": "City",
    "city": "City",
    "Town": "City",
    "Location": "City",
    "location": "City",
    "State": "State",
    "state": "State",
    "Province": "State",
    "Region": "State",
    "Country": "Country",
    "country": "Country",
    "Postal code": "Postal_Code",
    "postal_code": "Postal_Code",
    "Postal Code": "Postal_Code",
    "Zip": "Postal_Code",
    "zip": "Postal_Code",
    "Zip Code": "Postal_Code",
    "Address": "Full_Address",
    "address": "Full_Address",
    "Street": "Full_Address",
    "Google maps url": "Google_Maps_URL",
    "maps_url": "Google_Maps_URL",
    "Full Address": "Full_Address",
    # Reputation
    "Google_Reviews_Count": "Reviews_Count",
    "reviews_count": "Reviews_Count",
    "Reviews count": "Reviews_Count",
    "Reviews": "Reviews_Count",
    "Google Rating": "Google_Rating",
    "Rating": "Google_Rating",
    "rating": "Google_Rating",
    # General Contact
    "Phone": "Primary_Phone",
    "phone": "Primary_Phone",
    "Phone Number": "Primary_Phone",
    "phone_number": "Primary_Phone",
    "Telephone": "Primary_Phone",
    "telephone": "Primary_Phone",
    "Mobile": "Primary_Phone",
    "mobile": "Primary_Phone",
    "Contact Number": "Primary_Phone",
    "Phone_Primary": "Primary_Phone",
    "primary_phone": "Primary_Phone",
    "Primary phone": "Primary_Phone",
    "Email": "General_Email",
    "email": "General_Email",
    "Email Address": "General_Email",
    "email_address": "General_Email",
    "Mail": "General_Email",
    "Email_General": "General_Email",
    "general_email": "General_Email",
    "General Email": "General_Email",
    "WhatsApp_Number": "WhatsApp_Number",
    "Whatsapp number": "WhatsApp_Number",
    "WhatsApp": "WhatsApp_Number",
    "whatsapp": "WhatsApp_Number",
    "Website": "Website_URL",
    "website": "Website_URL",
    "Web": "Website_URL",
    "Domain": "Website_URL",
    "domain": "Website_URL",
    "URL": "Website_URL",
    "url": "Website_URL",
    "Website_URL": "Website_URL",
    "Website URL": "Website_URL",
    "Has_Website": "Has_Website",
    "Has Website": "Has_Website",
    "Company_LinkedIn_URL": "Company_LinkedIn",
    "company_linkedin": "Company_LinkedIn",
    "Company Linkedin": "Company_LinkedIn",
    "LinkedIn": "Company_LinkedIn",
    # Decision Maker
    "Contact": "DM_Full_Name",
    "contact": "DM_Full_Name",
    "Contact Name": "DM_Full_Name",
    "contact_name": "DM_Full_Name",
    "Decision Maker": "DM_Full_Name",
    "decision_maker": "DM_Full_Name",
    "Person Name": "DM_Full_Name",
    "Executive": "DM_Full_Name",
    "Executive Name": "DM_Full_Name",
    "Full Name": "DM_Full_Name",
    "DM Name": "DM_Full_Name",
    "DM1_Full_Name": "DM_Full_Name",
    "dm_full_name": "DM_Full_Name",
    "DM Full name": "DM_Full_Name",
    "Title": "DM_Title",
    "title": "DM_Title",
    "Job Title": "DM_Title",
    "job_title": "DM_Title",
    "Position": "DM_Title",
    "position": "DM_Title",
    "Role": "DM_Title",
    "role": "DM_Title",
    "DM1_Title": "DM_Title",
    "dm_title": "DM_Title",
    "DM Title": "DM_Title",
    "DM1_Authority_Level": "DM_Authority_Level",
    "dm_authority_level": "DM_Authority_Level",
    "DM Authority Level": "DM_Authority_Level",
    "Direct Email": "DM_Direct_Email",
    "direct_email": "DM_Direct_Email",
    "Personal Email": "DM_Direct_Email",
    "DM1_Email": "DM_Direct_Email",
    "dm_direct_email": "DM_Direct_Email",
    "DM Direct Email": "DM_Direct_Email",
    "DM1_Email_Status": "DM_Email_Status",
    "dm_email_status": "DM_Email_Status",
    "DM Email Status": "DM_Email_Status",
    "DM1_Email_Score": "DM_Email_Score",
    "dm_email_score": "DM_Email_Score",
    "DM Email Score": "DM_Email_Score",
    "Direct Phone": "DM_Direct_Phone",
    "direct_phone": "DM_Direct_Phone",
    "Mobile Phone": "DM_Direct_Phone",
    "Cell Phone": "DM_Direct_Phone",
    "DM1_Phone": "DM_Direct_Phone",
    "dm_direct_phone": "DM_Direct_Phone",
    "DM Direct phone": "DM_Direct_Phone",
    "DM LinkedIn": "DM_LinkedIn_URL",
    "dm_linkedin": "DM_LinkedIn_URL",
    "DM1_LinkedIn_URL": "DM_LinkedIn_URL",
    "dm_linkedin_url": "DM_LinkedIn_URL",
    "DM Linkedin URL": "DM_LinkedIn_URL",
    "DM1_Authority_Level": "DM_Authority_Level",
    "dm_authority_level": "DM_Authority_Level",
    "DM Authority Level": "DM_Authority_Level",
    "DM1_Email": "DM_Direct_Email",
    "dm_direct_email": "DM_Direct_Email",
    "DM Direct Email": "DM_Direct_Email",
    "DM1_Email_Status": "DM_Email_Status",
    "dm_email_status": "DM_Email_Status",
    "DM Email Status": "DM_Email_Status",
    "DM1_Email_Score": "DM_Email_Score",
    "dm_email_score": "DM_Email_Score",
    "DM Email Score": "DM_Email_Score",
    "DM1_Phone": "DM_Direct_Phone",
    "dm_direct_phone": "DM_Direct_Phone",
    "DM Direct phone": "DM_Direct_Phone",
    "DM1_LinkedIn_URL": "DM_LinkedIn_URL",
    "dm_linkedin_url": "DM_LinkedIn_URL",
    "DM Linkedin URL": "DM_LinkedIn_URL",
    # Pipeline & CRM
    "Pipeline Stage": "Pipeline_Stage",
    "Outreach Status": "Outreach_Status",
    "Assigned to": "Assigned_To",
    "Deal_Value_SAR": "Deal_Value",
    "deal_value": "Deal_Value",
    "Deal Value": "Deal_Value",
    "Notes": "CRM_Notes",
    "crm_notes": "CRM_Notes",
    "CRM Notes": "CRM_Notes",
    "Last Updated": "Last_Updated",
    "Updated by": "Updated_By",
}

NUMERIC_COLUMNS = {
    "Google_Rating": "REAL",
    "Reviews_Count": "INTEGER",
    "DM_Email_Score": "INTEGER",
    "Deal_Value": "REAL",
}

DEFAULTS = {
    "Lead_Status": "New",
    "Outreach_Status": "Not_Started",
    "Pipeline_Stage": "Identified",
}

ALLOWED_CRM_COLUMNS = {
    "Lead_Status",
    "Status",
    "Pipeline_Stage",
    "Outreach_Status",
    "Assigned_To",
    "Deal_Value",
    "Deal_Value_SAR",
    "CRM_Notes",
    "Notes",
    "Tags",
}


# ── SQLAlchemy Universal Schema Metadata ─────────────────────────────────────

metadata = MetaData()

master_records_table = Table(
    "master_records",
    metadata,
    Column("Record_ID", String(64), primary_key=True),
    Column("Date_Added", String(32)),
    Column("Added_By", String(64)),
    Column("Lead_Status", String(32), server_default="New"),
    Column("Company_Name", String(255)),
    Column("Company_Type", String(128)),
    Column("Primary_Industry", String(128)),
    Column("Secondary_Industry", String(128)),
    Column("Employee_Count", String(64)),
    Column("Country", String(128)),
    Column("State", String(128)),
    Column("City", String(128)),
    Column("Full_Address", Text),
    Column("Postal_Code", String(32)),
    Column("Google_Maps_URL", Text),
    Column("Google_Rating", Float),
    Column("Reviews_Count", Integer, server_default="0"),
    Column("Primary_Phone", String(64)),
    Column("General_Email", String(255)),
    Column("WhatsApp_Number", String(64)),
    Column("Website_URL", Text),
    Column("Has_Website", String(16), server_default="No"),
    Column("Company_LinkedIn", Text),
    Column("DM_Full_Name", String(255)),
    Column("DM_Title", String(255)),
    Column("DM_Authority_Level", String(64)),
    Column("DM_Direct_Email", String(255)),
    Column("DM_Email_Status", String(64)),
    Column("DM_Email_Score", Integer, server_default="0"),
    Column("DM_Direct_Phone", String(64)),
    Column("DM_LinkedIn_URL", Text),
    Column("Pipeline_Stage", String(64), server_default="Identified"),
    Column("Outreach_Status", String(64), server_default="Not_Started"),
    Column("Assigned_To", String(128)),
    Column("Deal_Value", Float),
    Column("CRM_Notes", Text),
    Column("Tags", Text),
    Column("Last_Updated", String(32)),
    Column("Updated_By", String(64)),
    Column("google_place_id", String(255), unique=True),
    Column("sheet_name", String(128), server_default="MasterDB"),
    Index("idx_master_place_id", "google_place_id", unique=True),
    Index("idx_master_sheet", "sheet_name"),
    Index("idx_master_city", "City"),
    Index("idx_master_state", "State"),
    Index("idx_master_industry", "Primary_Industry"),
    Index("idx_master_status", "Lead_Status"),
    Index("idx_master_has_website", "Has_Website"),
)

apify_run_log_table = Table(
    "apify_run_log",
    metadata,
    Column("Run_ID", String(64), primary_key=True),
    Column("Date", String(32)),
    Column("Time_Started", String(32)),
    Column("Time_Completed", String(32)),
    Column("Query", Text),
    Column("Language", String(16)),
    Column("City_Target", String(128)),
    Column("Industry", String(128)),
    Column("Max_Records_Set", Integer),
    Column("Records_Returned", Integer),
    Column("Cost_USD", Float),
    Column("Cost_per_100", Float),
    Column("Quality_Score", Float),
    Column("Duplicates_Found", Integer),
    Column("Added_to_Master", Integer),
    Column("Notes", Text),
    Column("Run_By", String(64)),
    Column("Run_Type", String(32), server_default="Normal"),
    Column("sheet_name", String(128), server_default="MasterDB"),
    Index("idx_run_log_sheet", "sheet_name"),
)

suppression_list_table = Table(
    "suppression_list",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("Date_Added", String(32)),
    Column("Time_Added", String(32)),
    Column("Company_Name", String(255)),
    Column("Contact_Name", String(255)),
    Column("Email", String(255)),
    Column("Phone", String(64)),
    Column("LinkedIn_URL", Text),
    Column("Reason", Text),
    Column("Channels_Suppressed", Text),
    Column("Original_Record_ID", String(64)),
    Column("Suppressed_By", String(64)),
    Column("Notes", Text),
    Column("sheet_name", String(128), server_default="MasterDB"),
    Index("idx_suppression_sheet", "sheet_name"),
)


# ── Engine Lifecycle & Connection Pool ────────────────────────────────────────

def get_engine(custom_url: str | None = None, sheet_name: str | None = None) -> sa.Engine:
    """
    Returns a cached SQLAlchemy Engine instance.
    - If custom_url is specified, connects directly to that database URL.
    - If DATABASE_URL is configured (e.g. Postgres, MySQL), connects to that remote server.
    - Otherwise defaults to the local SQLite database for the active sheet.
    """
    url = custom_url or config.get_database_url(sheet_name)

    with _cache_lock:
        if url in _engine_cache:
            return _engine_cache[url]

        is_sqlite_url = url.startswith("sqlite")

        if is_sqlite_url:
            eng = sa.create_engine(
                url,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
            )
            # Enable WAL mode and foreign keys automatically for SQLite
            @sa.event.listens_for(eng, "connect")
            def _sqlite_on_connect(dbapi_conn, _):
                cursor = dbapi_conn.cursor()
                try:
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA foreign_keys=ON")
                except Exception:
                    pass
                finally:
                    cursor.close()
        else:
            # Client/Server Database (PostgreSQL, MySQL, CockroachDB, etc.)
            eng = sa.create_engine(
                url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,
            )

        _engine_cache[url] = eng
        return eng


def close_connection() -> None:
    """Disposes cached database engines and resets connection state."""
    with _cache_lock:
        for eng in _engine_cache.values():
            try:
                eng.dispose()
            except Exception:
                pass
        _engine_cache.clear()


def test_connection(database_url: str) -> tuple[bool, str, dict[str, Any]]:
    """
    Tests live connectivity to any database URL.
    Returns (success: bool, message: str, details: dict).
    """
    t0 = time.time()
    try:
        temp_engine = sa.create_engine(database_url, pool_pre_ping=True)
        with temp_engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
            dialect = temp_engine.dialect.name
            server_version = "Unknown"
            try:
                # Try fetching version
                res = conn.execute(sa.text("SELECT version()")).scalar()
                if res:
                    server_version = str(res)
            except Exception:
                pass
            latency_ms = round((time.time() - t0) * 1000, 1)

        temp_engine.dispose()
        return (
            True,
            f"Successfully connected to {dialect.upper()} in {latency_ms}ms.",
            {
                "dialect": dialect,
                "latency_ms": latency_ms,
                "server_version": server_version,
            },
        )
    except Exception as exc:
        err_msg = str(exc)
        return False, f"Database connection failed: {err_msg}", {"error": err_msg}


# ── Database Initialization & Column Migrations ───────────────────────────────

def init_db(sheet_name: str | None = None, custom_url: str | None = None) -> None:
    """
    Initializes database tables, creates indexes, and runs non-destructive schema migrations.
    """
    config.MASTERDATABASE_DIR.mkdir(parents=True, exist_ok=True)
    if sheet_name:
        config.set_active_sheet(sheet_name)

    eng = get_engine(custom_url, sheet_name)

    # 1. Create tables if not present
    metadata.create_all(eng)

    # 2. Schema check / column additions for backward compatibility
    try:
        insp = sa.inspect(eng)
        existing_cols = {c["name"] for c in insp.get_columns("master_records")}

        # Ensure sheet_name column exists
        if "sheet_name" not in existing_cols:
            with eng.begin() as conn:
                conn.execute(sa.text("ALTER TABLE master_records ADD COLUMN sheet_name VARCHAR(128) DEFAULT 'MasterDB'"))

        # Ensure google_place_id column exists
        if "google_place_id" not in existing_cols:
            with eng.begin() as conn:
                conn.execute(sa.text("ALTER TABLE master_records ADD COLUMN google_place_id VARCHAR(255)"))

        # Check apify_run_log sheet_name
        log_cols = {c["name"] for c in insp.get_columns("apify_run_log")}
        if "sheet_name" not in log_cols:
            with eng.begin() as conn:
                conn.execute(sa.text("ALTER TABLE apify_run_log ADD COLUMN sheet_name VARCHAR(128) DEFAULT 'MasterDB'"))

        # Check suppression_list sheet_name
        supp_cols = {c["name"] for c in insp.get_columns("suppression_list")}
        if "sheet_name" not in supp_cols:
            with eng.begin() as conn:
                conn.execute(sa.text("ALTER TABLE suppression_list ADD COLUMN sheet_name VARCHAR(128) DEFAULT 'MasterDB'"))

    except Exception as exc:
        logger.warning("Automated column check completed with notice: %s", exc)


def _active_sheet(sheet_name: str | None = None) -> str:
    return sheet_name or config.get_active_sheet() or config.DEFAULT_SHEET_NAME


# ── Row Normalization for Frontend Backwards Compatibility ───────────────────

def _normalize_row_for_output(row: dict[str, Any] | sa.engine.row.RowMapping | Any) -> dict[str, Any]:
    d = dict(row) if hasattr(row, "keys") else {col: getattr(row, col, None) for col in MASTER_COLUMNS}
    # Backward compatible aliases
    d["Company_Name_EN"] = d.get("Company_Name") or ""
    d["Status"] = d.get("Lead_Status") or "New"
    d["Industry_Primary"] = d.get("Primary_Industry") or ""
    d["Sub_Industry"] = d.get("Secondary_Industry") or ""
    d["Employee_Count_Est"] = d.get("Employee_Count") or ""
    d["Google_Reviews_Count"] = d.get("Reviews_Count") or 0
    d["Phone_Primary"] = d.get("Primary_Phone") or ""
    d["Email_General"] = d.get("General_Email") or ""
    d["Company_LinkedIn_URL"] = d.get("Company_LinkedIn") or ""
    d["DM1_Full_Name"] = d.get("DM_Full_Name") or ""
    d["DM1_Title"] = d.get("DM_Title") or ""
    d["DM1_Authority_Level"] = d.get("DM_Authority_Level") or ""
    d["DM1_Email"] = d.get("DM_Direct_Email") or ""
    d["DM1_Email_Status"] = d.get("DM_Email_Status") or ""
    d["DM1_Email_Score"] = d.get("DM_Email_Score") or 0
    d["DM1_Phone"] = d.get("DM_Direct_Phone") or ""
    d["DM1_LinkedIn_URL"] = d.get("DM_LinkedIn_URL") or ""
    d["Deal_Value_SAR"] = d.get("Deal_Value")
    d["Notes"] = d.get("CRM_Notes") or ""
    return d


# ── Record Deduplication, Upserting & Merging ─────────────────────────────────

def record_exists(place_id: str, sheet_name: str | None = None) -> bool:
    if not place_id:
        return False
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)
    with eng.connect() as conn:
        if config.is_sqlite():
            row = conn.execute(
                sa.text("SELECT 1 FROM master_records WHERE google_place_id = :pid"),
                {"pid": place_id},
            ).fetchone()
        else:
            row = conn.execute(
                sa.text("SELECT 1 FROM master_records WHERE google_place_id = :pid AND sheet_name = :sh"),
                {"pid": place_id, "sh": sh},
            ).fetchone()
    return row is not None


def get_existing_enrichment(place_ids: list[str], max_age_days: int = 30, sheet_name: str | None = None) -> dict[str, dict]:
    """
    Returns stored enrichment data for place IDs that were updated within max_age_days.
    Returns {google_place_id: record_dict}.
    """
    if not place_ids:
        return {}

    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)

    with eng.connect() as conn:
        query = select(master_records_table).where(master_records_table.c.google_place_id.in_(place_ids))
        if not config.is_sqlite():
            query = query.where(master_records_table.c.sheet_name == sh)
        rows = conn.execute(query).mappings().fetchall()

    now = datetime.now()
    results = {}
    for r in rows:
        d = dict(r)
        pid = d.get("google_place_id")
        if not pid:
            continue
        last_up = d.get("Last_Updated")
        is_fresh = False
        if last_up:
            try:
                up_dt = datetime.fromisoformat(last_up)
                if (now - up_dt).days <= max_age_days:
                    is_fresh = True
            except (ValueError, TypeError):
                pass
        if not is_fresh:
            date_added = d.get("Date_Added")
            if date_added:
                try:
                    add_dt = datetime.fromisoformat(date_added)
                    if (now - add_dt).days <= max_age_days:
                        is_fresh = True
                except (ValueError, TypeError):
                    pass
        if is_fresh:
            results[pid] = d

    return results


def _infer_state(city: str | None, address: str | None) -> str:
    combined = f"{city or ''} {address or ''}".lower()
    if any(k in combined for k in ["austin", "dallas", "houston", "san antonio", "fort worth", "plano", "texas", ", tx", " tx ", " tx,"]):
        return "Texas"
    if any(k in combined for k in ["los angeles", "san francisco", "san diego", "california", ", ca", " ca "]):
        return "California"
    if any(k in combined for k in ["miami", "orlando", "tampa", "florida", ", fl", " fl "]):
        return "Florida"
    if any(k in combined for k in ["new york", "nyc", "manhattan", "brooklyn", ", ny", " ny "]):
        return "New York"
    if any(k in combined for k in ["chicago", "illinois", ", il", " il "]):
        return "Illinois"
    m = re.search(r'\b([A-Z]{2})\s+\d{5}\b', f"{city or ''} {address or ''}")
    if m:
        state_code = m.group(1).upper()
        state_map = {"TX": "Texas", "CA": "California", "FL": "Florida", "NY": "New York", "IL": "Illinois", "WA": "Washington", "CO": "Colorado", "GA": "Georgia"}
        return state_map.get(state_code, state_code)
    return ""


def _yes_no(value: Any) -> str:
    return "Yes" if value in (True, "True", "true", 1, "1", "Yes", "yes") else "No"


def _prepare_record(record: dict[str, Any]) -> dict[str, Any]:
    # Normalize aliases
    normalized: dict[str, Any] = {}
    for k, v in record.items():
        canonical = COLUMN_ALIASES.get(k, k)
        if canonical not in normalized or (normalized[canonical] in (None, "") and v not in (None, "")):
            normalized[canonical] = v

    prepared = {col: normalized.get(col) for col in MASTER_COLUMNS}
    for col, default in DEFAULTS.items():
        if prepared.get(col) in (None, ""):
            prepared[col] = default

    if prepared.get("Has_Website") not in (None, ""):
        prepared["Has_Website"] = _yes_no(prepared["Has_Website"])

    # State inference if missing
    if not prepared.get("State"):
        prepared["State"] = _infer_state(prepared.get("City"), prepared.get("Full_Address"))

    phone = prepared.get("Primary_Phone") or ""
    digits = re.sub(r"\D", "", str(phone))
    if not prepared.get("WhatsApp_Number") and len(digits) >= 9:
        prepared["WhatsApp_Number"] = phone

    return prepared


def _merge_existing_values(stored: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Keep existing enrichment when a later provider/rerun returns blanks."""
    merged = dict(incoming)
    for col in MASTER_COLUMNS:
        if merged.get(col) in (None, "") and stored.get(col) not in (None, ""):
            merged[col] = stored[col]
    return merged


def _next_record_id(city: str, year: int, conn: sa.Connection, city_counters: dict[str, int] | None = None, sheet_name: str | None = None) -> str:
    code = get_city_code(city)
    prefix = f"{code}-{year}-"
    if city_counters is not None and prefix in city_counters:
        city_counters[prefix] += 1
        seq = city_counters[prefix]
    else:
        q = sa.text("SELECT Record_ID FROM master_records WHERE Record_ID LIKE :pref ORDER BY Record_ID DESC LIMIT 1")
        row = conn.execute(q, {"pref": prefix + "%"}).mappings().fetchone()
        seq = int(row["Record_ID"].split("-")[-1]) + 1 if row else 1
        if city_counters is not None:
            city_counters[prefix] = seq
    return f"{prefix}{seq:05d}"


def upsert_records_batch(
    records: list[dict[str, Any]],
    commit: bool = True,
    sheet_name: str | None = None,
) -> tuple[int, int]:
    """
    Universal batch upsert across any database.
    Performs non-destructive updates for existing records, preserving all valid data.
    Returns (inserted_count, updated_count).
    """
    if not records:
        return 0, 0

    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)

    now = datetime.now()
    now_iso = now.isoformat(timespec="seconds")
    today_iso = now.date().isoformat()

    inserted_count = 0
    updated_count = 0
    city_counters: dict[str, int] = {}

    update_cols = [col for col in MASTER_COLUMNS if col not in {"Record_ID", "Date_Added", "Added_By"}]

    with eng.begin() as conn:
        for record in records:
            prepared = _prepare_record(record)
            place_id = (record.get("google_place_id") or "").strip()
            prepared["Last_Updated"] = now_iso
            prepared["Updated_By"] = prepared.get("Updated_By") or prepared.get("Added_By") or "System"

            existing = None
            if place_id:
                if config.is_sqlite():
                    existing = conn.execute(
                        sa.text("SELECT * FROM master_records WHERE google_place_id = :pid"),
                        {"pid": place_id},
                    ).mappings().fetchone()
                else:
                    existing = conn.execute(
                        sa.text("SELECT * FROM master_records WHERE google_place_id = :pid AND sheet_name = :sh"),
                        {"pid": place_id, "sh": sh},
                    ).mappings().fetchone()
            elif record.get("DM_LinkedIn_URL") or record.get("DM1_LinkedIn_URL"):
                li = (record.get("DM_LinkedIn_URL") or record.get("DM1_LinkedIn_URL") or "").strip()
                existing = conn.execute(
                    sa.text("SELECT * FROM master_records WHERE DM_LinkedIn_URL = :li"),
                    {"li": li},
                ).mappings().fetchone()
            elif (record.get("Company_Name") or record.get("Company_Name_EN")) and (record.get("DM_Full_Name") or record.get("DM1_Full_Name")):
                c_name = (record.get("Company_Name") or record.get("Company_Name_EN") or "").strip()
                d_name = (record.get("DM_Full_Name") or record.get("DM1_Full_Name") or "").strip()
                existing = conn.execute(
                    sa.text("SELECT * FROM master_records WHERE LOWER(Company_Name) = LOWER(:c) AND LOWER(DM_Full_Name) = LOWER(:d)"),
                    {"c": c_name, "d": d_name},
                ).mappings().fetchone()
            elif record.get("Record_ID"):
                r_id = str(record.get("Record_ID")).strip()
                if r_id:
                    existing = conn.execute(
                        sa.text("SELECT * FROM master_records WHERE Record_ID = :rid"),
                        {"rid": r_id},
                    ).mappings().fetchone()
            elif record.get("Company_Name") or record.get("Company_Name_EN"):
                c_name = (record.get("Company_Name") or record.get("Company_Name_EN") or "").strip()
                if c_name:
                    existing = conn.execute(
                        sa.text("SELECT * FROM master_records WHERE LOWER(Company_Name) = LOWER(:c)"),
                        {"c": c_name},
                    ).mappings().fetchone()
            elif record.get("Website_URL"):
                web = str(record.get("Website_URL")).strip().rstrip("/")
                if web and len(web) > 5:
                    existing = conn.execute(
                        sa.text("SELECT * FROM master_records WHERE Website_URL = :w OR Website_URL = :w_slash"),
                        {"w": web, "w_slash": web + "/"},
                    ).mappings().fetchone()

            if existing:
                rec_id = existing["Record_ID"]
                stored = dict(existing)
                prepared = _merge_existing_values(stored, prepared)

                if stored.get("Company_Type") in (None, ""):
                    prepared["Company_Type"] = record.get("Company_Type")
                if stored.get("Country") in (None, ""):
                    prepared["Country"] = record.get("Country")
                if stored.get("State") in (None, ""):
                    prepared["State"] = record.get("State")

                update_params = {col: prepared.get(col) for col in update_cols}
                update_params["rec_id"] = rec_id
                assignments = ", ".join(f'"{col}" = :{col}' for col in update_cols)

                conn.execute(
                    sa.text(f"UPDATE master_records SET {assignments} WHERE Record_ID = :rec_id"),
                    update_params,
                )
                updated_count += 1
            else:
                city = prepared.get("City", "")
                rec_id = _next_record_id(city, now.year, conn, city_counters, sheet_name=sh)
                prepared["Record_ID"] = rec_id
                prepared["Date_Added"] = today_iso
                prepared["Added_By"] = prepared.get("Added_By") or "System"

                insert_dict = {col: prepared.get(col) for col in MASTER_COLUMNS}
                insert_dict["google_place_id"] = place_id or None
                insert_dict["sheet_name"] = sh

                col_names = ", ".join(f'"{col}"' for col in insert_dict.keys())
                placeholders = ", ".join(f":{col}" for col in insert_dict.keys())
                conn.execute(
                    sa.text(f"INSERT INTO master_records ({col_names}) VALUES ({placeholders})"),
                    insert_dict,
                )
                inserted_count += 1

    return inserted_count, updated_count


def upsert_record(record: dict[str, Any], sheet_name: str | None = None) -> tuple[bool, str]:
    """Insert or update a single business record by google_place_id."""
    inserted_count, _ = upsert_records_batch([record], commit=True, sheet_name=sheet_name)
    place_id = (record.get("google_place_id") or "").strip()
    if place_id:
        eng = get_engine(sheet_name=sheet_name)
        with eng.connect() as conn:
            row = conn.execute(
                sa.text("SELECT Record_ID FROM master_records WHERE google_place_id = :pid"),
                {"pid": place_id},
            ).mappings().fetchone()
            if row:
                return (inserted_count > 0), row["Record_ID"]
    return (inserted_count > 0), record.get("Record_ID", "")


def insert_record(record: dict[str, Any]) -> tuple[bool, str]:
    """Backward-compatible alias. Existing rows are updated non-destructively."""
    return upsert_record(record)


# ── Querying, Filtering & Full-Text Search ────────────────────────────────────

def query_records(
    q: str = "",
    city: str = "",
    industry: str = "",
    status: str = "",
    has_website: str = "",
    has_email: str = "",
    has_dm: str = "",
    has_phone: str = "",
    page: int = 1,
    limit: int | None = 25,
    sheet_name: str | None = None,
) -> tuple[list[dict], int]:
    """
    Universal SQL-level filtering, search, and pagination across any database.
    Returns (records_list, total_matching_count).
    """
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)

    conditions = []
    params: dict[str, Any] = {}

    if not config.is_sqlite():
        conditions.append("sheet_name = :sh")
        params["sh"] = sh

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        conditions.append(
            "("
            "LOWER(Company_Name) LIKE :q OR "
            "LOWER(Full_Address) LIKE :q OR "
            "LOWER(General_Email) LIKE :q OR "
            "LOWER(DM_Direct_Email) LIKE :q OR "
            "LOWER(Primary_Phone) LIKE :q OR "
            "LOWER(Record_ID) LIKE :q"
            ")"
        )
        params["q"] = term

    if city and city.strip():
        conditions.append("LOWER(City) = LOWER(:city)")
        params["city"] = city.strip()

    if industry and industry.strip():
        conditions.append("LOWER(Primary_Industry) LIKE LOWER(:industry)")
        params["industry"] = f"%{industry.strip()}%"

    if status and status.strip():
        conditions.append("LOWER(Lead_Status) = LOWER(:status)")
        params["status"] = status.strip()

    if has_website and has_website.strip():
        if has_website.strip().lower() in ("yes", "true", "1"):
            conditions.append("Website_URL IS NOT NULL AND TRIM(Website_URL) != ''")
        else:
            conditions.append("(Website_URL IS NULL OR TRIM(Website_URL) = '')")

    if has_email and has_email.strip():
        if has_email.strip().lower() in ("yes", "true", "1"):
            conditions.append(
                "((General_Email IS NOT NULL AND TRIM(General_Email) != '') OR "
                "(DM_Direct_Email IS NOT NULL AND TRIM(DM_Direct_Email) != ''))"
            )
        else:
            conditions.append(
                "((General_Email IS NULL OR TRIM(General_Email) = '') AND "
                "(DM_Direct_Email IS NULL OR TRIM(DM_Direct_Email) = ''))"
            )

    if has_dm and has_dm.strip():
        if has_dm.strip().lower() in ("yes", "true", "1"):
            conditions.append("DM_Full_Name IS NOT NULL AND TRIM(DM_Full_Name) != ''")
        else:
            conditions.append("(DM_Full_Name IS NULL OR TRIM(DM_Full_Name) = '')")

    if has_phone and has_phone.strip():
        if has_phone.strip().lower() in ("yes", "true", "1"):
            conditions.append(
                "((Primary_Phone IS NOT NULL AND TRIM(Primary_Phone) != '') OR "
                "(DM_Direct_Phone IS NOT NULL AND TRIM(DM_Direct_Phone) != ''))"
            )
        else:
            conditions.append(
                "((Primary_Phone IS NULL OR TRIM(Primary_Phone) = '') AND "
                "(DM_Direct_Phone IS NULL OR TRIM(DM_Direct_Phone) = ''))"
            )

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with eng.connect() as conn:
        count_sql = sa.text(f"SELECT COUNT(*) FROM master_records {where_clause}")
        total_count = conn.execute(count_sql, params).scalar() or 0

        if limit is not None and limit > 0:
            offset = max(0, (page - 1) * limit)
            page_sql = sa.text(f"SELECT * FROM master_records {where_clause} ORDER BY Record_ID LIMIT :limit OFFSET :offset")
            query_params = {**params, "limit": limit, "offset": offset}
        else:
            page_sql = sa.text(f"SELECT * FROM master_records {where_clause} ORDER BY Record_ID")
            query_params = params

        rows = conn.execute(page_sql, query_params).mappings().fetchall()

    return [_normalize_row_for_output(r) for r in rows], total_count


def get_all_records(sheet_name: str | None = None) -> list[dict]:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)
    with eng.connect() as conn:
        if config.is_sqlite():
            rows = conn.execute(sa.text("SELECT * FROM master_records ORDER BY Record_ID")).mappings().fetchall()
        else:
            rows = conn.execute(
                sa.text("SELECT * FROM master_records WHERE sheet_name = :sh ORDER BY Record_ID"),
                {"sh": sh},
            ).mappings().fetchall()
    return [_normalize_row_for_output(r) for r in rows]


def get_record_by_id(record_id: str, sheet_name: str | None = None) -> dict | None:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    with eng.connect() as conn:
        row = conn.execute(
            sa.text("SELECT * FROM master_records WHERE Record_ID = :rid"),
            {"rid": record_id},
        ).mappings().fetchone()
    return _normalize_row_for_output(row) if row else None


def get_total_count(sheet_name: str | None = None) -> int:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)
    with eng.connect() as conn:
        if config.is_sqlite():
            return conn.execute(sa.text("SELECT COUNT(*) FROM master_records")).scalar() or 0
        return conn.execute(
            sa.text("SELECT COUNT(*) FROM master_records WHERE sheet_name = :sh"),
            {"sh": sh},
        ).scalar() or 0


# ── KPI Analytics & Aggregations ──────────────────────────────────────────────

def get_stats(sheet_name: str | None = None) -> dict:
    """
    Calculates comprehensive KPI statistics using optimized SQL aggregations.
    Works identically across SQLite, PostgreSQL, MySQL, etc.
    """
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)

    where_clause = ""
    params: dict[str, Any] = {}
    if not config.is_sqlite():
        where_clause = "WHERE sheet_name = :sh"
        params["sh"] = sh

    with eng.connect() as conn:
        summary_sql = sa.text(f"""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN Website_URL IS NOT NULL AND TRIM(Website_URL) != '' THEN 1 ELSE 0 END) AS with_website,
                SUM(CASE WHEN Primary_Phone IS NOT NULL AND TRIM(Primary_Phone) != '' THEN 1 ELSE 0 END) AS with_phone,
                SUM(CASE WHEN (General_Email IS NOT NULL AND TRIM(General_Email) != '') OR (DM_Direct_Email IS NOT NULL AND TRIM(DM_Direct_Email) != '') THEN 1 ELSE 0 END) AS with_email,
                SUM(CASE WHEN WhatsApp_Number IS NOT NULL AND TRIM(WhatsApp_Number) != '' THEN 1 ELSE 0 END) AS with_whatsapp,
                SUM(CASE WHEN DM_Full_Name IS NOT NULL AND TRIM(DM_Full_Name) != '' THEN 1 ELSE 0 END) AS with_dm
            FROM master_records
            {where_clause}
        """)
        summary_row = conn.execute(summary_sql, params).mappings().fetchone()

        city_sql = sa.text(f"""
            SELECT COALESCE(NULLIF(TRIM(City), ''), 'Unspecified') AS city_name, COUNT(*) AS cnt 
            FROM master_records 
            {where_clause}
            GROUP BY city_name 
            ORDER BY cnt DESC
        """)
        city_rows = conn.execute(city_sql, params).mappings().fetchall()

        ind_sql = sa.text(f"""
            SELECT COALESCE(NULLIF(TRIM(Primary_Industry), ''), 'General') AS ind_name, COUNT(*) AS cnt 
            FROM master_records 
            {where_clause}
            GROUP BY ind_name 
            ORDER BY cnt DESC
        """)
        ind_rows = conn.execute(ind_sql, params).mappings().fetchall()

        status_sql = sa.text(f"""
            SELECT COALESCE(NULLIF(TRIM(Lead_Status), ''), 'New') AS st_name, COUNT(*) AS cnt 
            FROM master_records 
            {where_clause}
            GROUP BY st_name 
            ORDER BY cnt DESC
        """)
        status_rows = conn.execute(status_sql, params).mappings().fetchall()

        log_sql = sa.text(f"""
            SELECT COUNT(*) AS total_runs, COALESCE(SUM(Cost_USD), 0.0) AS total_cost
            FROM apify_run_log
            {where_clause}
        """)
        log_row = conn.execute(log_sql, params).mappings().fetchone()

    total = (summary_row["total"] if summary_row else 0) or 0
    with_website = (summary_row["with_website"] if summary_row else 0) or 0
    with_phone = (summary_row["with_phone"] if summary_row else 0) or 0
    with_email = (summary_row["with_email"] if summary_row else 0) or 0
    with_whatsapp = (summary_row["with_whatsapp"] if summary_row else 0) or 0
    with_dm = (summary_row["with_dm"] if summary_row else 0) or 0

    total_cost = round(((log_row["total_cost"] if log_row else 0.0) or 0.0), 2)
    total_runs = (log_row["total_runs"] if log_row else 0) or 0

    return {
        "total": total,
        "with_website": with_website,
        "website_pct": round((with_website / total * 100), 1) if total else 0,
        "with_phone": with_phone,
        "phone_pct": round((with_phone / total * 100), 1) if total else 0,
        "with_email": with_email,
        "email_pct": round((with_email / total * 100), 1) if total else 0,
        "with_whatsapp": with_whatsapp,
        "with_dm": with_dm,
        "dm_pct": round((with_dm / total * 100), 1) if total else 0,
        "total_cost_usd": total_cost,
        "by_city": {r["city_name"]: r["cnt"] for r in city_rows},
        "by_industry": {r["ind_name"]: r["cnt"] for r in ind_rows},
        "by_status": {r["st_name"]: r["cnt"] for r in status_rows},
        "total_runs": total_runs,
    }


# ── Mutable CRM & Non-Destructive In-Place Updates ───────────────────────────

def update_record_crm(
    record_id: str,
    updates: dict[str, Any],
    updated_by: str = "CRM User",
    sheet_name: str | None = None,
) -> dict | None:
    """Updates mutable CRM fields for a lead in master_records."""
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)

    with eng.connect() as conn:
        existing = conn.execute(
            sa.text("SELECT * FROM master_records WHERE Record_ID = :rid"),
            {"rid": record_id},
        ).mappings().fetchone()

    if not existing:
        return None

    mapped_updates: dict[str, Any] = {}
    for k, v in updates.items():
        canonical = COLUMN_ALIASES.get(k, k)
        if canonical in ALLOWED_CRM_COLUMNS:
            mapped_updates[canonical] = v

    if not mapped_updates:
        return _normalize_row_for_output(existing)

    mapped_updates["Last_Updated"] = datetime.now().isoformat(timespec="seconds")
    mapped_updates["Updated_By"] = updated_by

    assignments = ", ".join(f'"{col}" = :{col}' for col in mapped_updates)
    params = {**mapped_updates, "rid": record_id}

    with eng.begin() as conn:
        conn.execute(sa.text(f"UPDATE master_records SET {assignments} WHERE Record_ID = :rid"), params)

    return get_record_by_id(record_id, sheet_name=sheet_name)


def enrich_record_in_place(
    record_id: str,
    new_fields: dict[str, Any],
    overwrite: bool = False,
    updated_by: str = "Enrichment Engine",
    sheet_name: str | None = None,
) -> tuple[bool, list[str]]:
    """
    Updates an existing record by Record_ID, populating ONLY fields that are currently empty or null.
    Existing valid data is strictly preserved unless overwrite is True.
    Returns (success, list_of_fields_updated).
    """
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)

    with eng.connect() as conn:
        existing = conn.execute(
            sa.text("SELECT * FROM master_records WHERE Record_ID = :rid"),
            {"rid": record_id},
        ).mappings().fetchone()

    if not existing:
        return False, []

    stored = dict(existing)
    updates_to_apply: dict[str, Any] = {}
    updated_fields: list[str] = []

    for k, v in new_fields.items():
        canonical_k = COLUMN_ALIASES.get(k, k)
        if canonical_k not in MASTER_COLUMNS or canonical_k in ("Record_ID", "Date_Added", "Added_By"):
            continue

        if v is None:
            continue
        v_str = str(v).strip()
        if not v_str or v_str.lower() in ("none", "null", "undefined", "n/a", "not discovered"):
            continue

        current_val = stored.get(canonical_k)
        is_empty = (
            current_val is None
            or str(current_val).strip() in ("", "None", "null", "undefined", "N/A", "Not Discovered")
            or (canonical_k == "Reviews_Count" and current_val == 0)
            or (canonical_k == "Has_Website" and current_val in ("No", "no", 0, "0"))
        )

        if is_empty or overwrite:
            updates_to_apply[canonical_k] = v
            updated_fields.append(canonical_k)

    # Auto-bridge valid phone number to WhatsApp_Number if WhatsApp is missing
    phone_to_check = updates_to_apply.get("Primary_Phone") or stored.get("Primary_Phone") or ""
    current_wa = updates_to_apply.get("WhatsApp_Number") or stored.get("WhatsApp_Number")
    if phone_to_check and (not current_wa or str(current_wa).strip() in ("", "None", "null", "undefined")):
        digits = re.sub(r"\D", "", str(phone_to_check))
        if len(digits) >= 9:
            updates_to_apply["WhatsApp_Number"] = phone_to_check
            if "WhatsApp_Number" not in updated_fields:
                updated_fields.append("WhatsApp_Number")

    if not updates_to_apply:
        return True, []

    updates_to_apply["Last_Updated"] = datetime.now().isoformat(timespec="seconds")
    updates_to_apply["Updated_By"] = updated_by

    assignments = ", ".join(f'"{col}" = :{col}' for col in updates_to_apply)
    params = {**updates_to_apply, "rid": record_id}

    with eng.begin() as conn:
        conn.execute(sa.text(f"UPDATE master_records SET {assignments} WHERE Record_ID = :rid"), params)

    return True, updated_fields


def suppress_record(
    record_id: str,
    reason: str = "Opt-out",
    suppressed_by: str = "CRM User",
    notes: str = "",
    sheet_name: str | None = None,
) -> bool:
    """
    Adds a lead to the suppression_list for compliance,
    and updates its master_records status to Disqualified / Do_Not_Contact.
    """
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)

    with eng.connect() as conn:
        row = conn.execute(
            sa.text("SELECT * FROM master_records WHERE Record_ID = :rid"),
            {"rid": record_id},
        ).mappings().fetchone()

    if not row:
        return False

    record = dict(row)
    now = datetime.now()
    date_str = now.date().isoformat()
    time_str = now.strftime("%H:%M:%S")

    with eng.begin() as conn:
        conn.execute(
            suppression_list_table.insert(),
            {
                "Date_Added": date_str,
                "Time_Added": time_str,
                "Company_Name": record.get("Company_Name") or record.get("Company_Name_EN") or "Unknown",
                "Contact_Name": record.get("DM_Full_Name") or record.get("DM1_Full_Name") or "",
                "Email": record.get("General_Email") or record.get("DM_Direct_Email") or "",
                "Phone": record.get("Primary_Phone") or "",
                "LinkedIn_URL": record.get("Company_LinkedIn") or record.get("DM_LinkedIn_URL") or "",
                "Reason": reason,
                "Channels_Suppressed": "All Channels",
                "Original_Record_ID": record_id,
                "Suppressed_By": suppressed_by,
                "Notes": notes or f"Suppressed via CRM Dashboard on {date_str}",
                "sheet_name": sh,
            },
        )
        conn.execute(
            sa.text("""
                UPDATE master_records
                SET Lead_Status = 'Disqualified',
                    Outreach_Status = 'Do_Not_Contact',
                    Last_Updated = :now_iso,
                    Updated_By = :supp_by
                WHERE Record_ID = :rid
            """),
            {"now_iso": now.isoformat(timespec="seconds"), "supp_by": suppressed_by, "rid": record_id},
        )

    return True


def delete_record(record_id: str, sheet_name: str | None = None) -> bool:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    with eng.begin() as conn:
        res = conn.execute(sa.text("DELETE FROM master_records WHERE Record_ID = :rid"), {"rid": record_id})
    return bool(res.rowcount and res.rowcount > 0)


def delete_all_records(sheet_name: str | None = None) -> int:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)
    with eng.begin() as conn:
        if config.is_sqlite():
            res = conn.execute(sa.text("DELETE FROM master_records"))
        else:
            res = conn.execute(sa.text("DELETE FROM master_records WHERE sheet_name = :sh"), {"sh": sh})
    return res.rowcount or 0


# ── Run Logs & Suppression Lists ──────────────────────────────────────────────

def log_run(run_data: dict[str, Any], sheet_name: str | None = None) -> None:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)

    records_returned = run_data.get("records_returned", 0) or 0
    cost = run_data.get("cost_usd", run_data.get("cost", 0.0)) or 0.0
    cost_per_100 = round(cost / records_returned * 100, 2) if records_returned else 0
    city = run_data.get("city") or run_data.get("city_target", "")
    max_rec = run_data.get("max_records") or run_data.get("max_records_set", 0) or 0
    dups = run_data.get("duplicates") or run_data.get("duplicates_found", 0) or 0
    added = run_data.get("added_to_master", records_returned) or 0

    with eng.begin() as conn:
        count = conn.execute(sa.text("SELECT COUNT(*) FROM apify_run_log")).scalar() or 0
        r_id = run_data.get("run_id") or f"AR-{count + 1:03d}"

        # Delete existing run if re-logging same ID
        conn.execute(sa.text("DELETE FROM apify_run_log WHERE Run_ID = :rid"), {"rid": r_id})
        conn.execute(
            apify_run_log_table.insert(),
            {
                "Run_ID": r_id,
                "Date": run_data.get("date", date.today().isoformat()),
                "Time_Started": run_data.get("time_started", ""),
                "Time_Completed": run_data.get("time_completed", ""),
                "Query": run_data.get("query", ""),
                "Language": run_data.get("language", "en"),
                "City_Target": city,
                "Industry": run_data.get("industry", ""),
                "Max_Records_Set": max_rec,
                "Records_Returned": records_returned,
                "Cost_USD": cost,
                "Cost_per_100": cost_per_100,
                "Quality_Score": run_data.get("quality_score", 9.0),
                "Duplicates_Found": dups,
                "Added_to_Master": added,
                "Notes": run_data.get("notes", ""),
                "Run_By": run_data.get("run_by", "System"),
                "Run_Type": run_data.get("run_type", "Normal"),
                "sheet_name": sh,
            },
        )


add_run_log = log_run


def get_run_log(sheet_name: str | None = None) -> list[dict]:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)
    with eng.connect() as conn:
        if config.is_sqlite():
            rows = conn.execute(sa.text("SELECT * FROM apify_run_log ORDER BY Run_ID")).mappings().fetchall()
        else:
            rows = conn.execute(
                sa.text("SELECT * FROM apify_run_log WHERE sheet_name = :sh ORDER BY Run_ID"),
                {"sh": sh},
            ).mappings().fetchall()
    return [dict(r) for r in rows]


def get_suppression_list(sheet_name: str | None = None) -> list[dict]:
    init_db(sheet_name)
    eng = get_engine(sheet_name=sheet_name)
    sh = _active_sheet(sheet_name)
    with eng.connect() as conn:
        if config.is_sqlite():
            rows = conn.execute(sa.text("SELECT * FROM suppression_list")).mappings().fetchall()
        else:
            rows = conn.execute(
                sa.text("SELECT * FROM suppression_list WHERE sheet_name = :sh"),
                {"sh": sh},
            ).mappings().fetchall()
    return [dict(r) for r in rows]