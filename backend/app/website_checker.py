"""
EIT Saudi Lead Intelligence — Async website checker.
website_checker.py: httpx concurrent visits + BS4 signal parsing.

For every record with Website_URL, detects:
  reachability, SSL, tech stack, B2B/B2C, year updated,
  CR/VAT numbers, Mada payments, hiring, branches, fleet, industrial facility.

Max concurrency : MAX_CONCURRENT_WEBSITE_CHECKS (config)
Timeout         : WEBSITE_TIMEOUT_SEC (config)
SSL warnings    : suppressed (common on Saudi SME sites)
"""

import asyncio
import logging
import re
import warnings
from typing import Any

import httpx
from bs4 import BeautifulSoup

try:
    from backend.app import config
except ImportError:
    import config

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# Compiled patterns
CR_PATTERN   = re.compile(r'\b(1\d{9}|7\d{9})\b')
VAT_PATTERN  = re.compile(r'\b3\d{14}\b')
YEAR_PATTERN = re.compile(r'©\s*(\d{4})|copyright\s+(\d{4})', re.IGNORECASE)

_PARSEABLE = ("text/html", "application/xhtml", "text/plain")


# ── Public API ────────────────────────────────────────────────────────────────

async def check_batch(
    records: list[dict[str, Any]],
    html_cache: dict[str, str] | None = None,
) -> dict[str, dict]:
    """
    Check all records that have a Website_URL.
    Populates html_cache with {google_place_id: html_text} if provided.
    Returns {google_place_id → signal_dict}.
    """
    sem     = asyncio.Semaphore(config.MAX_CONCURRENT_WEBSITE_CHECKS)
    results: dict[str, dict] = {}

    async with httpx.AsyncClient(
        timeout          = httpx.Timeout(config.WEBSITE_TIMEOUT_SEC),
        follow_redirects = True,
        verify           = False,
        trust_env        = False,
        headers          = {
            "User-Agent":      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/124.0.0.0 Safari/537.36",
            "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        },
        limits = httpx.Limits(max_connections=config.MAX_CONCURRENT_WEBSITE_CHECKS + 5),
    ) as client:
        tasks    = [_check_one(client, sem, r) for r in records if r.get("Website_URL")]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    for record, outcome in zip(
        [r for r in records if r.get("Website_URL")], outcomes
    ):
        pid = record.get("google_place_id", "")
        if isinstance(outcome, Exception):
            results[pid] = _empty()
        else:
            signals, html = outcome
            results[pid] = signals
            if html_cache is not None and pid and html:
                html_cache[pid] = html

    # Records with no website get explicit "No" defaults so green columns are never blank
    for record in records:
        pid = record.get("google_place_id", "")
        if pid and not record.get("Website_URL") and pid not in results:
            results[pid] = _no_website()

    return results


# ── Single-record check ───────────────────────────────────────────────────────

async def _check_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    record: dict,
) -> tuple[dict, str]:
    url = record.get("Website_URL", "")
    async with sem:
        try:
            resp = await client.get(url)

            if resp.status_code >= 400:
                return _empty(), ""

            ct = (resp.headers.get("content-type") or "").lower()
            if not any(t in ct for t in _PARSEABLE):
                return _empty(), ""

            html = resp.text or ""
            return _parse_html(html), html

        except Exception as exc:
            logger.debug("Cannot reach %s: %s", url, type(exc).__name__)
            return _empty(), ""


# ── HTML signal extraction ────────────────────────────────────────────────────

def _parse_html(html: str) -> dict:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements to avoid clean number string collision false-positives
    for s in soup(["script", "style", "noscript"]):
        s.decompose()

    body_text  = soup.get_text(separator=" ", strip=True)
    body_lower = body_text.lower()

    return {
        "Has_Website":                "Yes",
        "Year_Last_Updated":          _detect_year(soup, body_text),
        "Tech_Stack_Notes":           _detect_tech_stack(html),
        "B2B_or_B2C":                 _detect_b2b_b2c(body_lower),
        "Industrial_Facility":        _kw(body_lower, [
            "factory", "plant", "warehouse", "facility", "manufacturing",
            "production line", "assembly", "industrial zone", "مصنع", "مستودع",
        ]),
        "Customer_Facing_Operations": _kw(body_lower, [
            "walk in", "walk-in", "visit us", "open to public", "retail",
            "showroom", "clinic", "appointment", "book now", "زيارة",
        ]),
        "Has_Multiple_Branches":      _kw(body_lower, [
            "branches", "locations", "our offices", "multiple locations",
            "فروعنا", "مواقعنا", "branch",
        ]),
        "Hiring_Signal":              _detect_hiring(soup, body_lower),
        "Displays_CR_Number":         "Yes" if CR_PATTERN.search(body_text) else "No",
        "Displays_VAT_Number":        "Yes" if VAT_PATTERN.search(body_text) else "No",
        "Mada_Payment_Visible":       _kw(body_lower, [
            "mada", "مدى", "tap payment", "stc pay", "apple pay",
            "payment gateway", "visa", "mastercard",
        ]),
        "Has_Fleet":                  _kw(body_lower, [
            "fleet", "vehicles", "trucks", "delivery vehicles",
            "شاحنات", "أسطول", "مركبات",
        ]),
    }


# ── Signal detectors ──────────────────────────────────────────────────────────

def _detect_year(soup: BeautifulSoup, body_text: str) -> str:
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        if name in ("article:modified_time", "article:published_time", "date"):
            content = meta.get("content") or ""
            m = re.search(r"(\d{4})", content)
            if m:
                return m.group(1)
    m = YEAR_PATTERN.search(body_text)
    if m:
        return m.group(1) or m.group(2) or ""
    return ""


def _detect_tech_stack(html: str) -> str:
    html_lower = html.lower()
    detected   = [
        tech for tech, patterns in config.TECH_PATTERNS.items()
        if any(p.lower() in html_lower for p in patterns)
    ]
    return ", ".join(detected)


def _detect_b2b_b2c(body_lower: str) -> str:
    b2b = sum(1 for kw in config.B2B_KEYWORDS if kw in body_lower)
    b2c = sum(1 for kw in config.B2C_KEYWORDS if kw in body_lower)
    if b2b > 0 and b2c > 0:
        return "Both"
    if b2b > b2c:
        return "B2B"
    if b2c > b2b:
        return "B2C"
    return "Unknown"


def _detect_hiring(soup: BeautifulSoup, body_lower: str) -> str:
    for a in soup.find_all("a", href=True):
        if any(kw in a["href"].lower() for kw in ("career", "job", "vacanc", "hiring")):
            return "Yes"
    career_kws = [
        "careers", "jobs", "join us", "join our team", "vacancies",
        "we are hiring", "open positions", "وظائف", "انضم إلينا",
    ]
    return "Yes" if any(kw in body_lower for kw in career_kws) else "No"


def _kw(text: str, keywords: list[str]) -> str:
    return "Yes" if any(kw in text for kw in keywords) else "No"


def _empty() -> dict:
    """Default signals for records that have a URL but couldn't be reached/parsed."""
    return {
        "Has_Website":                "Yes",
        "Year_Last_Updated":          "",
        "Tech_Stack_Notes":           "",
        "B2B_or_B2C":                 "Unknown",
        "Industrial_Facility":        "No",
        "Customer_Facing_Operations": "No",
        "Has_Multiple_Branches":      "No",
        "Hiring_Signal":              "No",
        "Displays_CR_Number":         "No",
        "Displays_VAT_Number":         "No",
        "Mada_Payment_Visible":       "No",
        "Has_Fleet":                  "No",
    }


def _no_website() -> dict:
    """Default signals for records that have no website URL at all."""
    return {
        "Has_Website":                "No",
        "Year_Last_Updated":          "",
        "Tech_Stack_Notes":           "",
        "B2B_or_B2C":                 "Unknown",
        "Industrial_Facility":        "No",
        "Customer_Facing_Operations": "No",
        "Has_Multiple_Branches":      "No",
        "Hiring_Signal":              "No",
        "Displays_CR_Number":         "No",
        "Displays_VAT_Number":         "No",
        "Mada_Payment_Visible":       "No",
        "Has_Fleet":                  "No",
    }