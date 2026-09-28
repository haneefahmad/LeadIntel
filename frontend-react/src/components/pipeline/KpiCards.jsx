import React from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';

export default function KpiCards() {
  const { stats } = useApp();
  const { filters, applyKpiFilter } = usePipeline();

  const isEmailActive = filters.has_email === 'Yes';
  const isPhoneActive = filters.has_phone === 'Yes';
  const isWebsiteActive = filters.has_website === 'Yes';

  const total = stats?.total || 0;
  const emailsCount = stats?.with_email || 0;
  const emailPct = stats?.email_pct != null ? stats.email_pct : 0;
  const phonesCount = stats?.with_phone || 0;
  const phonePct = stats?.phone_pct != null ? stats.phone_pct : 0;
  const websCount = stats?.with_website || 0;
  const webPct = stats?.website_pct != null ? stats.website_pct : 0;
  const totalCost = stats?.total_cost_usd != null ? stats.total_cost_usd : 0;

  return (
    <section className="kpi-grid" aria-label="System Metrics">
      {/* 1. Total Leads */}
      <div 
        className="kpi-card"
        id="cardTotalLeads"
        onClick={() => applyKpiFilter('all')}
        title="Click to reset filters and view all leads"
        style={{ cursor: 'pointer' }}
      >
        <div className="kpi-info">
          <h4>TOTAL LEADS</h4>
          <div className="kpi-value" id="kpiTotalLeads">{total.toLocaleString()}</div>
          <div className="kpi-subtext">Verified database records</div>
        </div>
      </div>

      {/* 2. Websites Audited */}
      <div 
        className={`kpi-card ${isWebsiteActive ? 'active-kpi-filter' : ''}`}
        id="cardWebsites"
        onClick={() => applyKpiFilter('website')}
        title="Click to toggle filter for active websites"
        style={{ cursor: 'pointer' }}
      >
        <div className="kpi-info">
          <h4>WEBSITES AUDITED</h4>
          <div className="kpi-value" id="kpiWebsites">{webPct}%</div>
          <div className="kpi-subtext" id="kpiWebsitesCount">{websCount.toLocaleString()} audited</div>
        </div>
      </div>

      {/* 3. Valid Phone Numbers */}
      <div 
        className={`kpi-card ${isPhoneActive ? 'active-kpi-filter' : ''}`}
        id="cardPhones"
        onClick={() => applyKpiFilter('phone')}
        title="Click to toggle filter for formatted phones"
        style={{ cursor: 'pointer' }}
      >
        <div className="kpi-info">
          <h4>VALID PHONE NUMBERS</h4>
          <div className="kpi-value" id="kpiPhones">{phonePct}%</div>
          <div className="kpi-subtext" id="kpiPhonesCount">{phonesCount.toLocaleString()} formatted</div>
        </div>
      </div>

      {/* 4. Emails Discovered */}
      <div 
        className={`kpi-card ${isEmailActive ? 'active-kpi-filter' : ''}`}
        id="cardEmails"
        onClick={() => applyKpiFilter('email')}
        title="Click to toggle filter for records with verified emails"
        style={{ cursor: 'pointer' }}
      >
        <div className="kpi-info">
          <h4>EMAILS DISCOVERED</h4>
          <div className="kpi-value" id="kpiEmails">{emailPct}%</div>
          <div className="kpi-subtext" id="kpiEmailsCount">{emailsCount.toLocaleString()} enriched</div>
        </div>
      </div>

      {/* 5. Total Apify Cost */}
      <div 
        className="kpi-card"
        id="cardApifyCost"
        title="Cumulative Apify Scraper & Actor spend"
      >
        <div className="kpi-info">
          <h4>TOTAL APIFY COST</h4>
          <div className="kpi-value" id="kpiCost">${Number(totalCost).toFixed(2)}</div>
          <div className="kpi-subtext">Cumulative spend</div>
        </div>
      </div>
    </section>
  );
}
