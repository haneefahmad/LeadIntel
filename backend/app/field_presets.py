"""
Business Lead Generator — Field Presets & Dynamic Schema Customizer.
Provides metadata, categories, and presets for the active 45-column schema.
"""

from typing import Any

COLUMN_CATEGORIES = [
    {
        "id": "identity",
        "name": "Identity & System",
        "icon": "hash",
        "description": "Unique identifiers, audit stamps, and global record status",
    },
    {
        "id": "company",
        "name": "Company Firmographics",
        "icon": "briefcase",
        "description": "Company names, categorization, corporate structure, and size",
    },
    {
        "id": "location",
        "name": "Location & Maps",
        "icon": "map-pin",
        "description": "Geographic location, physical address, coordinates, and Google Maps",
    },
    {
        "id": "reputation",
        "name": "Reputation & Reviews",
        "icon": "star",
        "description": "Google Places rating and review metrics",
    },
    {
        "id": "contact",
        "name": "Contact & Digital Presence",
        "icon": "phone",
        "description": "Public phone numbers, WhatsApp, general emails, websites, and tech stack",
    },
    {
        "id": "decision_maker",
        "name": "Decision Maker & Leadership",
        "icon": "user-check",
        "description": "Executive names, job titles, verified emails, direct phones, and LinkedIn",
    },
    {
        "id": "crm",
        "name": "Pipeline & CRM",
        "icon": "trello",
        "description": "Sales pipeline stages, outreach status, deal values, notes, and tags",
    },
]

COLUMN_DEFINITIONS: list[dict[str, Any]] = [
    # 1. Identity & System
    {
        "id": "Record_ID",
        "label": "Record id",
        "category": "identity",
        "description": "System-generated unique ID per lead",
    },
    {
        "id": "Date_Added",
        "label": "Date added",
        "category": "identity",
        "description": "Date lead was discovered and added",
    },
    {
        "id": "Added_By",
        "label": "Added by",
        "category": "identity",
        "description": "Campaign manager or script that scraped this lead",
    },
    {
        "id": "Lead_Status",
        "label": "Lead status",
        "category": "identity",
        "description": "Overall lead lifecycle status (New, Contacted, Qualified, etc.)",
    },

    # 2. Company Firmographics
    {
        "id": "Company_Name",
        "label": "Company Name",
        "category": "company",
        "description": "Primary corporate or organization name",
    },
    {
        "id": "Company_Type",
        "label": "Company type",
        "category": "company",
        "description": "Enterprise classification (Corporation, LLC, Partnership, etc.)",
    },
    {
        "id": "Primary_Industry",
        "label": "Primary Industry",
        "category": "company",
        "description": "Main target industry category",
    },
    {
        "id": "Secondary_Industry",
        "label": "Secondary Industry",
        "category": "company",
        "description": "Specialized sub-sector or operational niche",
    },
    {
        "id": "Employee_Count",
        "label": "Employee count",
        "category": "company",
        "description": "Workforce size or headcount bracket",
    },

    # 3. Location & Maps
    {
        "id": "Country",
        "label": "Country",
        "category": "location",
        "description": "Country of operation",
    },
    {
        "id": "State",
        "label": "State",
        "category": "location",
        "description": "State or province jurisdiction (e.g. Texas)",
    },
    {
        "id": "City",
        "label": "City",
        "category": "location",
        "description": "Metropolitan market or city (e.g. Austin)",
    },
    {
        "id": "Full_Address",
        "label": "Full Address",
        "category": "location",
        "description": "Formatted physical business address",
    },
    {
        "id": "Postal_Code",
        "label": "Postal code",
        "category": "location",
        "description": "Postal or ZIP code",
    },
    {
        "id": "Google_Maps_URL",
        "label": "Google maps url",
        "category": "location",
        "description": "Direct Google Maps navigation URL",
    },

    # 4. Reputation & Reviews
    {
        "id": "Google_Rating",
        "label": "Google Rating",
        "category": "reputation",
        "description": "Star rating out of 5.0",
    },
    {
        "id": "Reviews_Count",
        "label": "Reviews count",
        "category": "reputation",
        "description": "Total count of public Google reviews",
    },

    # 5. Contact & Digital Presence
    {
        "id": "Primary_Phone",
        "label": "Primary phone",
        "category": "contact",
        "description": "Main business switchboard or phone",
    },
    {
        "id": "General_Email",
        "label": "General Email",
        "category": "contact",
        "description": "Corporate or info@ email address",
    },
    {
        "id": "WhatsApp_Number",
        "label": "Whatsapp number",
        "category": "contact",
        "description": "WhatsApp direct messaging number",
    },
    {
        "id": "Website_URL",
        "label": "Website URL",
        "category": "contact",
        "description": "Verified domain website URL",
    },
    {
        "id": "Has_Website",
        "label": "Has Website",
        "category": "contact",
        "description": "Yes / No web presence indicator",
    },
    {
        "id": "Company_LinkedIn",
        "label": "Company Linkedin",
        "category": "contact",
        "description": "Company official LinkedIn profile link",
    },

    # 6. Primary Decision Maker
    {
        "id": "DM_Full_Name",
        "label": "DM Full name",
        "category": "decision_maker",
        "description": "Key executive / decision maker name",
    },
    {
        "id": "DM_Title",
        "label": "DM Title",
        "category": "decision_maker",
        "description": "Executive job title / designation",
    },
    {
        "id": "DM_Authority_Level",
        "label": "DM Authority Level",
        "category": "decision_maker",
        "description": "C-Suite, VP, Director, or Owner classification",
    },
    {
        "id": "DM_Direct_Email",
        "label": "DM Direct Email",
        "category": "decision_maker",
        "description": "Direct verified executive email address",
    },
    {
        "id": "DM_Email_Status",
        "label": "DM Email Status",
        "category": "decision_maker",
        "description": "Verification status (verified, extrapolated, etc.)",
    },
    {
        "id": "DM_Email_Score",
        "label": "DM Email Score",
        "category": "decision_maker",
        "description": "Confidence score for verified email (0-100)",
    },
    {
        "id": "DM_Direct_Phone",
        "label": "DM Direct phone",
        "category": "decision_maker",
        "description": "Executive direct mobile or desk extension",
    },
    {
        "id": "DM_LinkedIn_URL",
        "label": "DM Linkedin URL",
        "category": "decision_maker",
        "description": "Executive personal LinkedIn profile link",
    },

    # 7. Pipeline & CRM
    {
        "id": "Pipeline_Stage",
        "label": "Pipeline Stage",
        "category": "crm",
        "description": "Sales pipeline funnel stage",
    },
    {
        "id": "Outreach_Status",
        "label": "Outreach Status",
        "category": "crm",
        "description": "Current outreach cadence status",
    },
    {
        "id": "Assigned_To",
        "label": "Assigned to",
        "category": "crm",
        "description": "Sales development rep or account owner",
    },
    {
        "id": "Deal_Value",
        "label": "Deal Value",
        "category": "crm",
        "description": "Estimated or closed deal value ($)",
    },
    {
        "id": "CRM_Notes",
        "label": "CRM Notes",
        "category": "crm",
        "description": "Sales notes and interaction summary",
    },
    {
        "id": "Tags",
        "label": "Tags",
        "category": "crm",
        "description": "Custom segmentation tags",
    },
    {
        "id": "Last_Updated",
        "label": "Last Updated",
        "category": "crm",
        "description": "Timestamp of most recent record update",
    },
    {
        "id": "Updated_By",
        "label": "Updated by",
        "category": "crm",
        "description": "User or process that last modified this record",
    },
]

COLUMN_MAP = {col["id"]: col for col in COLUMN_DEFINITIONS}

PRESETS = {
    "executive": {
        "id": "executive",
        "name": "Executive Outreach",
        "icon": "zap",
        "badge": "Default",
        "description": "High-impact view for direct leadership outreach, verified DM contacts, and deal stage.",
        "columns": [
            "Record_ID",
            "Company_Name",
            "Company_Type",
            "Primary_Industry",
            "Country",
            "State",
            "City",
            "Primary_Phone",
            "WhatsApp_Number",
            "Website_URL",
            "Company_LinkedIn",
            "General_Email",
            "DM_Full_Name",
            "DM_Title",
            "DM_Authority_Level",
            "DM_Direct_Email",
            "DM_Direct_Phone",
            "DM_LinkedIn_URL",
            "Outreach_Status",
        ],
    },
    "email": {
        "id": "email",
        "name": "Cold Email Campaign",
        "icon": "mail",
        "badge": "Email",
        "description": "Laser-focused on deliverability: company name, decision maker, verified email, and score.",
        "columns": [
            "Company_Name",
            "Primary_Industry",
            "State",
            "City",
            "Website_URL",
            "General_Email",
            "Company_LinkedIn",
            "DM_Full_Name",
            "DM_Title",
            "DM_Direct_Email",
            "DM_Email_Status",
            "DM_Email_Score",
        ],
    },
    "calling": {
        "id": "calling",
        "name": "Cold Calling",
        "icon": "phone-call",
        "badge": "Phone",
        "description": "Optimized for SDRs: phone numbers, WhatsApp, physical address, and decision maker name.",
        "columns": [
            "Company_Name",
            "Primary_Industry",
            "State",
            "City",
            "Full_Address",
            "Primary_Phone",
            "WhatsApp_Number",
            "DM_Full_Name",
            "DM_Title",
            "DM_Direct_Phone",
            "Outreach_Status",
        ],
    },
    "all": {
        "id": "all",
        "name": "All Fields (39 Columns)",
        "icon": "grid",
        "badge": "Complete",
        "description": "The complete, pristine 39-column dataset covering all firmographic, decision maker, and CRM attributes.",
        "columns": [col["id"] for col in COLUMN_DEFINITIONS],
    },
}


def get_field_catalog() -> dict[str, Any]:
    """Returns the full catalog of fields categorized with presets."""
    return {
        "categories": COLUMN_CATEGORIES,
        "fields": COLUMN_DEFINITIONS,
        "presets": PRESETS,
        "default_preset": "executive",
    }


def get_column_label(col_id: str) -> str:
    """Returns user-friendly label for a column ID."""
    return COLUMN_MAP.get(col_id, {}).get("label", col_id)
