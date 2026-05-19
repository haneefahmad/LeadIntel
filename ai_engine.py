# ============================================================
# ai_engine.py — Stage 4: AI analysis + sales pitch generation
# Uses Groq API with llama-3.1-8b-instant
# Only runs for businesses that FAILED the audit quality gate
# ============================================================

import json                                    # For parsing JSON responses from Groq
from groq import Groq                          # Groq official SDK — pip install groq
from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    SEO_SCORE_THRESHOLD,
    PERFORMANCE_THRESHOLD,
    ACCESSIBILITY_THRESHOLD,
    BEST_PRACTICES_THRESHOLD,
)

# ── GROQ CLIENT (CREATED ONCE) ────────────────────────────────
# Creating the client once at module load is more efficient than creating per call

client = Groq(api_key=GROQ_API_KEY)           # Initialize Groq client with your API key

# ── PROMPT BUILDERS ───────────────────────────────────────────

def build_weak_site_prompt(business: dict, audit: dict) -> str:
    """
    Builds a detailed AI analysis prompt for businesses with a weak website.
    Now asks for:
      - Root cause explanation for EACH issue (why it's a problem)
      - Specific actionable fix for EACH issue (exactly what to do)
      - Prioritised improvement roadmap
      - Concrete outreach messages
    """
    name       = business.get("business_name", "Unknown")
    category   = business.get("category", "Unknown")
    product_lines = business.get("product_lines", "SSL, ERP, Custom Software")
    source_query = business.get("source_query", "")
    city       = business.get("city", "Saudi Arabia")
    website    = business.get("website", "None")
    validation = business.get("validation", {})
    html_data  = audit.get("html_data", {})
    issues     = audit.get("issues_found", [])

    # Format issues as a numbered list for clarity in the prompt
    issues_text = "\n".join(f"{i+1}. {issue}" for i, issue in enumerate(issues)) \
                  if issues else "None automatically detected"

    # Format HTML data as clear facts
    title_text   = html_data.get("title_text", "None found")[:120]
    meta_length  = html_data.get("meta_desc_length", 0)
    has_title    = "Yes" if html_data.get("has_title") else "No — MISSING"
    has_meta     = f"Yes ({meta_length} chars)" if html_data.get("has_meta_desc") else "No — MISSING"
    has_https    = "Yes" if validation.get("https") else "No — NOT SECURE"
    has_ssl      = "Yes" if validation.get("ssl_valid") else "No — INVALID/EXPIRED"
    is_mobile    = "Yes" if audit.get("mobile_friendly") else "No — FAILS MOBILE TEST"

    return f"""You are a senior web development and digital marketing consultant. You are writing a detailed technical audit report for a Saudi Arabian business website, on behalf of a digital agency that wants to offer their services.

Your report must be specific, professional, and actionable. Generic or vague answers are not acceptable.

═══════════════════════════════════════════
BUSINESS DETAILS
═══════════════════════════════════════════
Business Name : {name}
Category      : {category}
EIT Products  : {product_lines}
Source Query  : {source_query}
City          : {city}
Website       : {website}

═══════════════════════════════════════════
TECHNICAL AUDIT SCORES (Google PageSpeed)
═══════════════════════════════════════════
SEO Score          : {audit.get("seo_score", "N/A")} / 100
Performance Score  : {audit.get("performance_score", "N/A")} / 100
Accessibility Score: {audit.get("accessibility_score", "N/A")} / 100
Best Practices     : {audit.get("best_practices_score", "N/A")} / 100
Mobile Friendly    : {is_mobile}
HTTPS Secure       : {has_https}
SSL Certificate    : {has_ssl}

═══════════════════════════════════════════
HTML STRUCTURE AUDIT
═══════════════════════════════════════════
Title Tag          : {has_title}
Title Content      : {title_text}
Meta Description   : {has_meta}
═══════════════════════════════════════════
DETECTED ISSUES
═══════════════════════════════════════════
{issues_text}

═══════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════
Analyze all the data above and produce a detailed audit report.

For EACH issue detected, you must explain:
  a) WHY it is a problem — the real-world impact on the business
  b) EXACTLY how to fix it — specific technical steps, not general advice

Example of a BAD answer: "Improve SEO"
Example of a GOOD answer: "The performance score is 38/100, which means mobile visitors may leave before the page loads. Fix: compress images, remove unused scripts, enable caching, and rebuild the landing page so key content loads in under 3 seconds."

Respond ONLY with a valid raw JSON object. No markdown, no code blocks, no extra text:
{{
  "uiux_score": <integer 1-10, where 1=completely broken, 10=excellent>,
  "branding_score": <integer 1-10>,
  "professionalism_score": <integer 1-10>,
  "modernity_score": <integer 1-10>,

  "overall_weakness_summary": "<3-4 sentences summarising the main problems and their business impact. Be specific — mention actual scores and concrete business risk.>",

  "detailed_issues": [
    {{
      "issue": "<name of the issue>",
      "root_cause": "<why this is happening technically>",
      "business_impact": "<what this costs the business in real terms — lost enquiries, weaker buyer trust, missed tenders, lost ranking, or operational risk. Be concrete and credible.>",
      "exact_fix": "<specific step-by-step instructions to fix this issue>"
    }}
  ],

  "improvement_roadmap": [
    "<Step 1: highest priority fix — do this first and why>",
    "<Step 2: second priority fix>",
    "<Step 3: third priority fix>",
    "<Step 4: fourth priority fix if applicable>"
  ],

  "recommended_services": [
    "<specific service 1 — e.g. 'SEO audit and on-page optimisation'>",
    "<specific service 2>",
    "<specific service 3>"
  ],

  "redesign_priority": "<low|medium|high|urgent>",
  "redesign_reason": "<one sentence explaining why this priority level was chosen>",

  "outreach_message": "<professional 4-5 sentence risk-based agency email. Open with a specific audit finding, then create urgency by explaining the credible commercial risk of doing nothing: lost enquiries, weak trust, tender/client perception, security risk, or slow mobile conversion. Pitch the relevant EIT products ({product_lines}) as the fix. The tone must feel serious and urgent, but do not lie, exaggerate, threaten, or invent losses. Close with a direct call to action for a quick audit/fix plan. Do not use generic openers like 'I hope this email finds you well'.>",

  "whatsapp_message": "<urgent but professional WhatsApp message under 100 words in English. Reference {name}. Mention one specific risk from the audit and the likely business consequence if ignored. Offer a quick free audit/fix plan. Do not use fake claims or threats.>"
}}"""


def build_no_website_prompt(business: dict) -> str:
    """
    Builds a detailed prompt for businesses with absolutely NO website.
    Asks for specific pitch explaining what they are losing and exactly what to build.
    """
    name     = business.get("business_name", "Unknown")
    category = business.get("category", "Unknown")
    product_lines = business.get("product_lines", "SSL, ERP, Custom Software")
    source_query = business.get("source_query", "")
    city     = business.get("city", "Saudi Arabia")
    phone    = business.get("phone", "Not listed")
    rating   = business.get("rating", "Unknown")
    reviews  = business.get("review_count", 0)

    return f"""You are a senior web development consultant writing a lead report for a digital agency.

This Saudi Arabian business has NO website at all — a critical missed opportunity in 2026.

═══════════════════════════════════════════
BUSINESS DETAILS
═══════════════════════════════════════════
Business Name : {name}
Category      : {category}
EIT Products  : {product_lines}
Source Query  : {source_query}
City          : {city}
Phone         : {phone}
Google Rating : {rating} stars ({reviews} reviews)

═══════════════════════════════════════════
SITUATION
═══════════════════════════════════════════
This business exists on Google Maps but has zero web presence.
In Saudi Arabia where mobile internet usage exceeds 95%, this means:
- Invisible to Google Search — customers searching online cannot find them
- No way to showcase services, menus, pricing, or location online
- Competitors with websites are capturing all digital customers
- No ability to run Google Ads, Instagram link-in-bio, or WhatsApp Business links
- Missing from all online directories that require a website

═══════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════
Write a specific, compelling outreach report that explains exactly what this
business is losing and exactly what a professional website would give them.
Be specific to their category ({category}) — mention real examples relevant to that business type.

Respond ONLY with valid raw JSON. No markdown, no code blocks, no extra text:
{{
  "uiux_score": 0,
  "branding_score": 0,
  "professionalism_score": 0,
  "modernity_score": 0,

  "overall_weakness_summary": "<3-4 precise sentences specific to a {category} in {city} with no website. Explain the credible commercial risk: invisible in search, lower trust, weaker tender/client perception, and lost enquiry paths.>",

  "detailed_issues": [
    {{
      "issue": "No website",
      "root_cause": "Business has not established any web presence",
      "business_impact": "<specific impact for a {category}: buyers, procurement teams, or customers cannot verify services, past work, credibility, or contact options from search>",
      "exact_fix": "Build a professional website with: home page, services/menu page, location and contact page, photo gallery, and WhatsApp booking button"
    }},
    {{
      "issue": "Invisible to Google Search",
      "root_cause": "No website means no pages for Google to index",
      "business_impact": "<specific lost opportunity for this category>",
      "exact_fix": "<specific SEO setup steps for a {category}>"
    }},
    {{
      "issue": "No digital customer conversion path",
      "root_cause": "Without a website, there is nowhere to send customers from social media, WhatsApp, or paid ads",
      "business_impact": "<how this limits growth for this specific business type>",
      "exact_fix": "<specific recommendation for this category>"
    }}
  ],

  "improvement_roadmap": [
    "Step 1: Build a professional {category} website with mobile-first design, Arabic and English content, WhatsApp integration, and Google Maps embed",
    "Step 2: Set up Google Business Profile fully with photos, hours, and website link to appear in local searches",
    "Step 3: Implement on-page SEO targeting '{category} in {city}' and nearby district keywords",
    "Step 4: Connect website to Instagram and WhatsApp Business for a complete digital presence"
  ],

  "recommended_services": [
    "Website design and development (Arabic + English)",
    "Google Business Profile setup and optimisation",
    "Local SEO targeting {city} searches",
    "WhatsApp Business integration and automation"
  ],

  "redesign_priority": "urgent",
  "redesign_reason": "Business has zero online presence — every day without a website is lost customers and lost revenue.",

  "outreach_message": "<professional 4-5 sentence risk-based email specific to {name}. Open by saying you found them on Google Maps but could not verify a proper website. Create urgency by explaining the credible risk: buyers may choose competitors they can verify online, procurement teams may skip vendors without a digital profile, and enquiries have no conversion path. Pitch the relevant EIT products ({product_lines}) as the fix. End with a direct call to action for a quick audit/fix plan. Do not lie, threaten, or invent numbers.>",

  "whatsapp_message": "<urgent but professional WhatsApp message under 100 words. Address {name}. Mention you saw their Google Maps listing but could not verify a proper website. State the risk that serious buyers may move to competitors with clearer online proof. Offer a quick free audit/fix plan.>"
}}"""

# ── GROQ API CALL ─────────────────────────────────────────────

def call_groq(prompt: str) -> dict:
    """
    Sends a prompt to Groq and returns the parsed JSON response as a Python dict.
    Returns an empty dict if the API call fails or returns invalid JSON.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,        # llama-3.1-8b-instant — fastest Groq model
            messages=[
                {
                    "role":    "system",
                    "content": "You are a web quality analysis expert. Always respond with valid JSON only. Never include explanations, markdown, or code blocks.",
                    # System message sets the AI's role and forces clean JSON output
                },
                {
                    "role":    "user",
                    "content": prompt   # The analysis or pitch prompt we built above
                }
            ],
            temperature=0.3,         # Low temperature = consistent, factual, not creative
            max_tokens=2000,         # Increased — new prompts return detailed root causes and roadmaps
        )

        content = response.choices[0].message.content.strip()
        # Navigate the Groq response: choices[0] → message → content (the text)

        # Clean up in case the model wrapped JSON in markdown code fences
        if content.startswith("```"):
            parts   = content.split("```")   # Split on triple-backtick
            content = parts[1] if len(parts) > 1 else content   # Take content between fences
            if content.startswith("json"):
                content = content[4:]        # Remove "json" language tag after opening fence

        content = content.strip()            # Remove any remaining whitespace

        return json.loads(content)           # Parse JSON string into Python dict — raises on error

    except json.JSONDecodeError as e:
        print(f"[AI] JSON parse failed: {e}")   # Groq returned text that wasn't valid JSON
        return {}                               # Return empty dict — safe fallback
    except Exception as e:
        print(f"[AI] Groq API error: {e}")      # Network error, rate limit, etc.
        return {}                               # Return empty dict


def build_bad_reason(business: dict, audit: dict, ai_result: dict) -> str:
    """Creates a short database-friendly explanation of why this is an actionable lead."""
    category = business.get("category", "business")
    product_lines = business.get("product_lines", "SSL, ERP, Custom Software")
    city = business.get("city", "Saudi Arabia")
    issues = audit.get("issues_found", [])
    summary = ai_result.get("overall_weakness_summary", "")

    if summary:
        return summary

    if issues:
        return (
            f"This {category} in {city} is an actionable lead for {product_lines} "
            f"because it has these digital problems: {'; '.join(issues)}."
        )

    return (
        f"This {category} in {city} is an actionable lead because its website or "
        "online presence failed the quality checks."
    )


def build_industry_sales_pitch(business: dict, audit: dict, ai_result: dict) -> str:
    """Returns the AI pitch, or a category-specific fallback if AI output is unavailable."""
    pitch = ai_result.get("outreach_message", "")
    if pitch:
        return pitch

    name = business.get("business_name", "your business")
    category = business.get("category", "business")
    product_lines = business.get("product_lines", "SSL, ERP, Custom Software")
    city = business.get("city", "Saudi Arabia")
    issues = audit.get("issues_found", [])
    issue_text = issues[0] if issues else "your online presence is missing key trust and conversion signals"

    return (
        f"We found {name} while reviewing {category} businesses in {city}. "
        f"One risk stood out immediately: {issue_text}. When buyers or procurement teams "
        "cannot quickly verify a company online, they usually move to competitors with clearer "
        f"digital proof and faster enquiry paths. EIT can position {product_lines} for this "
        f"{category.lower()} business through secure browsing, mobile-first pages, local SEO, "
        "workflow automation, and WhatsApp/contact conversion before more opportunities leak away."
    )

# ── MAIN ANALYSIS FUNCTION ────────────────────────────────────

def analyze_business(business: dict, audit: dict) -> dict:
    """
    Runs AI analysis on a single business.
    Selects the right prompt based on whether the business has a website.
    Returns a dict of AI results ready to be saved in the database.
    """
    has_website  = bool(business.get("website"))   # Does this business have a website URL?
    was_audited  = audit.get("should_audit", False)  # Did we successfully run PSI on it?

    print(f"[AI] Analyzing: {business.get('business_name', '?')}")

    # Choose prompt based on situation
    if has_website and was_audited:
        prompt = build_weak_site_prompt(business, audit)   # Weak website analysis prompt
    else:
        prompt = build_no_website_prompt(business)         # No website pitch prompt

    ai_result = call_groq(prompt)   # Send to Groq — waits for response

    if not ai_result:               # If Groq failed or returned empty
        fallback = {}
        return {                    # Return safe default values so pipeline continues
            "ai_uiux_score":   0,
            "ai_analysis":     "{}",
            "bad_reason":      build_bad_reason(business, audit, fallback),
            "industry_sales_pitch": build_industry_sales_pitch(business, audit, fallback),
            "ai_sales_pitch":  "Analysis unavailable",
            "ai_whatsapp_msg": "Analysis unavailable",
        }

    # Package the AI results for database storage
    # New fields: detailed_issues (root cause + exact fix per issue)
    #             improvement_roadmap (prioritised steps)
    #             redesign_reason (explains the priority level)
    return {
        "ai_uiux_score": ai_result.get("uiux_score", 0),   # UI/UX score 0-10

        "ai_analysis": json.dumps({
            "branding":             ai_result.get("branding_score"),
            "professionalism":      ai_result.get("professionalism_score"),
            "modernity":            ai_result.get("modernity_score"),
            "summary":              ai_result.get("overall_weakness_summary"),
            "detailed_issues":      ai_result.get("detailed_issues", []),
            # Each item has: issue, root_cause, business_impact, exact_fix
            "improvement_roadmap":  ai_result.get("improvement_roadmap", []),
            # Ordered list of specific steps to fix the site
            "recommended_services": ai_result.get("recommended_services", []),
            "redesign_priority":    ai_result.get("redesign_priority"),
            "redesign_reason":      ai_result.get("redesign_reason"),
        }),

        "bad_reason":           build_bad_reason(business, audit, ai_result),
        "industry_sales_pitch":  build_industry_sales_pitch(business, audit, ai_result),
        "ai_sales_pitch":  ai_result.get("outreach_message", ""),   # Professional email text
        "ai_whatsapp_msg": ai_result.get("whatsapp_message", ""),   # WhatsApp message text
    }

# ── LEAD SCORE CALCULATOR ─────────────────────────────────────

def calculate_lead_score(business: dict, audit: dict, ai_result: dict) -> float:
    """
    Calculates a final lead priority score from 0 to 100.
    Higher score = higher revenue opportunity for the agency.
    This score is used to sort leads in the CSV export.
    """
    score = 0.0   # Start at zero and add points for each problem found

    # No website = highest possible opportunity (agency builds from scratch)
    if not business.get("website"):
        score += 50   # 50 base points for businesses with no online presence

    # No HTTPS = clear, easy-to-pitch security problem
    if not business.get("validation", {}).get("https"):
        score += 15   # 15 points for missing HTTPS

    # PSI score failures — worse score = more points added
    seo  = audit.get("seo_score")
    perf = audit.get("performance_score")
    acc  = audit.get("accessibility_score")
    bp   = audit.get("best_practices_score")

    if seo  is not None: score += max(0, (SEO_SCORE_THRESHOLD - seo) / SEO_SCORE_THRESHOLD * 10)
    if perf is not None: score += max(0, (PERFORMANCE_THRESHOLD - perf) / PERFORMANCE_THRESHOLD * 10)
    if acc  is not None: score += max(0, (ACCESSIBILITY_THRESHOLD - acc) / ACCESSIBILITY_THRESHOLD * 8)
    if bp   is not None: score += max(0, (BEST_PRACTICES_THRESHOLD - bp) / BEST_PRACTICES_THRESHOLD * 5)

    # Not mobile friendly = significant problem in Saudi Arabia (very high mobile usage)
    if audit.get("mobile_friendly") == 0:
        score += 8    # 8 points for failing mobile friendliness

    # Each additional issue found adds to the score (capped at 10 bonus points)
    issue_count = len(audit.get("issues_found", []))
    score += min(issue_count * 2, 10)   # 2 points per issue, max 10 total

    # AI UI/UX rating — very poor design means higher redesign opportunity
    uiux = ai_result.get("ai_uiux_score", 5)   # Default to 5 if not available
    if uiux <= 3:   score += 10   # Very poor UI/UX = high redesign opportunity
    elif uiux <= 5: score += 5    # Mediocre UI/UX = medium opportunity

    return min(round(score, 1), 100.0)   # Cap at 100 and round to 1 decimal place
