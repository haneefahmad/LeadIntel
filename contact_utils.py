import re
import socket
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse

import requests

from config import HUNTER_API_KEY, SAUDI_PHONE_PATTERN   # FIX ⑨: single source of truth


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# FIX ⑨: Use the unified SAUDI_PHONE_PATTERN from config.py instead of
# maintaining a duplicate regex here.  Previously this file and validator.py
# each had their own pattern that could silently diverge over time.
PHONE_RE = re.compile(SAUDI_PHONE_PATTERN)
HUNTER_EMAIL_VERIFIER_URL = "https://api.hunter.io/v2/email-verifier"

JUNK_EMAIL_PARTS = (
    "example.",
    "domain.",
    "test@",
    "noreply@",
    "no-reply@",
    "donotreply@",
    "do-not-reply@",
)

JUNK_EMAIL_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".css",
    ".js",
)

EMAIL_PRIORITY = (
    "sales@",
    "business@",
    "info@",
    "contact@",
    "hello@",
    "support@",
    "admin@",
)


def clean_email(email: str) -> str:
    email = unquote((email or "").strip().lower())
    email = email.replace("mailto:", "").split("?")[0].strip()
    return email.strip(".,;:()[]{}<>\"'")


def is_usable_email(email: str) -> bool:
    email = clean_email(email)
    if not EMAIL_RE.fullmatch(email):
        return False
    if any(part in email for part in JUNK_EMAIL_PARTS):
        return False
    if any(ext in email for ext in JUNK_EMAIL_EXTENSIONS):
        return False
    return True


def dedupe_emails(emails: list) -> list:
    seen = set()
    cleaned = []
    for email in emails:
        email = clean_email(email)
        if email and email not in seen and is_usable_email(email):
            seen.add(email)
            cleaned.append(email)
    return cleaned


def email_domain_has_mail(domain: str) -> tuple[str, str]:
    """
    Best-effort deliverability check.
    valid_mx requires dnspython. likely_valid_domain is a weaker socket fallback.
    This does not guarantee no bounce; that needs a verifier API.
    """
    if not domain:
        return "invalid", "none"

    try:
        import dns.resolver

        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        if answers:
            return "valid_mx", "high"
    except ImportError:
        pass
    except Exception:
        return "invalid_domain", "low"

    try:
        socket.getaddrinfo(domain, 80)
        return "likely_valid_domain", "medium"
    except Exception:
        return "invalid_domain", "low"


def verify_email_with_hunter(email: str) -> dict:
    """Verifies an email through Hunter when HUNTER_API_KEY is configured."""
    if not email:
        return {
            "provider": "none",
            "status": "not_found",
            "confidence": "none",
            "score": None,
            "checked_at": "",
            "raw": "",
        }

    if not HUNTER_API_KEY:
        return {
            "provider": "dns",
            "status": "",
            "confidence": "",
            "score": None,
            "checked_at": "",
            "raw": "",
        }

    try:
        response = requests.get(
            HUNTER_EMAIL_VERIFIER_URL,
            params={"email": email, "api_key": HUNTER_API_KEY},
            timeout=15,
        )
        checked_at = datetime.now().isoformat(timespec="seconds")
        if response.status_code != 200:
            return {
                "provider": "hunter",
                "status": f"api_error_{response.status_code}",
                "confidence": "unknown",
                "score": None,
                "checked_at": checked_at,
                "raw": response.text[:1000],
            }

        data = response.json().get("data", {})
        status = data.get("status") or data.get("result") or "unknown"
        score = data.get("score")
        confidence = "high" if isinstance(score, (int, float)) and score >= 80 else "medium"
        if status not in ("valid", "accept_all"):
            confidence = "low" if status in ("invalid", "disposable") else "unknown"

        return {
            "provider": "hunter",
            "status": status,
            "confidence": confidence,
            "score": score,
            "checked_at": checked_at,
            "raw": response.text[:4000],
        }
    except Exception as e:
        return {
            "provider": "hunter",
            "status": f"verification_error_{type(e).__name__}",
            "confidence": "unknown",
            "score": None,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "raw": "",
        }


def choose_primary_email(emails: list, source_url: str = "") -> dict:
    emails = dedupe_emails(emails)
    if not emails:
        return {
            "primary_email": "",
            "email_status": "not_found",
            "email_confidence": "none",
            "email_source_url": "",
            "email_verification_provider": "none",
            "email_checked_at": "",
            "hunter_status": "",
            "hunter_score": None,
            "hunter_result": "",
        }

    ranked = sorted(
        emails,
        key=lambda e: next(
            (idx for idx, prefix in enumerate(EMAIL_PRIORITY) if e.startswith(prefix)),
            len(EMAIL_PRIORITY),
        ),
    )
    primary = ranked[0]
    domain = primary.split("@", 1)[1]
    status, confidence = email_domain_has_mail(domain)
    hunter = verify_email_with_hunter(primary)
    if hunter["provider"] == "hunter":
        status = hunter["status"]
        confidence = hunter["confidence"]

    return {
        "primary_email": primary,
        "email_status": status,
        "email_confidence": confidence,
        "email_source_url": source_url,
        "email_verification_provider": hunter["provider"],
        "email_checked_at": hunter["checked_at"],
        "hunter_status": hunter["status"] if hunter["provider"] == "hunter" else "",
        "hunter_score": hunter["score"],
        "hunter_result": hunter["raw"],
    }


def normalize_phone(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    digits = re.sub(r"\D+", "", raw)
    if not digits:
        return ""
    if digits.startswith("00966"):
        digits = digits[2:]
    if digits.startswith("966"):
        return "+" + digits
    if digits.startswith("0") and len(digits) >= 10:
        return "+966" + digits[1:]
    if len(digits) == 9:
        return "+966" + digits
    return "+" + digits if raw.startswith("+") else digits


def classify_phone(phone: str) -> str:
    normalized = normalize_phone(phone)
    digits = re.sub(r"\D+", "", normalized)
    if digits.startswith("9665") and len(digits) == 12:
        return "mobile"
    # Saudi landline area codes after +966:
    #   11 = Riyadh       12 = Mecca / Jeddah / Taif
    #   13 = Eastern      14 = Al-Madinah / Qassim
    #   15 = Special/military network
    #   16 = Hail / Tabuk / Northern borders
    #   17 = Asir / Jizan / Najran
    if any(digits.startswith(prefix) for prefix in (
        "96611", "96612", "96613", "96614", "96615", "96616", "96617"
    )):
        return "landline"
    return "phone"


def extract_phone_numbers(text: str) -> list:
    if not text:
        return []
    return list({normalize_phone(match) for match in PHONE_RE.findall(text) if normalize_phone(match)})


def extract_whatsapp_number(url: str) -> str:
    parsed = urlparse(url or "")
    combined = url or ""
    if "api.whatsapp.com" in parsed.netloc:
        combined += " " + " ".join(parse_qs(parsed.query).get("phone", []))
    numbers = extract_phone_numbers(combined)
    return numbers[0] if numbers else ""


def build_contact_fields(business: dict, html_data: dict, phones: list) -> dict:
    whatsapp_numbers = list(html_data.get("whatsapp_numbers", []))
    all_phones = list(phones or [])
    if business.get("phone"):
        all_phones.append(business.get("phone"))

    normalized = []
    for phone in all_phones:
        phone = normalize_phone(phone)
        if phone and phone not in normalized:
            normalized.append(phone)

    mobile_numbers = [p for p in normalized if classify_phone(p) == "mobile"]
    landlines = [p for p in normalized if classify_phone(p) == "landline"]

    whatsapp_numbers = [
        normalize_phone(p) for p in whatsapp_numbers if normalize_phone(p)
    ]
    whatsapp_numbers = list(dict.fromkeys(whatsapp_numbers))

    email_result = choose_primary_email(
        html_data.get("emails", []),
        html_data.get("contact_page_url") or business.get("website") or "",
    )

    return {
        "contact_phone": mobile_numbers[0] if mobile_numbers else (normalized[0] if normalized else ""),
        "landline_number": landlines[0] if landlines else "",
        "whatsapp_number": whatsapp_numbers[0] if whatsapp_numbers else (mobile_numbers[0] if mobile_numbers else ""),
        "primary_email": email_result["primary_email"],
        "email_status": email_result["email_status"],
        "email_confidence": email_result["email_confidence"],
        "email_source_url": email_result["email_source_url"],
        "email_verification_provider": email_result["email_verification_provider"],
        "email_checked_at": email_result["email_checked_at"],
        "hunter_status": email_result["hunter_status"],
        "hunter_score": email_result["hunter_score"],
        "hunter_result": email_result["hunter_result"],
        "linkedin_company_url": html_data.get("linkedin_company_url", ""),
        "decision_maker_linkedin": html_data.get("decision_maker_linkedin", ""),
    }
