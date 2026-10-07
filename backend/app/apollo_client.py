"""
Business Lead Generator — Apollo.io API Client
backend/app/apollo_client.py

Enriches company leads with:
- Direct verified email addresses (with status and score)
- Direct phone numbers
- Executive leadership (Owner, Founder, CEO, VP) when DM is missing
- Employee count, secondary industry, and company firmographics
"""

import asyncio
import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

try:
    from backend.app import config
except ImportError:
    import config

logger = logging.getLogger(__name__)

APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
DEFAULT_DM_TITLES = [
    "Owner",
    "Founder",
    "Co-Founder",
    "CEO",
    "Chief Executive Officer",
    "President",
    "Managing Director",
    "Partner",
    "Principal",
    "Director of Recruiting",
    "VP of Operations",
    "Vice President",
    "Director",
]


def extract_clean_domain(url_or_domain: str) -> str:
    """Extracts a clean hostname domain (e.g. 'company.com') from a website URL or string."""
    if not url_or_domain:
        return ""
    val = str(url_or_domain).strip().lower()
    if not val or val in ("none", "null", "undefined", "n/a"):
        return ""
    if "://" not in val:
        val = "http://" + val
    try:
        parsed = urlparse(val)
        netloc = parsed.netloc or parsed.path
        # Remove port and www
        netloc = netloc.split(":")[0].strip()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Remove paths/slashes if any remain
        netloc = netloc.split("/")[0]
        # Validate that it looks like a domain with a dot
        if "." in netloc and len(netloc) > 3:
            return netloc
    except Exception:
        pass
    return ""


def clean_phone_number(raw_phone: Any) -> str:
    """Sanitizes raw phone numbers."""
    if not raw_phone:
        return ""
    phone_str = str(raw_phone).strip()
    if not phone_str or phone_str.lower() in ("none", "null", "n/a"):
        return ""
    return phone_str


def is_country_compatible(expected: str | None, candidate: str | None) -> bool:
    """
    Checks if a candidate location/country from an API match is compatible with the expected country.
    Prevents false-positive American or foreign company matches from corrupting local records.
    """
    if not expected or not candidate:
        return True
    exp = expected.strip().lower()
    cand = candidate.strip().lower()

    if exp == cand:
        return True

    aliases = {
        "saudi arabia": ["saudi arabia", "saudi", "ksa", "sa", "riyadh", "jeddah", "dammam"],
        "united states": ["united states", "usa", "us", "u.s.", "u.s.a.", "united states of america", "illinois", "california", "texas", "new york", "florida"],
        "united arab emirates": ["united arab emirates", "uae", "u.a.e.", "dubai", "abu dhabi", "sharjah"],
        "united kingdom": ["united kingdom", "uk", "u.k.", "great britain", "england", "london", "scotland"],
        "qatar": ["qatar", "doha"],
        "kuwait": ["kuwait"],
        "bahrain": ["bahrain"],
        "oman": ["oman"],
        "egypt": ["egypt", "cairo"],
    }

    def match_key(text: str) -> str | None:
        words = set(re.findall(r"\b[a-zA-Z\.]+\b", text.lower()))
        for key, vals in aliases.items():
            for v in vals:
                if " " in v:
                    if v in text.lower():
                        return key
                else:
                    if v in words:
                        return key
        return None

    exp_key = match_key(exp)
    cand_key = match_key(cand)

    if exp_key and cand_key:
        return exp_key == cand_key

    return exp in cand or cand in exp


class ApolloClient:
    """Client for interacting with the Apollo.io REST API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = (api_key or getattr(config, "APOLLO_API_KEY", "") or "").strip()

    def is_configured(self) -> tuple[bool, str]:
        """Checks if the Apollo API key is configured with a valid format."""
        if not self.api_key or self.api_key.lower() in (
            "your_apollo_key_here",
            "your_key_here",
            "none",
        ):
            return False, "Apollo API Key is not configured. Please add it in Settings."

        if " " in self.api_key or "\n" in self.api_key or "\r" in self.api_key:
            return False, "Apollo API Key contains spaces or newlines. Please enter a valid Apollo API key."

        try:
            self.api_key.encode("ascii")
        except UnicodeEncodeError:
            return False, "Apollo API Key contains non-ASCII characters. Please enter a valid Apollo API key."

        if len(self.api_key) < 10:
            return False, "Apollo API Key is too short. Please enter a valid Apollo API key."

        return True, "Ready"

    async def test_connection(self) -> tuple[bool, str, dict[str, Any]]:
        """
        Tests connection to Apollo API using /auth/health.
        Returns (is_valid, message, details).
        """
        ok, msg = self.is_configured()
        if not ok:
            return False, msg, {}

        url = f"{APOLLO_BASE_URL}/auth/health"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._headers())
                if resp.status_code == 200:
                    data = resp.json()
                    is_logged_in = data.get("is_logged_in", False)
                    if is_logged_in:
                        return True, "Apollo connection verified successfully! API key is active and healthy.", data
                    else:
                        return False, "Apollo API reached, but key was rejected (is_logged_in: false). Please verify your key.", data
                elif resp.status_code == 401:
                    return False, "Apollo authentication failed (HTTP 401 Unauthorized). Invalid API key.", {}
                elif resp.status_code == 429:
                    return False, "Apollo rate limit exceeded (HTTP 429).", {}
                else:
                    return False, f"Apollo returned HTTP {resp.status_code}: {resp.text[:120]}", {}
        except UnicodeEncodeError:
            return False, "Apollo API Key contains non-ASCII characters.", {}
        except Exception as e:
            return False, f"Failed to connect to Apollo: {e}", {}

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
        }

    async def match_person(
        self,
        name: str = "",
        first_name: str = "",
        last_name: str = "",
        organization_name: str = "",
        domain: str = "",
        linkedin_url: str = "",
        person_id: str = "",
        reveal_personal_emails: bool = False,
    ) -> dict[str, Any] | None:
        """
        Calls POST /api/v1/people/match to find a matching person in Apollo.
        Consumes 1 Apollo credit only if an email is successfully revealed/returned.
        """
        if not self.api_key:
            return None

        payload: dict[str, Any] = {
            "reveal_personal_emails": reveal_personal_emails,
        }

        if person_id and person_id.strip():
            payload["id"] = person_id.strip()
        if linkedin_url and "linkedin.com" in linkedin_url.lower():
            payload["linkedin_url"] = linkedin_url.strip()
        if name and name.strip():
            payload["name"] = name.strip()
        if first_name and first_name.strip():
            payload["first_name"] = first_name.strip()
        if last_name and last_name.strip():
            payload["last_name"] = last_name.strip()
        if organization_name and organization_name.strip():
            payload["organization_name"] = organization_name.strip()
        if domain and domain.strip():
            payload["domain"] = domain.strip()

        # Need person_id OR (at least one identifying company attribute and one person attribute), or a linkedin URL
        has_id = bool(payload.get("id"))
        has_person = bool(payload.get("linkedin_url") or payload.get("name") or payload.get("first_name"))
        has_company = bool(payload.get("organization_name") or payload.get("domain") or payload.get("linkedin_url"))
        if not (has_id or (has_person and has_company)):
            return None

        url = f"{APOLLO_BASE_URL}/people/match"

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, headers=self._headers(), json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        person = data.get("person")
                        if person:
                            return person
                    elif resp.status_code == 429:
                        await asyncio.sleep(2.0 * (attempt + 1))
                        continue
                    elif resp.status_code == 404:
                        return None
                    else:
                        logger.warning(
                            "Apollo people/match returned HTTP %d: %s",
                            resp.status_code,
                            resp.text[:200],
                        )
            except Exception as e:
                logger.warning("Apollo people/match error: %s", e)
                if attempt == 0:
                    await asyncio.sleep(1.0)
        return None

    async def search_people(
        self,
        domain: str = "",
        organization_name: str = "",
        titles: list[str] | None = None,
        country: str = "",
        city: str = "",
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Searches for top executive contacts at a company using POST /api/v1/mixed_people/api_search.
        Does NOT consume email credits; returns candidate profile previews.
        Uses JSON request body with domain or company name matching.
        """
        if not self.api_key:
            return []

        search_titles = titles or DEFAULT_DM_TITLES
        url = f"{APOLLO_BASE_URL}/mixed_people/api_search"

        # Construct primary JSON payload
        body: dict[str, Any] = {
            "person_titles": search_titles,
            "page": 1,
            "per_page": limit,
        }

        if domain:
            body["q_organization_domains"] = domain
        elif organization_name:
            body["q_organization_name"] = organization_name
            if country:
                body["person_locations"] = [country]
        else:
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=self._headers(), json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    people = data.get("people") or []
                    if people:
                        return people

                    # Fallback: if domain search returned 0 candidates, try searching by organization name
                    if domain and organization_name:
                        body_fallback = {
                            "person_titles": search_titles,
                            "q_organization_name": organization_name,
                            "page": 1,
                            "per_page": limit,
                        }
                        if country:
                            body_fallback["person_locations"] = [country]
                        resp_fallback = await client.post(url, headers=self._headers(), json=body_fallback)
                        if resp_fallback.status_code == 200:
                            data_fb = resp_fallback.json()
                            return data_fb.get("people") or []
                    return []
                else:
                    logger.debug(
                        "Apollo mixed_people/api_search returned HTTP %d: %s",
                        resp.status_code,
                        resp.text[:200],
                    )
        except Exception as e:
            logger.warning("Apollo search_people error: %s", e)
        return []

    async def enrich_organization(
        self,
        domain: str = "",
        organization_name: str = "",
    ) -> dict[str, Any] | None:
        """
        Calls GET /api/v1/organizations/enrich to get company firmographics.
        Does not consume contact email credits.
        """
        if not self.api_key:
            return None

        clean_dom = extract_clean_domain(domain)
        if not clean_dom and not organization_name:
            return None

        url = f"{APOLLO_BASE_URL}/organizations/enrich"
        params: dict[str, str] = {}
        if clean_dom:
            params["domain"] = clean_dom
        elif organization_name:
            params["name"] = organization_name.strip()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self._headers(), params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("organization")
                else:
                    logger.debug(
                        "Apollo organizations/enrich returned HTTP %d: %s",
                        resp.status_code,
                        resp.text[:200],
                    )
        except Exception as e:
            logger.warning("Apollo enrich_organization error: %s", e)
        return None

    async def enrich_lead(
        self,
        record: dict[str, Any],
        enrich_firmographics: bool = False,
    ) -> dict[str, Any]:
        """
        High-level intelligent lead enrichment pipeline for a single record.
        Inspects existing record, discovers decision maker candidates, and reveals verified contacts.
        Does NOT burn credits on standalone organization lookups unless enrich_firmographics is True.
        Returns a dict of new non-empty field values.
        """
        new_fields: dict[str, Any] = {}

        company_name = (record.get("Company_Name") or "").strip()
        website_url = (record.get("Website_URL") or "").strip()
        domain = extract_clean_domain(website_url)
        target_country = (record.get("Country") or "").strip()
        target_city = (record.get("City") or "").strip()

        dm_name = (record.get("DM_Full_Name") or "").strip()
        dm_title = (record.get("DM_Title") or "").strip()
        dm_linkedin = (record.get("DM_LinkedIn_URL") or "").strip()
        dm_email = (record.get("DM_Direct_Email") or "").strip()
        dm_phone = (record.get("DM_Direct_Phone") or "").strip()

        # Step 0: If record ALREADY has verified DM email, do NOT burn an Apollo credit
        if dm_email and "@" in dm_email:
            logger.info("Record %s already has DM_Direct_Email (%s). Preserving existing email and skipping Apollo credit consumption.", record.get("Record_ID"), dm_email)
            # Only enrich firmographics if missing (0 credits)
            if not record.get("Employee_Count") or not record.get("Secondary_Industry"):
                org_info = await self.enrich_organization(domain=domain, organization_name=company_name)
                if org_info:
                    org_c = org_info.get("country") or ""
                    if not target_country or not org_c or is_country_compatible(target_country, org_c):
                        emp_count = org_info.get("estimated_num_employees")
                        if emp_count and not record.get("Employee_Count"):
                            new_fields["Employee_Count"] = emp_count
                        org_sub = org_info.get("industry")
                        if org_sub and not record.get("Secondary_Industry"):
                            new_fields["Secondary_Industry"] = str(org_sub).strip()
                        org_type = org_info.get("company_type")
                        if org_type and not record.get("Company_Type"):
                            new_fields["Company_Type"] = str(org_type).strip()
            return new_fields

        matched_person: dict[str, Any] | None = None

        # Step 1: If we have DM Name or LinkedIn, run people/match directly
        if dm_name or (dm_linkedin and "linkedin.com" in dm_linkedin):
            # Split name into first and last if needed
            name_parts = dm_name.split() if dm_name else []
            first_n = name_parts[0] if name_parts else ""
            last_n = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            matched_person = await self.match_person(
                name=dm_name,
                first_name=first_n,
                last_name=last_n,
                organization_name=company_name,
                domain=domain,
                linkedin_url=dm_linkedin,
            )

        # Step 2: If DM Name is empty, search for top executive via mixed_people/api_search
        if not matched_person and not dm_name and (domain or company_name):
            candidates = await self.search_people(
                domain=domain,
                organization_name=company_name,
                country=target_country,
                city=target_city,
                limit=3,
            )
            # If search was name-only, filter out candidate profiles with mismatched countries
            if candidates and not domain and target_country:
                candidates = [
                    c for c in candidates
                    if is_country_compatible(target_country, c.get("country") or (c.get("organization") or {}).get("country"))
                ]

            if candidates:
                top_cand = candidates[0]
                cand_id = top_cand.get("id")
                cand_name = top_cand.get("name") or f"{top_cand.get('first_name', '')} {top_cand.get('last_name', '')}".strip()
                cand_linkedin = top_cand.get("linkedin_url") or ""

                if cand_id or cand_name or cand_linkedin:
                    # Match candidate to reveal full verified email & direct phone
                    matched_person = await self.match_person(
                        person_id=cand_id or "",
                        name=cand_name,
                        organization_name=company_name,
                        domain=domain,
                        linkedin_url=cand_linkedin,
                    )
                    if not matched_person:
                        # Fallback to the search preview info
                        matched_person = top_cand

        # Discard matched person if location incompatible and search was name-only
        if matched_person and not domain and target_country:
            m_country = matched_person.get("country") or (matched_person.get("organization") or {}).get("country") or ""
            if not is_country_compatible(target_country, m_country):
                logger.info(
                    "Apollo matched person country '%s' incompatible with expected '%s'. Discarding false positive.",
                    m_country,
                    target_country,
                )
                matched_person = None

        # Step 3: Extract fields from matched person
        if matched_person:
            # Person Identity
            p_name = matched_person.get("name") or f"{matched_person.get('first_name', '')} {matched_person.get('last_name', '')}".strip()
            if p_name and not dm_name:
                new_fields["DM_Full_Name"] = p_name

            p_title = (matched_person.get("title") or "").strip()
            if p_title and not dm_title:
                new_fields["DM_Title"] = p_title
                new_fields["DM_Authority_Level"] = config.classify_dm_authority(p_title)

            p_li = (matched_person.get("linkedin_url") or "").strip()
            if p_li and not dm_linkedin:
                new_fields["DM_LinkedIn_URL"] = p_li

            # Direct Verified Email
            p_email = (matched_person.get("email") or "").strip().lower()
            if p_email and "@" in p_email and not dm_email:
                new_fields["DM_Direct_Email"] = p_email
                email_status = (matched_person.get("email_status") or "verified").lower()
                new_fields["DM_Email_Status"] = email_status.capitalize()
                
                # Derive email confidence score
                if email_status == "verified":
                    new_fields["DM_Email_Score"] = 95
                elif email_status == "extrapolated":
                    new_fields["DM_Email_Score"] = 75
                else:
                    new_fields["DM_Email_Score"] = 60

            # Direct Phone
            if not dm_phone:
                # Check direct phone numbers list or sanitized_phone
                p_phones = matched_person.get("phone_numbers") or []
                phone_candidate = ""
                for ph in p_phones:
                    if isinstance(ph, dict):
                        p_val = ph.get("sanitized_number") or ph.get("raw_number")
                        p_type = (ph.get("type") or "").lower()
                        if p_val:
                            phone_candidate = p_val
                            if "mobile" in p_type or "direct" in p_type:
                                break
                    elif isinstance(ph, str) and ph.strip():
                        phone_candidate = ph.strip()
                        break
                
                if not phone_candidate:
                    phone_candidate = matched_person.get("sanitized_phone") or matched_person.get("phone_number") or ""
                
                if phone_candidate:
                    new_fields["DM_Direct_Phone"] = clean_phone_number(phone_candidate)

            # Organization firmographics embedded in person match (FREE, 0 extra credits)
            p_org = matched_person.get("organization") or {}
            p_org_country = p_org.get("country") or ""
            org_country_ok = not target_country or not p_org_country or is_country_compatible(target_country, p_org_country)
            if isinstance(p_org, dict) and p_org and org_country_ok:
                emp_count = p_org.get("estimated_num_employees")
                if emp_count and not record.get("Employee_Count"):
                    new_fields["Employee_Count"] = emp_count

                org_sub = p_org.get("industry")
                if org_sub and not record.get("Secondary_Industry"):
                    new_fields["Secondary_Industry"] = str(org_sub).strip()

                org_web = p_org.get("website_url")
                if org_web and not website_url:
                    new_fields["Website_URL"] = org_web.strip()
                    new_fields["Has_Website"] = "Yes"

                org_li = p_org.get("linkedin_url")
                if org_li and not record.get("Company_LinkedIn"):
                    new_fields["Company_LinkedIn"] = org_li.strip()

                org_ph = p_org.get("phone")
                if org_ph and not record.get("Primary_Phone") and "Primary_Phone" not in new_fields:
                    new_fields["Primary_Phone"] = clean_phone_number(org_ph)

        # Step 4: Standalone organization enrichment (only if explicitly enabled to prevent unwanted credit usage)
        if enrich_firmographics:
            has_emp = bool(record.get("Employee_Count") or new_fields.get("Employee_Count"))
            has_ind = bool(record.get("Secondary_Industry") or new_fields.get("Secondary_Industry"))
            if (not has_emp or not has_ind or not website_url) and (domain or company_name):
                org = await self.enrich_organization(domain=domain, organization_name=company_name)
                if org:
                    org_country = org.get("country") or ""
                    org_country_ok = not target_country or not org_country or is_country_compatible(target_country, org_country)
                    if org_country_ok:
                        emp_count = org.get("estimated_num_employees")
                        if emp_count and not record.get("Employee_Count") and "Employee_Count" not in new_fields:
                            new_fields["Employee_Count"] = emp_count

                        org_ind = org.get("industry")
                        if org_ind and not record.get("Secondary_Industry") and "Secondary_Industry" not in new_fields:
                            new_fields["Secondary_Industry"] = str(org_ind).strip()

                        org_web = org.get("website_url")
                        if org_web and not website_url and "Website_URL" not in new_fields:
                            new_fields["Website_URL"] = org_web.strip()
                            new_fields["Has_Website"] = "Yes"

                        org_li = org.get("linkedin_url")
                        if org_li and not record.get("Company_LinkedIn") and "Company_LinkedIn" not in new_fields:
                            new_fields["Company_LinkedIn"] = org_li.strip()

                        # Primary Phone fallback if missing
                        org_phone = org.get("phone")
                        if org_phone and not record.get("Primary_Phone") and "Primary_Phone" not in new_fields:
                            new_fields["Primary_Phone"] = clean_phone_number(org_phone)

        return new_fields
