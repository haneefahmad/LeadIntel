# ============================================================
# validator.py — Stage 2: Website validation
# Checks if each website is real, reachable, HTTPS, and not blocked
# Runs up to 50 checks in PARALLEL using Python async for speed
#
# FIXES IN THIS VERSION:
#   1. One shared httpx.AsyncClient for all URLs — avoids creating
#      and destroying a full connection pool per URL.
#   2. SSL certificate check wrapped with asyncio.to_thread so it
#      no longer blocks the async event loop during validation.
# ============================================================

import asyncio                          # Python async runtime — enables true parallel execution
import ssl                              # Built-in SSL certificate checking library
import socket                           # Used for opening raw TCP connections for SSL checks
import re                               # Regular expressions — used for phone number extraction
from urllib.parse import urlparse       # Safely extracts parts of a URL like hostname, scheme

import httpx                            # Async HTTP client — much faster than requests for parallel use

from config import (
    BLOCKED_DOMAINS,                    # List of domain strings we reject
    MAX_CONCURRENT_VALIDATIONS,         # Max simultaneous website checks
    WEBSITE_TIMEOUT_SECONDS,            # Seconds before giving up on a slow site
    SAUDI_PHONE_PATTERN,                # Regex string for Saudi phone numbers
)

# ── BROWSER HEADERS ───────────────────────────────────────────
# Some websites block requests that don't look like a real browser
# These headers mimic a real Chrome browser visiting the page

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",   # Accept English and Arabic content
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── BLOCKLIST CHECK ───────────────────────────────────────────

def is_blocked_domain(url: str) -> bool:
    """
    Returns True if the URL belongs to a blocked domain.
    We reject social media, directories, review sites, and PDFs.
    """
    if not url:                              # If URL is empty or None treat it as blocked
        return True
    url_lower = url.lower()                  # Lowercase the URL for case-insensitive matching
    for blocked in BLOCKED_DOMAINS:          # Check each blocked domain string
        if blocked.lower() in url_lower:     # If blocked string appears anywhere in the URL
            return True                      # Reject this URL
    return False                             # URL passed all checks — not blocked

# ── SSL CERTIFICATE CHECK ─────────────────────────────────────

def check_ssl_certificate(hostname: str) -> dict:
    """
    Opens a raw SSL connection to port 443 and reads the certificate.
    Returns dict with valid (bool) and expiry (string) fields.
    This runs synchronously — called only after we know the site uses HTTPS.
    """
    try:
        ctx = ssl.create_default_context()                    # Create SSL context using system CA certificates
        with socket.create_connection((hostname, 443), timeout=5) as sock:  # Open TCP connection to HTTPS port
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:  # Perform SSL handshake
                cert   = ssock.getpeercert()                  # Read the server's SSL certificate data
                expiry = cert.get("notAfter", "Unknown")      # Extract expiry date from cert fields
                return {"valid": True, "expiry": expiry}      # Certificate is valid and trusted
    except ssl.SSLCertVerificationError:
        return {"valid": False, "expiry": None}               # Certificate is untrusted or self-signed
    except ssl.SSLError:
        return {"valid": False, "expiry": None}               # Any SSL protocol error
    except Exception:
        return {"valid": False, "expiry": None}               # Connection failed — treat as invalid

# ── SINGLE WEBSITE VALIDATION (ASYNC) ────────────────────────

def detect_https(original_url: str, final_url: str, history: list) -> bool:
    """
    Reliably detects whether a website uses HTTPS.
    Checks THREE sources to avoid false negatives:

    Problem that was happening:
      Some sites start as http:// but redirect to https://
      httpx follows the redirect and the final URL is https://
      BUT some redirect chains go http → https → http (badly configured)
      AND some sites serve https but their Google Maps URL is listed as http://
      Checking only response.url was sometimes wrong.

    Fix: We check three things:
      1. Original URL starts with https — the URL Google Maps stored
      2. Final URL after all redirects starts with https
      3. Any URL in the redirect history used https

    If ANY of these is true → the site supports HTTPS → return True.
    This prevents marking an https site as 0 just because of a redirect quirk.

    Args:
        original_url: The URL we started with (from Google Maps)
        final_url:    The URL after following all redirects
        history:      List of response objects from the redirect chain
    Returns:
        True if the site uses HTTPS by any measure
    """
    # Check 1: original URL already uses https
    if original_url.lower().startswith("https://"):
        return True   # Google Maps stored it as https — trust that

    # Check 2: final URL after redirects uses https
    if str(final_url).lower().startswith("https://"):
        return True   # Site redirected us to https — it supports HTTPS

    # Check 3: any step in the redirect chain used https
    # This catches sites that go http → https → https (final is https)
    # AND sites that go http → https → something-else
    for resp in history:
        if str(resp.url).lower().startswith("https://"):
            return True   # At least one redirect step was https

    return False   # No https found anywhere in the chain

async def validate_website(
    url: str,
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,          # FIX ⑤: shared client passed in, not created here
) -> dict:
    """
    Validates one website URL asynchronously.
    The semaphore limits how many run simultaneously.
    The shared client reuses the connection pool across all URLs.
    Returns a dict with all validation findings for this URL.

    HTTPS FIX: Uses detect_https() which checks original URL,
    final URL, AND redirect history — so sites that redirect from
    http to https are correctly marked as https=True, not 0.

    SSL FIX: check_ssl_certificate is wrapped with asyncio.to_thread
    so the blocking TCP handshake does not stall the event loop.
    """
    result = {
        "url":          url,    # The original URL being tested
        "reachable":    False,  # True if we get any HTTP response
        "https":        False,  # True if site uses HTTPS by any measure
        "ssl_valid":    False,  # True if SSL certificate is valid and trusted
        "ssl_expiry":   None,   # SSL certificate expiry date string
        "status_code":  None,   # HTTP response code (200, 301, 404, etc.)
        "final_url":    url,    # URL after following all redirects
        "blocked":      False,  # True if URL is a social/directory domain
        "html_content": "",     # First 100KB of HTML for parsing later
    }

    # Blocklist check first — no network request needed for blocked domains
    if is_blocked_domain(url):
        result["blocked"] = True
        return result

    async with semaphore:   # Wait for a free slot from the concurrent pool
        try:
            response = await client.get(url)   # Reuse the shared connection pool

            result["reachable"]    = True
            result["status_code"]  = response.status_code
            result["final_url"]    = str(response.url)
            result["html_content"] = response.text[:100000]   # First 100KB of HTML

            # ── HTTPS DETECTION ──────────────────────────────────
            result["https"] = detect_https(
                original_url = url,
                final_url    = str(response.url),
                history      = list(response.history),
            )

            # ── SSL CERTIFICATE CHECK (non-blocking) ─────────────
            # FIX ②: asyncio.to_thread runs the blocking SSL socket
            # handshake in a thread pool — the event loop stays free
            # to continue other concurrent validations.
            if result["https"]:
                https_url = str(response.url)
                if not https_url.startswith("https://"):
                    https_url = url if url.startswith("https://") else str(response.url)

                hostname             = urlparse(https_url).netloc
                hostname             = hostname.split(":")[0]        # Remove port if present
                ssl_info             = await asyncio.to_thread(check_ssl_certificate, hostname)
                result["ssl_valid"]  = ssl_info["valid"]
                result["ssl_expiry"] = ssl_info["expiry"]

        except httpx.TimeoutException:
            result["reachable"] = False   # No response within timeout
        except httpx.TooManyRedirects:
            result["reachable"] = False   # Redirect loop
        except httpx.ConnectError:
            result["reachable"] = False   # DNS failure or server down
        except Exception as e:
            result["reachable"] = False
            print(f"[VALIDATOR] {url}: {type(e).__name__}")

    return result

# ── PARALLEL VALIDATION OF ALL BUSINESSES ────────────────────

async def validate_all_async(businesses: list) -> list:
    """
    Validates all business websites in parallel using asyncio.
    Creates up to MAX_CONCURRENT_VALIDATIONS simultaneous connections.

    FIX ⑤: One shared httpx.AsyncClient is created here and passed
    to every validate_website call.  This means all URLs share a
    single connection pool and TLS session cache instead of each
    URL spinning up and tearing down its own client.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_VALIDATIONS)

    # Split businesses into those with and without websites
    with_site    = [b for b in businesses if b.get("website")]
    without_site = [b for b in businesses if not b.get("website")]

    print(f"[VALIDATOR] {len(with_site)} with website | {len(without_site)} without")

    # Businesses with no website get an empty validation result immediately
    for b in without_site:
        b["validation"] = {
            "reachable": False, "https": False, "ssl_valid": False,
            "blocked": False,   "html_content": "",
        }

    if not with_site:
        return businesses

    print(f"[VALIDATOR] Running {len(with_site)} validations in parallel...")

    # ── SHARED CLIENT ─────────────────────────────────────────
    # One AsyncClient for the entire batch — single connection pool,
    # reused TLS sessions, and no per-URL setup/teardown overhead.
    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=WEBSITE_TIMEOUT_SECONDS,
        follow_redirects=True,
        verify=False,                          # Allow self-signed certs
        limits=httpx.Limits(
            max_connections=MAX_CONCURRENT_VALIDATIONS + 10,
            max_keepalive_connections=MAX_CONCURRENT_VALIDATIONS,
        ),
    ) as client:
        tasks = [
            validate_website(b["website"], semaphore, client)
            for b in with_site
        ]
        results = await asyncio.gather(*tasks)

    # Attach each validation result back to its matching business
    for i, b in enumerate(with_site):
        b["validation"] = results[i]

    return without_site + with_site

def run_validation(businesses: list) -> list:
    """
    Synchronous wrapper so main.py (which is not async) can call the async validator.
    asyncio.run() starts a new event loop, runs the coroutine, and returns the result.
    """
    return asyncio.run(validate_all_async(businesses))   # Start async event loop and wait

# ── STATUS CLASSIFIER ─────────────────────────────────────────

def classify_website_status(business: dict) -> str:
    """
    Returns a simple status string summarizing the website situation.
    Used in main.py to decide how to handle each business.
    """
    if not business.get("website"):
        return "no_website"                      # No URL found on Google Maps listing

    v = business.get("validation", {})           # Get the validation result attached earlier

    if v.get("blocked"):
        return "blocked_domain"                  # URL is a social page or directory

    if not v.get("reachable"):
        return "unreachable"                     # Website exists but is down or timed out

    if not v.get("https"):
        return "no_https"                        # Site loads but uses HTTP instead of HTTPS

    return "valid"                               # Site is live, HTTPS, and not blocked

# ── SAUDI PHONE EXTRACTION ────────────────────────────────────

def extract_saudi_phones(html: str, existing_phone: str = "") -> list:
    """
    Finds Saudi phone numbers in HTML content using regex.
    Combines numbers from the webpage with the number from Google Maps.
    Returns a deduplicated list.
    """
    phones = set()                               # Use a set to automatically remove duplicates

    if existing_phone:
        phones.add(existing_phone.strip())       # Start with the phone from Google Maps listing

    if html:
        matches = re.findall(SAUDI_PHONE_PATTERN, html)  # Apply Saudi phone regex to all HTML text
        for match in matches:
            phones.add(match.strip())            # Add each found number to the set

    return list(phones)                          # Convert set to list for JSON serialization