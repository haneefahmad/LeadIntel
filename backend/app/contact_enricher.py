"""
Generic business contact enrichment.
Crawls business websites for public emails and company LinkedIn profiles.
"""

import asyncio
import logging
import re
import urllib.parse
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:
    from backend.app import config
except ImportError:
    import config


EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
BAD_EMAIL_PARTS = (
    "example.",
    "sentry.",
    "wixpress.",
    "schema.org",
    "yourdomain",
    "domain.com",
    "email.com",
)
BAD_EMAIL_ENDINGS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".css",
    ".js",
)
CONTACT_PATHS = (
    "",
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/team",
    "/management",
    "/leadership",
    "/executive-management",
)


@dataclass
class WebsiteContactResult:
    email: str = ""
    company_linkedin: str = ""
    source_url: str = ""


async def enrich_contacts_batch(
    records: list[dict[str, Any]],
    html_cache: dict[str, str] | None = None,
) -> dict[str, dict]:
    """
    Returns {google_place_id: enrichment_fields}.
    Uses cached homepage HTML if provided to avoid redundant HTTP requests.
    Extracts public emails and company LinkedIn URLs via direct website crawling.
    """
    sem = asyncio.Semaphore(config.MAX_CONCURRENT_WEBSITE_CHECKS)
    results: dict[str, dict] = {}

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(config.WEBSITE_TIMEOUT_SEC),
        follow_redirects=True,
        verify=False,
        trust_env=False,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        },
    ) as client:
        tasks = [
            _enrich_one(
                client,
                sem,
                record,
                html_cache.get(record.get("google_place_id", "")) if html_cache else None,
            )
            for record in records
        ]
        for pid, fields in await asyncio.gather(*tasks):
            if pid and fields:
                results[pid] = fields

    return results


async def _enrich_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    record: dict[str, Any],
    cached_homepage_html: str | None = None,
) -> tuple[str, dict]:
    pid = record.get("Record_ID") or record.get("google_place_id", "")
    website = record.get("Website_URL", "")
    if not pid or not website:
        return pid, {}

    found = WebsiteContactResult()
    base = _base_url(website)

    # 1. First extract contacts from cached homepage HTML if available
    if cached_homepage_html:
        emails = _extract_emails(cached_homepage_html)
        linkedin = _extract_company_linkedin(cached_homepage_html, base)
        if emails and not found.email:
            found.email = emails[0]
            found.source_url = base
        if linkedin and not found.company_linkedin:
            found.company_linkedin = linkedin

    # If both email and company linkedin are already found from homepage, skip all outbound GETs!
    if not (found.email and found.company_linkedin):
        paths_to_crawl = [p for p in CONTACT_PATHS if p] if cached_homepage_html else CONTACT_PATHS
        urls = [urljoin(base, path) for path in paths_to_crawl]

        async with sem:
            for url in urls:
                try:
                    resp = await client.get(url)
                except Exception:
                    continue
                if resp.status_code >= 400:
                    continue
                html = resp.text or ""
                emails = _extract_emails(html)
                linkedin = _extract_company_linkedin(html, url)
                if emails and not found.email:
                    found.email = emails[0]
                    found.source_url = url
                if linkedin and not found.company_linkedin:
                    found.company_linkedin = linkedin
                if found.email and found.company_linkedin:
                    break
                # If email is already discovered and we checked contact or about, don't crawl deep management paths
                if found.email and any(path in url.lower() for path in ("/contact", "/about")):
                    break

    fields: dict[str, Any] = {}
    if found.email:
        fields["Email_General"] = found.email
        fields["Notes"] = _append_note(record.get("Notes"), f"Email source: {found.source_url}")
    if found.company_linkedin:
        fields["Company_LinkedIn_URL"] = found.company_linkedin
    return pid, fields


def _base_url(url: str) -> str:
    parsed = urlparse(url if url.startswith(("http://", "https://")) else f"https://{url}")
    return f"{parsed.scheme}://{parsed.netloc}"


def _extract_emails(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    raw = set(EMAIL_RE.findall(soup.get_text(" ") + " " + html))
    for a in soup.select("a[href^='mailto:']"):
        raw.add(a["href"].split(":", 1)[1].split("?", 1)[0])
    cleaned = []
    for email in raw:
        email = email.strip().strip(".,;:()[]{}<>").lower()
        if not email or any(part in email for part in BAD_EMAIL_PARTS):
            continue
        if email.endswith(BAD_EMAIL_ENDINGS):
            continue
        if email not in cleaned:
            cleaned.append(email)
    return sorted(cleaned, key=_email_rank)


def _email_rank(email: str) -> tuple[int, str]:
    local = email.split("@", 1)[0]
    priority = {
        "commercial": 0,
        "business": 1,
        "sales": 2,
        "marketing": 3,
        "info": 4,
        "contact": 5,
        "customer": 6,
        "support": 7,
    }
    score = min((rank for key, rank in priority.items() if key in local), default=20)
    return score, email


def _extract_company_linkedin(html: str, page_url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"]).split("?", 1)[0]
        lower = href.lower()
        if "linkedin.com/company/" in lower or "linkedin.com/school/" in lower:
            return href.rstrip("/")
    return ""




def _append_note(existing: str | None, note: str) -> str:
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing} | {note}"


IGNORED_SEARCH_DOMAINS = {
    "duckduckgo.com", "google.com", "bing.com", "yahoo.com", "yandex.com", "baidu.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com",
    "wikipedia.org", "yelp.com", "yellowpages.com", "tripadvisor.com",
    "bizmideast.com", "exportbusinessmart.com", "kompass.com", "dnb.com",
    "zoominfo.com", "crunchbase.com", "bloomberg.com", "mapquest.com",
    "foursquare.com", "ich.ma", "saudiyello.com", "saudi-directory.net",
    "saudidatabase.com", "linkedin.com", "pinterest.com", "tiktok.com",
    "waze.com", "apple.com", "play.google.com"
}


async def resolve_company_website(company_name: str, city: str = "", country: str = "") -> str:
    """
    Intelligently resolves an official website URL for a business when Google Maps lacks one.
    Uses search query: "{company_name} {city} {country} official website".
    Returns the canonical website URL or empty string.
    """
    if not company_name:
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    }

    query_str = f"{company_name.strip()} {city.strip()} {country.strip()} official website".strip()
    encoded_q = urllib.parse.quote(query_str)
    search_url = f"https://lite.duckduckgo.com/lite/?q={encoded_q}"

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
            resp = await client.get(search_url, headers=headers)
            if resp.status_code != 200:
                return ""

            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a.result-link"):
                href = a.get("href", "")
                parsed = urllib.parse.urlparse(href)
                params = urllib.parse.parse_qs(parsed.query)
                clean_url = params.get("uddg", [""])[0]
                if clean_url:
                    parsed_clean = urllib.parse.urlparse(clean_url)
                    netloc = parsed_clean.netloc.lower()
                    domain = netloc[4:] if netloc.startswith("www.") else netloc
                    if not domain or any(ign in domain for ign in IGNORED_SEARCH_DOMAINS):
                        continue
                    # Return base site URL
                    return f"{parsed_clean.scheme}://{parsed_clean.netloc}"
    except Exception as e:
        logger.debug("resolve_company_website error for '%s': %s", company_name, e)

    return ""


async def enrich_single_record_from_website(record: dict[str, Any]) -> dict[str, Any]:
    """
    Crawls the website for a single record to discover general email and company LinkedIn.
    """
    url = (record.get("Website_URL") or "").strip()
    if not url:
        return {}

    sem = asyncio.Semaphore(1)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(6.0),
        follow_redirects=True,
        verify=False,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        },
    ) as client:
        _, fields = await _enrich_one(client, sem, record)
        return fields
