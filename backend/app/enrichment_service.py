"""
Business Lead Generator — Multi-Engine Lead Enrichment Service
backend/app/enrichment_service.py

Provides independent, on-demand enrichment engines:
1. Enrich Apify (Google Maps/Places data): Website, Phone, Address, Postal Code, Rating, Reviews, Maps URL
2. Enrich Apollo (Apollo.io B2B contacts): Verified Direct Email, Status/Score, Direct Phone, Employee Count, Sub-industry

Strict Non-Destructive Update Guarantees:
- Never creates duplicate company records.
- Populates ONLY fields that are missing or empty.
- Preserves all existing valid data.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Callable

from apify_client import ApifyClient

try:
    from backend.app import config, contact_enricher, database as db, exporter
    from backend.app.apollo_client import ApolloClient, extract_clean_domain
except ImportError:
    import config
    import contact_enricher
    import database as db
    import exporter
    from apollo_client import ApolloClient, extract_clean_domain

logger = logging.getLogger(__name__)

# Field sets for each engine
APIFY_TARGET_FIELDS = [
    "Website_URL",
    "Has_Website",
    "Primary_Phone",
    "WhatsApp_Number",
    "General_Email",
    "Full_Address",
    "Postal_Code",
    "Google_Maps_URL",
    "Google_Rating",
    "Reviews_Count",
    "State",
]

APOLLO_TARGET_FIELDS = [
    "DM_Full_Name",
    "DM_Title",
    "DM_Authority_Level",
    "DM_LinkedIn_URL",
    "DM_Direct_Email",
    "DM_Email_Status",
    "DM_Email_Score",
    "DM_Direct_Phone",
    "Employee_Count",
    "Secondary_Industry",
    "Company_Type",
    "Website_URL",
    "Company_LinkedIn",
]


def is_field_empty(val: Any, field_name: str = "") -> bool:
    """Checks if a field value in a record is considered empty."""
    if val is None:
        return True
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "undefined", "n/a", "not discovered", "no email found"):
        return True
    if field_name == "Reviews_Count" and (val == 0 or s == "0"):
        return True
    if field_name == "Has_Website" and s.lower() in ("no", "0"):
        return True
    return False


def get_record_missing_fields(record: dict[str, Any], engine: str) -> list[str]:
    """Returns list of target field names that are currently missing in the record."""
    if engine == "apify":
        target = [f for f in APIFY_TARGET_FIELDS if f != "Has_Website"]
    elif engine == "apollo":
        target = APOLLO_TARGET_FIELDS
    else:
        target = []

    missing = []
    for f in target:
        if is_field_empty(record.get(f), f):
            missing.append(f)
    return missing


def preview_enrichment(
    sheet_name: str,
    engine: str,
    selected_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Computes a preview for an enrichment action before execution.
    Returns counts, eligible records, missing fields, and estimated cost.
    """
    target_sheet = config.clean_sheet_name(sheet_name or config.get_active_sheet())
    config.set_active_sheet(target_sheet)
    db.init_db(target_sheet)

    all_records = db.get_all_records()
    selected_set = set(selected_ids) if selected_ids else None

    # Filter by user selection if provided
    pool = [r for r in all_records if not selected_set or r.get("Record_ID") in selected_set]

    eligible_records = []
    for r in pool:
        missing = get_record_missing_fields(r, engine)
        if missing:
            eligible_records.append({
                "record_id": r.get("Record_ID"),
                "company_name": r.get("Company_Name") or "Unknown",
                "city": r.get("City") or "",
                "state": r.get("State") or "",
                "missing_fields": missing,
            })

    # Validate engine configuration
    is_configured = False
    config_error = ""
    cost_estimate = ""
    fields_to_fill = []

    if engine == "apify":
        fields_to_fill = APIFY_TARGET_FIELDS
        token = (config.APIFY_API_TOKEN or "").strip()
        is_configured = bool(token and token.lower() not in ("your_apify_token_here", "your_token_here"))
        if not is_configured:
            config_error = "Apify API Token is missing. Configure it in Settings."
        cost_estimate = f"~${len(eligible_records) * 0.011:.2f} USD (~$0.011 per business query)"

    elif engine == "apollo":
        fields_to_fill = APOLLO_TARGET_FIELDS
        client = ApolloClient()
        is_configured, msg = client.is_configured()
        if not is_configured:
            config_error = msg
        missing_email_records = [r for r in pool if is_field_empty(r.get("DM_Direct_Email"), "DM_Direct_Email")]
        has_email_count = len(pool) - len(missing_email_records)
        if has_email_count > 0:
            cost_estimate = f"1 credit per verified email unlocked (Max {len(missing_email_records)} credits; {has_email_count} already have emails & use 0 credits)"
        else:
            cost_estimate = f"1 credit per verified email discovered (Max {len(missing_email_records)} credits; 0 credits if no email found)"

    return {
        "engine": engine,
        "sheet_name": target_sheet,
        "total_records_in_sheet": len(all_records),
        "selected_records_count": len(pool),
        "eligible_count": len(eligible_records),
        "fields_to_fill": fields_to_fill,
        "sample_records": eligible_records[:10],
        "cost_estimate": cost_estimate,
        "is_configured": is_configured,
        "config_error": config_error,
    }


# ── Execution Runners ─────────────────────────────────────────────────────────

async def run_apollo_enrichment(
    records: list[dict[str, Any]],
    log: Callable[[str, str], None],
    job: dict[str, Any],
) -> int:
    """Enriches records with Apollo.io contacts and firmographics."""
    client = ApolloClient()
    ok, err = client.is_configured()
    if not ok:
        raise ValueError(err)

    total = len(records)
    log(f"Starting Apollo.io enrichment across {total} lead record(s)...")
    updated_records_count = 0
    total_fields_filled = 0

    for idx, rec in enumerate(records, 1):
        if job.get("cancelled"):
            log("Enrichment halted by user.", "warning")
            break
        rec_id = rec.get("Record_ID")
        company = rec.get("Company_Name") or "Company"
        existing_email = (rec.get("DM_Direct_Email") or "").strip()
        job["current_location"] = f"{rec.get('City', '')}, {rec.get('State', '')}".strip(', ')
        job["current_industry"] = company

        if existing_email and "@" in existing_email:
            log(f"[{idx}/{total}] Checking firmographics for '{company}' ({rec_id})... [Email already present: 0 credits used]")
        else:
            log(f"[{idx}/{total}] Querying Apollo for '{company}' ({rec_id})...")

        try:
            new_fields = await client.enrich_lead(rec)
            if new_fields:
                success, changed_cols = db.enrich_record_in_place(
                    rec_id,
                    new_fields,
                    overwrite=False,
                    updated_by="Enrich Apollo",
                )
                if success and changed_cols:
                    updated_records_count += 1
                    total_fields_filled += len(changed_cols)
                    job["total_saved"] = updated_records_count
                    cols_str = ", ".join(changed_cols)
                    email_str = f" [Email: {new_fields.get('DM_Direct_Email')}]" if new_fields.get('DM_Direct_Email') else ""
                    log(f"  ✓ Enriched {company}: populated {len(changed_cols)} field(s) ({cols_str}){email_str}")
                else:
                    log(f"  - No new empty fields to update for {company}")
            else:
                log(f"  - No Apollo match found for {company}")
        except Exception as e:
            log(f"  [!] Apollo error for {company}: {e}", "warning")

        job["completed_steps"] = idx
        await asyncio.sleep(0.4)  # Respect Apollo rate limits

    return updated_records_count


def _clean_company_name(name: str) -> str:
    """Normalizes company name for robust fuzzy matching."""
    if not name:
        return ""
    # Strip common corporate suffixes and punctuation
    cleaned = re.sub(
        r'\b(llc|inc|corp|corporation|ltd|limited|co|company|group|services|agency|consulting|recruiting|staffing)\b',
        '',
        name.lower(),
    )
    return re.sub(r'[^a-z0-9]', '', cleaned)


async def run_apify_enrichment(
    records: list[dict[str, Any]],
    log: Callable[[str, str], None],
    job: dict[str, Any],
    run_id: str | None = None,
    dataset_id: str | None = None,
) -> int:
    """Enriches records using Apify Google Places crawler."""
    token = (config.APIFY_API_TOKEN or "").strip()
    if not token:
        raise ValueError("Apify API Token is not configured.")

    total = len(records)
    log(f"Starting Apify Google Places enrichment across {total} lead record(s)...")

    # Build targeted search query for each record
    search_queries = []
    record_map: dict[str, dict] = {}
    clean_name_map: dict[str, dict] = {}

    for r in records:
        c_name = (r.get("Company_Name") or "").strip()
        city = (r.get("City") or "").strip()
        state = (r.get("State") or "").strip()
        query = f"{c_name} {city} {state}".strip()
        if not query:
            query = c_name
        search_queries.append(query)
        record_map[query.lower()] = r

        c_clean = _clean_company_name(c_name)
        if c_clean:
            clean_name_map[c_clean] = r

    actor_client = ApifyClient(token)
    actor_id = getattr(config, "APIFY_ACTOR_ID", "compass/crawler-google-places")

    actor_input = {
        "searchStringsArray": search_queries,
        "maxCrawledPlacesPerSearch": 1,
        "language": "en",
        "maxImages": 0,
        "maxReviews": 0,
        "scrapePlaceDetailPage": False,
        "includeOpeningHours": False,
        "additionalInfo": False,
    }

    loop = asyncio.get_running_loop()

    # Support recovering / attaching to an existing Apify run or dataset
    if run_id and not dataset_id:
        log(f"Connecting to existing Apify run '{run_id}'...")
        def _get_existing_run():
            r = actor_client.run(run_id).get()
            return getattr(r, "default_dataset_id", None) or getattr(r, "defaultDatasetId", None) or (r.get("defaultDatasetId") if isinstance(r, dict) else None)
        dataset_id = await loop.run_in_executor(None, _get_existing_run)

    if not dataset_id:
        log(f"Deploying Apify actor '{actor_id}' for {len(search_queries)} search queries...")

        def _call_apify():
            return actor_client.actor(actor_id).call(run_input=actor_input)

        run = await loop.run_in_executor(None, _call_apify)
        if not run:
            raise RuntimeError("Apify actor run failed to execute.")

        dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
        if not dataset_id and isinstance(run, dict):
            dataset_id = run.get("default_dataset_id") or run.get("defaultDatasetId")

        run_status = getattr(run, "status", None) or (run.get("status") if isinstance(run, dict) else "SUCCEEDED")
        run_id_val = getattr(run, "id", None) or (run.get("id") if isinstance(run, dict) else "")

        if not dataset_id:
            raise RuntimeError(f"Apify actor run '{run_id_val}' failed to return a dataset ID (status: {run_status}).")

        log(f"Apify run finished ({run_status}). Fetching results from dataset '{dataset_id}'...")
    else:
        log(f"Fetching extracted items directly from Apify dataset '{dataset_id}'...")

    def _fetch_items():
        return list(actor_client.dataset(dataset_id).iterate_items())

    items = await loop.run_in_executor(None, _fetch_items)
    log(f"Retrieved {len(items)} place results from Google Places.")

    updated_records_count = 0

    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict) or "error" in item:
            continue

        # Match back to record: 1. By query search string
        search_str = (item.get("searchString") or "").strip().lower()
        matched_rec = record_map.get(search_str)

        # 2. Fallback match by clean company name
        place_title = (item.get("title") or "").strip()
        clean_place = _clean_company_name(place_title)

        if not matched_rec and clean_place:
            matched_rec = clean_name_map.get(clean_place)

        if not matched_rec and clean_place:
            for c_clean, rec in clean_name_map.items():
                if c_clean in clean_place or clean_place in c_clean:
                    matched_rec = rec
                    break

        if not matched_rec:
            continue

        rec_id = matched_rec.get("Record_ID")
        company = matched_rec.get("Company_Name") or "Company"

        new_fields: dict[str, Any] = {}
        website = item.get("website") or ""
        if website:
            if not website.startswith(("http://", "https://")):
                website = "https://" + website
            new_fields["Website_URL"] = website
            new_fields["Has_Website"] = "Yes"

        phone = item.get("phone") or ""
        if phone:
            new_fields["Primary_Phone"] = phone
            if is_field_empty(matched_rec.get("WhatsApp_Number")):
                digits = re.sub(r"\D", "", phone)
                if len(digits) >= 9:
                    new_fields["WhatsApp_Number"] = phone

        addr = item.get("address") or ""
        if addr:
            new_fields["Full_Address"] = addr

        postal = item.get("postalCode") or ""
        if postal:
            new_fields["Postal_Code"] = postal

        g_url = item.get("url") or ""
        if g_url:
            new_fields["Google_Maps_URL"] = g_url

        rating = item.get("totalScore")
        if rating is not None:
            new_fields["Google_Rating"] = rating

        reviews = item.get("reviewsCount")
        if reviews is not None:
            new_fields["Reviews_Count"] = reviews

        # Primary industry / category
        cat = item.get("categoryName") or (
            item.get("categories", [None])[0]
            if isinstance(item.get("categories"), list) and item.get("categories")
            else None
        )
        if cat and is_field_empty(matched_rec.get("Primary_Industry")):
            new_fields["Primary_Industry"] = cat

        # City / State extraction if missing
        if is_field_empty(matched_rec.get("City")) and item.get("city"):
            new_fields["City"] = item.get("city")

        if is_field_empty(matched_rec.get("State")):
            state_val = db._infer_state(addr, matched_rec.get("City", "")) or item.get("state")
            if state_val:
                new_fields["State"] = state_val

        # Company LinkedIn if present in social links
        soc_li = (
            item.get("linkedIn")
            or item.get("companyLinkedinUrl")
            or (item.get("socialMedia", {}).get("linkedIn") if isinstance(item.get("socialMedia"), dict) else None)
        )
        if soc_li and is_field_empty(matched_rec.get("Company_LinkedIn")):
            new_fields["Company_LinkedIn"] = soc_li

        if new_fields:
            success, changed = db.enrich_record_in_place(
                rec_id,
                new_fields,
                overwrite=False,
                updated_by="Enrich Apify",
            )
            if success and changed:
                updated_records_count += 1
                job["total_saved"] = updated_records_count
                log(f"  ✓ Enriched {company}: populated {', '.join(changed)}")

        job["completed_steps"] = idx

    # Phase 2: For records that have a Website_URL but no General_Email, scan their websites for public contact emails
    records_to_scan = []
    for r in records:
        r_id = r.get("Record_ID")
        current_db_rec = db.get_record_by_id(r_id) or r
        web = (current_db_rec.get("Website_URL") or "").strip()
        gen_email = current_db_rec.get("General_Email")
        if web and is_field_empty(gen_email):
            records_to_scan.append(current_db_rec)

    if records_to_scan:
        log(f"Scanning {len(records_to_scan)} company website(s) for public General Email and social links...")
        try:
            contact_results = await contact_enricher.enrich_contacts_batch(records_to_scan)
            for r_id, c_fields in contact_results.items():
                if c_fields:
                    success, changed = db.enrich_record_in_place(
                        r_id,
                        c_fields,
                        overwrite=False,
                        updated_by="Enrich Apify (Web Scan)",
                    )
                    if success and changed:
                        updated_records_count += 1
                        job["total_saved"] = updated_records_count
                        log(f"  ✓ Website scan populated {', '.join(changed)} for {r_id}")
        except Exception as exc:
            log(f"Website contact scan notice: {exc}", "warning")

    return updated_records_count


async def run_enrichment_job(
    job_id: str,
    sheet_name: str,
    engine: str,
    selected_ids: list[str] | None = None,
    active_jobs: dict[str, dict[str, Any]] | None = None,
    run_id: str | None = None,
    dataset_id: str | None = None,
):
    """
    Background worker orchestrating the requested enrichment engine.
    Updates active_jobs logs and states for real-time SSE streaming.
    """
    target_sheet = config.clean_sheet_name(sheet_name or config.get_active_sheet())
    config.set_active_sheet(target_sheet)
    db.init_db(target_sheet)

    job = (active_jobs or {}).get(job_id, {})
    job["sheet_name"] = target_sheet
    job["status"] = "running"
    job["engine"] = engine
    job["started_at"] = datetime.now().isoformat()
    job["completed_steps"] = 0
    job["total_saved"] = 0
    job["stage"] = f"Initializing Enrich {engine.title()}"

    def log(msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = {"time": ts, "message": msg, "level": level}
        job["logs"].append(entry)
        logger.info("[%s - %s] %s", job_id, engine, msg)

    try:
        log(f"Connected to enrichment worker #{job_id}")
        log(f"Target Master Sheet: '{target_sheet}' ({config.DB_PATH})")
        log(f"Enrichment Engine: {engine.upper()}")

        # 1. Gather pool of records
        all_records = db.get_all_records()
        selected_set = set(selected_ids) if selected_ids else None
        pool = [r for r in all_records if not selected_set or r.get("Record_ID") in selected_set]

        # 2. Filter strictly for records with missing fields for this engine
        eligible = [r for r in pool if get_record_missing_fields(r, engine)]
        job["total_steps"] = len(eligible)

        if not eligible:
            log("All candidate records already have these fields populated! No enrichment required.", "info")
            job["status"] = "completed"
            job["stage"] = "Enrichment Complete (No Missing Fields)"
            job["finished_at"] = datetime.now().isoformat()
            return

        log(f"Identified {len(eligible)} record(s) with missing data requiring enrichment.")

        # 3. Dispatch to engine runner
        if engine == "apollo":
            job["stage"] = "Stage 1: Apollo.io B2B Enrichment"
            updated = await run_apollo_enrichment(eligible, log, job)
        elif engine == "apify":
            job["stage"] = "Stage 1: Apify Google Maps Enrichment"
            updated = await run_apify_enrichment(eligible, log, job, run_id=run_id, dataset_id=dataset_id)
        else:
            raise ValueError(f"Unknown enrichment engine: {engine}")

        # 4. Excel Synchronization
        try:
            log(f"Regenerating 2-sheet Excel database '{target_sheet}.xlsx'...")
            exporter.XLSXExporter().export(config.XLSX_PATH)
            log(f"Excel workbook refreshed with latest enriched fields.")
        except Exception as exc:
            log(f"Excel refresh notice: {exc}", "warning")

        job["status"] = "completed"
        job["stage"] = "Enrichment Complete"
        job["finished_at"] = datetime.now().isoformat()
        log(f"Enrichment completed! Successfully updated {updated} record(s) without modifying existing valid data.")

    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)
        log(f"[FATAL] Enrichment terminated: {exc}", "error")
        logger.exception("Error in enrichment job %s", job_id)
