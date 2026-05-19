# ============================================================
# database.py — SQLite database operations
#
# CHANGES IN THIS VERSION:
#   1. Added place_type column — stores Google Place Type used
#   2. Added google_categories column — stores all Google tags
#   3. Added website_quality column — human-readable quality label
#   4. ALL businesses are now saved (not just weak ones)
#      website_quality label distinguishes them in the CSV
#
# CHANGE DETECTION (new):
#   Re-running the pipeline on existing data now UPDATES records
#   in-place instead of skipping duplicates silently.
#
#   New table  : lead_updates  — field-level change log with
#                old/new values and timestamp per re-run.
#   New column : changes_detected on leads — plain-English
#                summary of what changed in the latest run
#                (e.g. "https_enabled: NO→YES; seo_score: 43→71").
#   New fn     : find_existing_lead()  — returns the full lead
#                dict if this business is already in the DB.
#   New fn     : update_lead()         — updates changed fields
#                in-place and writes changes_detected summary.
#   New fn     : log_lead_changes()    — appends each changed
#                field to lead_updates for full audit trail.
# ============================================================

import sqlite3
import json
import os
from datetime import datetime
import config   # NOT "from config import DB_PATH" — so main.py can override config.DB_PATH at runtime

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id               INTEGER,
    google_place_id      TEXT,
    google_maps_url      TEXT,
    business_name        TEXT,
    category             TEXT,
    opportunity_tier     TEXT,
    product_lines        TEXT,
    source_query         TEXT,
    place_type           TEXT,
    google_categories    TEXT,
    city                 TEXT,
    country              TEXT,
    address              TEXT,
    phone                TEXT,
    contact_phone        TEXT,
    landline_number      TEXT,
    whatsapp_number      TEXT,
    website              TEXT,
    primary_email        TEXT,
    email_status         TEXT,
    email_confidence     TEXT,
    email_source_url     TEXT,
    email_verification_provider TEXT,
    email_checked_at     TIMESTAMP,
    hunter_status        TEXT,
    hunter_score         REAL,
    hunter_result        TEXT,
    linkedin_company_url TEXT,
    decision_maker_linkedin TEXT,
    rating               REAL,
    review_count         INTEGER,
    emails               TEXT,
    social_links         TEXT,
    has_website          INTEGER,
    https_enabled        INTEGER,
    ssl_valid            INTEGER,
    seo_score            REAL,
    performance_score    REAL,
    accessibility_score  REAL,
    best_practices_score REAL,
    mobile_friendly      INTEGER,
    issues_found         TEXT,
    website_quality      TEXT,
    bad_reason           TEXT,
    ai_uiux_score        REAL,
    ai_analysis          TEXT,
    industry_sales_pitch TEXT,
    ai_sales_pitch       TEXT,
    ai_whatsapp_msg      TEXT,
    lead_score           REAL,
    lead_type            TEXT,
    status               TEXT DEFAULT 'new',
    last_checked_at      TIMESTAMP,
    scraped_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_RUNS_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    country               TEXT,
    cities                TEXT,
    categories            TEXT,
    started_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at           TIMESTAMP,
    raw_scraped_count     INTEGER DEFAULT 0,
    discarded_wrong_type_count INTEGER DEFAULT 0,
    duplicate_count       INTEGER DEFAULT 0,
    scraped_count         INTEGER DEFAULT 0,
    saved_leads_count     INTEGER DEFAULT 0,
    ignored_good_count    INTEGER DEFAULT 0,
    skipped_count         INTEGER DEFAULT 0,
    error_count           INTEGER DEFAULT 0,
    notes                 TEXT
)
"""

CREATE_BUSINESSES_SQL = """
CREATE TABLE IF NOT EXISTS businesses (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id               INTEGER,
    google_place_id      TEXT,
    google_maps_url      TEXT,
    business_name        TEXT,
    category             TEXT,
    opportunity_tier     TEXT,
    product_lines        TEXT,
    source_query         TEXT,
    place_type           TEXT,
    google_categories    TEXT,
    city                 TEXT,
    country              TEXT,
    address              TEXT,
    phone                TEXT,
    website              TEXT,
    rating               REAL,
    review_count         INTEGER,
    scrape_status        TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_LEAD_UPDATES_SQL = """
CREATE TABLE IF NOT EXISTS lead_updates (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id      INTEGER NOT NULL,          -- FK → leads.id
    run_id       INTEGER NOT NULL,          -- which pipeline run detected this
    field_name   TEXT NOT NULL,             -- which field changed
    old_value    TEXT,                      -- value before this run
    new_value    TEXT,                      -- value after this run
    detected_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_IGNORED_SQL = """
CREATE TABLE IF NOT EXISTS ignored_businesses (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id               INTEGER,
    google_place_id      TEXT,
    google_maps_url      TEXT,
    business_name        TEXT,
    category             TEXT,
    opportunity_tier     TEXT,
    product_lines        TEXT,
    source_query         TEXT,
    place_type           TEXT,
    city                 TEXT,
    country              TEXT,
    website              TEXT,
    reason               TEXT,
    seo_score            REAL,
    performance_score    REAL,
    accessibility_score  REAL,
    best_practices_score REAL,
    mobile_friendly      INTEGER,
    ai_uiux_score        REAL,
    ignored_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

REQUIRED_COLUMNS = {
    "run_id": "INTEGER",
    "google_place_id": "TEXT",
    "changes_detected": "TEXT",   # Plain-English summary of latest re-run changes
    "has_changes":      "INTEGER DEFAULT 0",  # 0 = no changes, 1 = updated this run
    "google_maps_url": "TEXT",
    "opportunity_tier": "TEXT",
    "product_lines": "TEXT",
    "source_query": "TEXT",
    "contact_phone": "TEXT",
    "landline_number": "TEXT",
    "whatsapp_number": "TEXT",
    "primary_email": "TEXT",
    "email_status": "TEXT",
    "email_confidence": "TEXT",
    "email_source_url": "TEXT",
    "email_verification_provider": "TEXT",
    "email_checked_at": "TIMESTAMP",
    "hunter_status": "TEXT",
    "hunter_score": "REAL",
    "hunter_result": "TEXT",
    "linkedin_company_url": "TEXT",
    "decision_maker_linkedin": "TEXT",
    "rating": "REAL",
    "review_count": "INTEGER",
    "bad_reason": "TEXT",
    "industry_sales_pitch": "TEXT",
    "lead_type": "TEXT",
    "last_checked_at": "TIMESTAMP",
}

RUN_REQUIRED_COLUMNS = {
    "raw_scraped_count": "INTEGER DEFAULT 0",
    "discarded_wrong_type_count": "INTEGER DEFAULT 0",
    "duplicate_count": "INTEGER DEFAULT 0",
}

BUSINESS_REQUIRED_COLUMNS = {
    "opportunity_tier": "TEXT",
    "product_lines": "TEXT",
    "source_query": "TEXT",
}

IGNORED_REQUIRED_COLUMNS = {
    "opportunity_tier": "TEXT",
    "product_lines": "TEXT",
    "source_query": "TEXT",
}

def get_connection():
    """Opens and returns a SQLite connection with dict-style row access."""
    conn = sqlite3.connect(config.DB_PATH)   # Uses config.DB_PATH — overridable at runtime
    conn.row_factory = sqlite3.Row           # Access columns by name
    return conn

def ensure_columns(cursor, table_name: str, required_columns: dict):
    """Adds missing columns to an existing SQLite table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row["name"] for row in cursor.fetchall()}
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

def initialize_database():
    """
    Creates leads.db and the leads table if they don't exist.
    Prints full absolute path so you can find the file.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    cursor.execute(CREATE_RUNS_SQL)
    cursor.execute(CREATE_BUSINESSES_SQL)
    cursor.execute(CREATE_IGNORED_SQL)
    cursor.execute(CREATE_LEAD_UPDATES_SQL)
    ensure_columns(cursor, "leads", REQUIRED_COLUMNS)
    ensure_columns(cursor, "runs", RUN_REQUIRED_COLUMNS)
    ensure_columns(cursor, "businesses", BUSINESS_REQUIRED_COLUMNS)
    ensure_columns(cursor, "ignored_businesses", IGNORED_REQUIRED_COLUMNS)
    conn.commit()
    conn.close()
    print(f"[DB] Database ready at: {os.path.abspath(config.DB_PATH)}")

def create_run(cities: list, category_pairs: list, country: str) -> int:
    """Creates a run record and returns its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO runs (country, cities, categories)
        VALUES (?, ?, ?)
        """,
        (
            country,
            json.dumps(cities, ensure_ascii=False),
            json.dumps([{"display_name": d, "place_type": p} for d, p in category_pairs], ensure_ascii=False),
        ),
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def finalize_run(
    run_id: int,
    scraped_count: int,
    saved_leads_count: int,
    ignored_good_count: int,
    skipped_count: int,
    error_count: int,
    raw_scraped_count: int = 0,
    discarded_wrong_type_count: int = 0,
    duplicate_count: int = 0,
    notes: str = "",
):
    """Updates run totals after the pipeline finishes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET finished_at = ?, raw_scraped_count = ?, discarded_wrong_type_count = ?,
            duplicate_count = ?, scraped_count = ?, saved_leads_count = ?,
            ignored_good_count = ?, skipped_count = ?, error_count = ?, notes = ?
        WHERE id = ?
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            raw_scraped_count,
            discarded_wrong_type_count,
            duplicate_count,
            scraped_count,
            saved_leads_count,
            ignored_good_count,
            skipped_count,
            error_count,
            notes,
            run_id,
        ),
    )
    conn.commit()
    conn.close()

def save_business_observation(business: dict, run_id: int, scrape_status: str = "verified") -> bool:
    """
    Stores a single business observation.
    Prefer save_business_observations_batch() for bulk inserts.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO businesses (
            run_id, google_place_id, google_maps_url, business_name, category,
            opportunity_tier, product_lines, source_query, place_type,
            google_categories, city, country, address, phone, website, rating,
            review_count, scrape_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            business.get("google_place_id", ""),
            business.get("google_maps_url", ""),
            business.get("business_name", ""),
            business.get("category", ""),
            business.get("opportunity_tier", ""),
            business.get("product_lines", ""),
            business.get("source_query", ""),
            business.get("place_type", ""),
            business.get("google_categories", ""),
            business.get("city", ""),
            business.get("country", ""),
            business.get("address", ""),
            business.get("phone", ""),
            business.get("website"),
            business.get("rating"),
            business.get("review_count"),
            scrape_status,
        ),
    )
    conn.commit()
    conn.close()
    return True


def save_business_observations_batch(
    businesses: list,
    run_id: int,
    scrape_status: str = "verified",
) -> int:
    """
    FIX ⑥: Inserts all scraped businesses in a SINGLE database transaction
    instead of opening and closing one connection per business.

    For a batch of 300 businesses the old code did 300 connect/commit/close
    cycles.  This does exactly one — roughly 100x fewer round-trips to the
    SQLite file.

    Returns the number of rows inserted.
    """
    if not businesses:
        return 0

    rows = [
        (
            run_id,
            b.get("google_place_id", ""),
            b.get("google_maps_url", ""),
            b.get("business_name", ""),
            b.get("category", ""),
            b.get("opportunity_tier", ""),
            b.get("product_lines", ""),
            b.get("source_query", ""),
            b.get("place_type", ""),
            b.get("google_categories", ""),
            b.get("city", ""),
            b.get("country", ""),
            b.get("address", ""),
            b.get("phone", ""),
            b.get("website"),
            b.get("rating"),
            b.get("review_count"),
            scrape_status,
        )
        for b in businesses
    ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO businesses (
            run_id, google_place_id, google_maps_url, business_name, category,
            opportunity_tier, product_lines, source_query, place_type,
            google_categories, city, country, address, phone, website, rating,
            review_count, scrape_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()
    print(f"[DB] Saved {len(rows)} business observations in one batch")
    return len(rows)

def save_ignored_business(business: dict, run_id: int, reason: str, audit: dict, ai_result: dict) -> bool:
    """Stores businesses that passed the quality gate so users can audit what was ignored."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO ignored_businesses (
            run_id, google_place_id, google_maps_url, business_name, category,
            opportunity_tier, product_lines, source_query, place_type,
            city, country, website, reason, seo_score,
            performance_score, accessibility_score, best_practices_score,
            mobile_friendly, ai_uiux_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            business.get("google_place_id", ""),
            business.get("google_maps_url", ""),
            business.get("business_name", ""),
            business.get("category", ""),
            business.get("opportunity_tier", ""),
            business.get("product_lines", ""),
            business.get("source_query", ""),
            business.get("place_type", ""),
            business.get("city", ""),
            business.get("country", ""),
            business.get("website"),
            reason,
            audit.get("seo_score"),
            audit.get("performance_score"),
            audit.get("accessibility_score"),
            audit.get("best_practices_score"),
            audit.get("mobile_friendly"),
            ai_result.get("ai_uiux_score"),
        ),
    )
    conn.commit()
    conn.close()
    return True

def save_lead(lead: dict) -> bool:
    """
    Inserts one lead into the database.
    ALL businesses are saved now — not just weak ones.
    Returns True if saved, False if duplicate or error.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Duplicate check — prefer stable Google identity, then fall back to name + city.
    google_place_id = lead.get("google_place_id")
    if google_place_id:
        cursor.execute(
            "SELECT id FROM leads WHERE google_place_id = ?",
            (google_place_id,)
        )
    else:
        cursor.execute(
            "SELECT id FROM leads WHERE business_name = ? AND city = ?",
            (lead.get("business_name"), lead.get("city"))
        )
    if cursor.fetchone():
        conn.close()
        return False   # Already exists — skip

    lead_copy = lead.copy()
    lead_copy["social_links"]  = json.dumps(lead.get("social_links", {}))
    lead_copy["issues_found"]  = json.dumps(lead.get("issues_found", []))

    columns      = ", ".join(lead_copy.keys())
    placeholders = ", ".join(["?" for _ in lead_copy])
    values       = tuple(lead_copy.values())

    try:
        cursor.execute(
            f"INSERT INTO leads ({columns}) VALUES ({placeholders})",
            values
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Insert failed: {e}")
        conn.close()
        return False

def get_all_leads() -> list:
    """Returns all leads sorted by lead_score descending."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY lead_score DESC")
    rows   = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_lead_count() -> int:
    """Returns total number of records in the database."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    count  = cursor.fetchone()[0]
    conn.close()
    return count

def get_leads_by_city(city: str) -> list:
    """Returns all leads for a specific city sorted by score."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM leads WHERE city LIKE ? ORDER BY lead_score DESC",
        (f"%{city}%",)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def is_already_scraped(business_name: str, city: str, google_place_id: str = "") -> bool:
    """Returns True if this business + city already exists in the DB."""
    conn   = get_connection()
    cursor = conn.cursor()
    if google_place_id:
        cursor.execute(
            "SELECT COUNT(*) FROM leads WHERE google_place_id = ?",
            (google_place_id,)
        )
    else:
        cursor.execute(
            "SELECT COUNT(*) FROM leads WHERE business_name = ? AND city = ?",
            (business_name, city)
        )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


# ── CHANGE DETECTION ──────────────────────────────────────────

def find_existing_lead(business_name: str, city: str, google_place_id: str = "") -> dict | None:
    """
    Returns the full existing lead record as a dict if this business
    is already in the database, or None if it is new.

    Prefers matching by google_place_id (stable Google identifier)
    and falls back to business_name + city if no place ID is available.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    if google_place_id:
        cursor.execute(
            "SELECT * FROM leads WHERE google_place_id = ?",
            (google_place_id,)
        )
    else:
        cursor.execute(
            "SELECT * FROM leads WHERE business_name = ? AND city = ?",
            (business_name, city)
        )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_lead(lead_id: int, updated_fields: dict, changes_summary: str) -> bool:
    """
    Updates an existing lead record in-place with new field values.

    Only the fields that actually changed are written — we never
    overwrite scraped_at (original first-seen date) or status
    (the user may have set this to "contacted", "closed", etc.).

    Also stamps changes_detected with a plain-English summary and
    refreshes last_checked_at to the current time.
    """
    if not updated_fields:
        return False

    # Protect fields the user owns — never overwrite these
    for protected in ("id", "scraped_at", "status"):
        updated_fields.pop(protected, None)

    updated_fields["changes_detected"] = changes_summary
    updated_fields["last_checked_at"]  = datetime.now().isoformat(timespec="seconds")

    set_clause = ", ".join(f"{k} = ?" for k in updated_fields)
    values     = list(updated_fields.values()) + [lead_id]

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def log_lead_changes(lead_id: int, run_id: int, changes: list) -> None:
    """
    Appends each changed field to the lead_updates audit table.

    Each row in lead_updates records:
      - which lead changed
      - which run detected the change
      - which field changed
      - the old value and new value
      - when it was detected

    This gives you a complete history of every change across all runs.
    """
    if not changes:
        return

    now  = datetime.now().isoformat(timespec="seconds")
    rows = [
        (lead_id, run_id, c["field"], str(c["old"]) if c["old"] is not None else "",
         str(c["new"]) if c["new"] is not None else "", now)
        for c in changes
    ]

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO lead_updates (lead_id, run_id, field_name, old_value, new_value, detected_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()
