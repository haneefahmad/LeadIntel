# ============================================================
# auditor.py — Stage 3: Technical audit + contact extraction
# Calls Google PageSpeed Insights API for performance scores
# Parses HTML with lxml (11x faster than BeautifulSoup)
#
# FIXES IN THIS VERSION:
#   ⑦ PSI calls now run concurrently via asyncio.to_thread with
#      a semaphore — PSI_CONCURRENT_LIMIT parallel calls (default 5).
#      A batch of 60 audits that took ~10 min sequentially now
#      finishes in ~2 min.
#   The public interface is unchanged: call run_audit_all(businesses)
#   which pre-attaches audit{} to each business dict, then call
#   process_one() as before.
# ============================================================

import asyncio                               # For concurrent PSI calls
import time                                  # For adding delays between PageSpeed API calls
import re                                    # Regular expressions — used for email extraction
import requests                              # Standard HTTP library — used for the PSI API call
from urllib.parse import urljoin, urlparse   # For converting relative URLs to absolute

from lxml import html as lxml_html          # lxml — C-based HTML parser, very fast

from config import (
    PSI_API_KEY,                # Your Google Cloud API key
    PSI_API_URL,                # PageSpeed Insights API endpoint URL
    PSI_CONCURRENT_LIMIT,       # Max parallel PSI API calls
    SEO_SCORE_THRESHOLD,        # Score threshold for "weak SEO"
    PERFORMANCE_THRESHOLD,      # Score threshold for "slow performance"
    ACCESSIBILITY_THRESHOLD,    # Score threshold for "poor accessibility"
    BEST_PRACTICES_THRESHOLD,   # Score threshold for "poor practices"
)
from contact_utils import dedupe_emails, extract_whatsapp_number

# ── PAGESPEED INSIGHTS API CALL ───────────────────────────────

def get_pagespeed_scores(url: str) -> dict:
    """
    Calls the Google PageSpeed Insights API for the given URL.
    Returns a dict with SEO, performance, accessibility, and best practices scores.
    Also returns mobile_friendly as 1 or 0.
    """
    # Default result returned on any API failure — None scores won't trigger lead flags
    default_result = {
        "seo_score":            None,
        "performance_score":    None,
        "accessibility_score":  None,
        "best_practices_score": None,
        "mobile_friendly":      None,
        "psi_error":            True,   # Flag indicating the API call failed
    }

    try:
        # Build the query parameters for the API request
        params = {
            "url":      url,         # The website URL to analyze
            "key":      PSI_API_KEY, # Your Google API key for authentication
            "strategy": "mobile",    # Test mobile version — more relevant for Saudi users
            "category": [            # Request all four score categories in one call
                "PERFORMANCE",
                "SEO",
                "ACCESSIBILITY",
                "BEST_PRACTICES",
            ],
        }

        # Make the HTTP GET request to the PSI API — 30s timeout because PSI can be slow
        response = requests.get(PSI_API_URL, params=params, timeout=30)

        if response.status_code != 200:                    # If API returned an error response
            print(f"[PSI] HTTP {response.status_code} for {url}")
            return default_result                          # Return empty scores

        data = response.json()                             # Parse the JSON response body

        # PSI scores are nested at: lighthouseResult → categories → [name] → score
        categories = data.get("lighthouseResult", {}).get("categories", {})

        def extract_score(key: str):
            """Helper: safely gets a category score and converts 0.0–1.0 to 0–100."""
            raw = categories.get(key, {}).get("score")   # Raw score is between 0.0 and 1.0
            if raw is None:
                return None                               # Score not available for this category
            return round(raw * 100, 1)                   # Multiply by 100 and round to 1 decimal

        seo           = extract_score("seo")              # e.g. 0.43 becomes 43.0
        performance   = extract_score("performance")      # e.g. 0.72 becomes 72.0
        accessibility = extract_score("accessibility")    # e.g. 0.61 becomes 61.0
        best_practices = extract_score("best-practices")  # e.g. 0.58 becomes 58.0

        # Mobile friendliness is in the audits section — separate from category scores
        audits          = data.get("lighthouseResult", {}).get("audits", {})
        viewport        = audits.get("viewport", {})      # The viewport meta-tag audit
        mobile_friendly = viewport.get("score", 0) == 1  # Score of 1.0 = mobile friendly

        time.sleep(0.5)  # Wait 0.5s between requests — PSI quota is 240 per 4 minutes

        return {
            "seo_score":            seo,
            "performance_score":    performance,
            "accessibility_score":  accessibility,
            "best_practices_score": best_practices,
            "mobile_friendly":      1 if mobile_friendly else 0,  # Convert bool to int for DB
            "psi_error":            False,  # No error — successful API call
        }

    except requests.Timeout:
        print(f"[PSI] Timeout: {url}")     # PSI took longer than 30 seconds
        return default_result
    except Exception as e:
        print(f"[PSI] Error: {url}: {e}") # Unexpected error (network, JSON, etc.)
        return default_result

# ── HTML PARSING WITH LXML ────────────────────────────────────

def parse_html(html_content: str, base_url: str) -> dict:
    """
    Parses the website HTML to extract SEO elements, emails, and social links.
    Uses lxml which is C-based and 11x faster than BeautifulSoup at scale.
    """
    result = {
        "emails":            [],    # Email addresses found on the page
        "social_links":      {},    # Social media URLs found — keyed by platform name
        "whatsapp_numbers":  [],
        "linkedin_company_url": "",
        "linkedin_profile_urls": [],
        "decision_maker_linkedin": "",
        "has_meta_desc":     False, # True if <meta name="description"> exists
        "has_title":         False, # True if <title> tag exists with content
        "meta_desc_length":  0,     # Character length of the meta description
        "title_text":        "",    # Text content inside the <title> tag
        "contact_page_url":  None,  # URL to a contact page if found on this page
    }

    if not html_content:     # If no HTML was captured during validation
        return result        # Return empty result — nothing to parse

    try:
        tree = lxml_html.fromstring(html_content)
        # fromstring() parses the HTML string into an lxml element tree
        # lxml is written in C so this parse step is extremely fast

        # ── TITLE TAG ──────────────────────────────────────────
        titles = tree.xpath("//title/text()")   # XPath selects text inside <title> tags
        if titles and titles[0].strip():        # If title exists and contains non-empty text
            result["has_title"]  = True
            result["title_text"] = titles[0].strip()[:200]   # Store first 200 chars max

        # ── META DESCRIPTION ───────────────────────────────────
        meta_descs = tree.xpath('//meta[@name="description"]/@content')
        # XPath: find <meta> tags where name="description" and get their content attribute
        if meta_descs and meta_descs[0].strip():           # If description exists with content
            result["has_meta_desc"]    = True
            result["meta_desc_length"] = len(meta_descs[0].strip())  # Count characters

        # ── EMAIL ADDRESSES ─────────────────────────────────────
        # Method 1: Look for mailto: links in <a href="mailto:..."> tags
        mailto_links = tree.xpath('//a[starts-with(@href, "mailto:")]/@href')
        for mailto in mailto_links:
            email = mailto.replace("mailto:", "").strip()  # Remove "mailto:" prefix to get email
            if "@" in email and "." in email:              # Basic format check — must have @ and .
                result["emails"].append(email)             # Add to emails list

        # Method 2: Use regex to find emails hidden in plain text or JavaScript
        email_regex = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        found_emails = re.findall(email_regex, html_content)  # Search entire raw HTML
        for email in found_emails:
            if email not in result["emails"]:              # Skip already-found emails
                # Filter out false positives (image filenames with @ are not emails)
                skip_extensions = [".png", ".jpg", ".gif", ".css", ".js", ".svg"]
                if not any(ext in email.lower() for ext in skip_extensions):
                    result["emails"].append(email)         # Add clean email to list

        result["emails"] = dedupe_emails(result["emails"])    # Deduplicate the full email list

        # ── SOCIAL MEDIA LINKS ──────────────────────────────────
        all_links = tree.xpath("//a/@href")   # Get href attribute from every <a> tag on the page

        # Map of platform name to the domain we look for in links
        social_map = {
            "instagram": "instagram.com",
            "facebook":  "facebook.com",
            "linkedin":  "linkedin.com",
            "twitter":   "twitter.com",
            "snapchat":  "snapchat.com",
            "tiktok":    "tiktok.com",
            "youtube":   "youtube.com",
            "whatsapp":  "wa.me",
        }

        for link in all_links:                             # Loop every anchor link on the page
            absolute_link = urljoin(base_url, str(link))
            for platform, domain in social_map.items():   # Check each social platform domain
                if domain in absolute_link.lower():            # If domain appears in the link URL
                    result["social_links"][platform] = absolute_link   # Store platform: URL in dict

            link_lower = absolute_link.lower()
            if "wa.me" in link_lower or "api.whatsapp.com" in link_lower:
                whatsapp_number = extract_whatsapp_number(absolute_link)
                if whatsapp_number:
                    result["whatsapp_numbers"].append(whatsapp_number)

            if "linkedin.com/company/" in link_lower and not result["linkedin_company_url"]:
                result["linkedin_company_url"] = absolute_link

            if "linkedin.com/in/" in link_lower:
                result["linkedin_profile_urls"].append(absolute_link)

        result["whatsapp_numbers"] = list(dict.fromkeys(result["whatsapp_numbers"]))
        result["linkedin_profile_urls"] = list(dict.fromkeys(result["linkedin_profile_urls"]))
        if result["linkedin_profile_urls"]:
            result["decision_maker_linkedin"] = result["linkedin_profile_urls"][0]

        # ── CONTACT PAGE LINK ───────────────────────────────────
        # XPath: find anchor tags where href or link text contains "contact" (case-insensitive)
        contact_links = tree.xpath(
            '//a[contains(translate(@href, "CONTACT", "contact"), "contact") or '
            'contains(translate(normalize-space(text()), "CONTACT", "contact"), "contact")]/@href'
        )
        if contact_links:
            href = contact_links[0]                        # Take the first contact link found
            if href.startswith("http"):
                result["contact_page_url"] = href          # Already an absolute URL — use as-is
            elif href.startswith("/"):
                result["contact_page_url"] = urljoin(base_url, href)  # Convert relative to absolute

    except Exception as e:
        print(f"[AUDITOR] HTML parse error: {e}")         # Log error but don't crash the pipeline

    return result   # Return all extracted data

# ── ISSUE DETECTION ───────────────────────────────────────────

def detect_issues(psi: dict, html_data: dict, validation: dict) -> list:
    """
    Builds a human-readable list of specific problems found on this website.
    Each issue string will be shown in the CSV under "Issues Found".
    """
    issues = []   # Empty list — we append each problem as a string

    # Check PSI scores against configured thresholds
    if psi.get("seo_score") is not None and psi["seo_score"] < SEO_SCORE_THRESHOLD:
        issues.append(f"Poor SEO score ({psi['seo_score']}/100)")

    if psi.get("performance_score") is not None and psi["performance_score"] < PERFORMANCE_THRESHOLD:
        issues.append(f"Slow website — performance score {psi['performance_score']}/100")

    if psi.get("accessibility_score") is not None and psi["accessibility_score"] < ACCESSIBILITY_THRESHOLD:
        issues.append(f"Poor accessibility ({psi['accessibility_score']}/100)")

    if psi.get("best_practices_score") is not None and psi["best_practices_score"] < BEST_PRACTICES_THRESHOLD:
        issues.append(f"Poor technical practices ({psi['best_practices_score']}/100)")

    # Check HTTPS and SSL certificate status
    if not validation.get("https"):
        issues.append("No HTTPS — website is not secure")              # Missing SSL entirely

    if validation.get("https") and not validation.get("ssl_valid"):
        issues.append("Invalid or expired SSL certificate")            # Has HTTPS but cert is bad

    # Check mobile friendliness
    if psi.get("mobile_friendly") == 0:
        issues.append("Not mobile friendly")                           # Fails mobile test

    # Check HTML SEO structure
    if not html_data.get("has_title"):
        issues.append("Missing <title> tag")                           # No page title

    if not html_data.get("has_meta_desc"):
        issues.append("Missing meta description")                      # No SEO description

    if html_data.get("has_meta_desc") and html_data.get("meta_desc_length", 0) < 50:
        issues.append("Meta description too short (under 50 characters)")  # Description too brief

    return issues   # Return complete list of issue strings

# ── WEAK WEBSITE DETECTOR ─────────────────────────────────────

def is_weak_website(psi: dict, validation: dict) -> bool:
    """
    Returns True if this website qualifies as weak enough to need AI analysis.
    This is the GATE that controls AI cost — only weak sites proceed to Stage 4.
    """
    if not validation.get("https"):        return True   # No HTTPS = always weak
    if not validation.get("ssl_valid"):    return True   # Bad SSL cert = weak

    seo  = psi.get("seo_score")
    perf = psi.get("performance_score")
    acc  = psi.get("accessibility_score")
    bp   = psi.get("best_practices_score")

    if seo  is not None and seo  < SEO_SCORE_THRESHOLD:          return True
    if perf is not None and perf < PERFORMANCE_THRESHOLD:         return True
    if acc  is not None and acc  < ACCESSIBILITY_THRESHOLD:       return True
    if bp   is not None and bp   < BEST_PRACTICES_THRESHOLD:      return True
    if psi.get("mobile_friendly") == 0:                           return True

    return False   # All scores pass — this website is decent quality

# ── MAIN AUDIT FUNCTION ───────────────────────────────────────

def audit_website(business: dict) -> dict:
    """
    Runs the complete technical audit for one business.
    Combines PSI API scores + HTML parsing + issue detection.
    Called from main.py for each business that passed validation.
    """
    url        = business.get("website")                  # Get website URL
    validation = business.get("validation", {})           # Get Stage 2 validation result
    html       = validation.get("html_content", "")       # Get HTML captured during validation

    # Default audit result — used when website is not auditable
    audit = {
        "seo_score":            None,
        "performance_score":    None,
        "accessibility_score":  None,
        "best_practices_score": None,
        "mobile_friendly":      None,
        "issues_found":         [],
        "is_weak":              False,
        "html_data":            {},
        "should_audit":         False,  # Whether PSI was actually called
    }

    # Only audit if the website is actually live and not a blocked domain
    if not url or not validation.get("reachable") or validation.get("blocked"):
        audit["is_weak"] = not bool(url)   # No website at all = automatically weak
        return audit                       # Return early — nothing to audit

    audit["should_audit"] = True           # Mark that we ran a real audit
    print(f"[AUDITOR] Auditing: {url}")

    psi      = get_pagespeed_scores(url)   # Step 1: Call PageSpeed Insights API
    html_data = parse_html(html, url)      # Step 2: Parse the HTML we captured earlier
    issues   = detect_issues(psi, html_data, validation)  # Step 3: Build issues list
    weak     = is_weak_website(psi, validation) or len(issues) >= 3  # Weak if scores fail OR 3+ issues

    # Merge all results into the audit dict
    audit.update({
        "seo_score":            psi.get("seo_score"),
        "performance_score":    psi.get("performance_score"),
        "accessibility_score":  psi.get("accessibility_score"),
        "best_practices_score": psi.get("best_practices_score"),
        "mobile_friendly":      psi.get("mobile_friendly"),
        "issues_found":         issues,    # List of problem strings
        "is_weak":              weak,      # True = send to AI, False = skip AI
        "html_data":            html_data, # Parsed HTML data for contact + SEO fields
    })

    return audit   # Return complete audit result


# ── BATCH ASYNC AUDITING ──────────────────────────────────────

def _needs_psi(business: dict) -> bool:
    """
    Returns True if this business should get a full PSI + HTML audit.
    Mirrors the status routing in main.py so we pre-fetch the right ones.
    """
    v = business.get("validation", {})
    if not business.get("website"):          return False  # No website
    if not v.get("reachable"):               return False  # Site is down
    if v.get("blocked"):                     return False  # Social/directory domain
    return True                                            # Reachable — needs PSI


def _build_stub_audit(business: dict) -> dict:
    """
    Builds a stub audit dict for businesses that don't need PSI.
    Sets is_weak based on the situation so AI + scoring still work.
    """
    v       = business.get("validation", {})
    website = business.get("website")

    if not website:
        return {
            "is_weak": True,
            "issues_found": ["No website — zero online presence"],
            "should_audit": False,
            "html_data": {},
            "seo_score": None, "performance_score": None,
            "accessibility_score": None, "best_practices_score": None,
            "mobile_friendly": None,
        }

    if not v.get("reachable"):
        return {
            "is_weak": True,
            "issues_found": ["Website unreachable — server down or domain expired"],
            "should_audit": False,
            "html_data": {},
            "seo_score": None, "performance_score": None,
            "accessibility_score": None, "best_practices_score": None,
            "mobile_friendly": None,
        }

    if v.get("blocked"):
        return {
            "is_weak": True,
            "issues_found": ["No proper business website — listing points to a social/directory domain"],
            "should_audit": False,
            "html_data": {},
            "seo_score": None, "performance_score": None,
            "accessibility_score": None, "best_practices_score": None,
            "mobile_friendly": None,
        }

    # Fallback — shouldn't be reached
    return {
        "is_weak": False, "issues_found": [], "should_audit": False, "html_data": {},
        "seo_score": None, "performance_score": None,
        "accessibility_score": None, "best_practices_score": None,
        "mobile_friendly": None,
    }


async def _audit_all_async(businesses: list) -> None:
    """
    Concurrently fetches PageSpeed scores for all auditable businesses,
    then runs HTML parsing + issue detection sequentially (it's fast).

    FIX ⑦: PSI API calls are the bottleneck — each takes 5-30 seconds.
    asyncio.to_thread runs each blocking requests.get() call in a
    thread-pool worker so up to PSI_CONCURRENT_LIMIT calls overlap.
    HTML parsing with lxml is CPU-bound and fast, so it stays sequential.

    Results are attached directly to each business dict as business["audit"].
    """
    semaphore = asyncio.Semaphore(PSI_CONCURRENT_LIMIT)

    needs_psi = [b for b in businesses if _needs_psi(b)]
    print(f"[AUDITOR] {len(needs_psi)} sites need PSI — running {PSI_CONCURRENT_LIMIT} concurrently")

    async def _fetch_psi(biz: dict) -> None:
        """Fetches PSI scores for one business, rate-limited by semaphore."""
        async with semaphore:
            # asyncio.to_thread runs the blocking requests call in a thread
            # so the event loop (and all other PSI calls) stay unblocked.
            psi = await asyncio.to_thread(get_pagespeed_scores, biz["website"])
            biz["_psi"] = psi   # Temporarily stash result on the dict

    # Fire all PSI fetches concurrently, respecting the semaphore limit
    await asyncio.gather(*[_fetch_psi(b) for b in needs_psi])

    # After all PSI results are in, run HTML parsing + issue detection
    for b in businesses:
        if _needs_psi(b):
            psi        = b.pop("_psi", {})        # Grab the pre-fetched PSI result
            validation = b.get("validation", {})
            html       = validation.get("html_content", "")
            html_data  = parse_html(html, b.get("website", ""))
            issues     = detect_issues(psi, html_data, validation)
            weak       = is_weak_website(psi, validation) or len(issues) >= 3

            b["audit"] = {
                "seo_score":            psi.get("seo_score"),
                "performance_score":    psi.get("performance_score"),
                "accessibility_score":  psi.get("accessibility_score"),
                "best_practices_score": psi.get("best_practices_score"),
                "mobile_friendly":      psi.get("mobile_friendly"),
                "issues_found":         issues,
                "is_weak":              weak,
                "html_data":            html_data,
                "should_audit":         True,
            }
        else:
            b["audit"] = _build_stub_audit(b)


def run_audit_all(businesses: list) -> list:
    """
    Synchronous entry point for main.py.
    Pre-computes audits for all businesses in parallel and attaches
    the result as business["audit"] so process_one() can read it.

    Returns the same list with audit dicts attached in-place.
    """
    asyncio.run(_audit_all_async(businesses))
    return businesses
