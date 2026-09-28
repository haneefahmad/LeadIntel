import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertTriangle, FileSpreadsheet } from 'lucide-react';

export default function AuditorView() {
  const { activeSheet, stats } = useApp();

  const total = stats?.total || 0;
  const withEmail = stats?.with_email || 0;
  const emailPct = stats?.email_pct || 0;
  const withDm = stats?.with_dm || 0;
  const dmPct = stats?.dm_pct || 0;
  const withPhone = stats?.with_phone || 0;
  const phonePct = stats?.phone_pct || 0;
  const withWeb = stats?.with_website || 0;
  const webPct = stats?.website_pct || 0;

  return (
    <div className="tab-view-container active-view">
      {/* Header */}
      <div className="view-panel-header">
        <div className="view-title-group">
          <div className="panel-badge-pill">
            <ShieldCheck size={13} />
            <span>Dataset Integrity & Governance</span>
          </div>
          <h1 className="panel-main-title">
            Data Auditor & Quality Metrics
            {activeSheet && <span className="panel-title-sheet"> / {activeSheet}</span>}
          </h1>
          <p className="panel-subtitle">
            Inspect dataset completeness, health scores, and verify GDPR/PDPL suppression compliance lists.
          </p>
        </div>
      </div>

      {/* Health Metrics Grid */}
      <div className="auditor-metrics-grid">
        <div className="auditor-metric-card">
          <div className="metric-header">
            <span className="metric-title">EMAIL FILL RATE</span>
            <span className={`metric-badge ${emailPct >= 50 ? 'emerald' : 'amber'}`}>{emailPct}%</span>
          </div>
          <div className="metric-progress-track">
            <div className="metric-progress-fill emerald" style={{ width: `${emailPct}%` }} />
          </div>
          <div className="metric-footer-text">
            <strong>{withEmail.toLocaleString()}</strong> of {total.toLocaleString()} leads have verified emails
          </div>
        </div>

        <div className="auditor-metric-card">
          <div className="metric-header">
            <span className="metric-title">DECISION MAKER IDENTIFIED</span>
            <span className={`metric-badge ${dmPct >= 50 ? 'sky' : 'amber'}`}>{dmPct}%</span>
          </div>
          <div className="metric-progress-track">
            <div className="metric-progress-fill sky" style={{ width: `${dmPct}%` }} />
          </div>
          <div className="metric-footer-text">
            <strong>{withDm.toLocaleString()}</strong> of {total.toLocaleString()} leads have named executive leadership
          </div>
        </div>

        <div className="auditor-metric-card">
          <div className="metric-header">
            <span className="metric-title">PHONE & WHATSAPP FORMATTING</span>
            <span className={`metric-badge ${phonePct >= 80 ? 'blue' : 'amber'}`}>{phonePct}%</span>
          </div>
          <div className="metric-progress-track">
            <div className="metric-progress-fill blue" style={{ width: `${phonePct}%` }} />
          </div>
          <div className="metric-footer-text">
            <strong>{withPhone.toLocaleString()}</strong> of {total.toLocaleString()} leads formatted for outreach
          </div>
        </div>

        <div className="auditor-metric-card">
          <div className="metric-header">
            <span className="metric-title">WEBSITE VALIDATION</span>
            <span className={`metric-badge ${webPct >= 70 ? 'indigo' : 'amber'}`}>{webPct}%</span>
          </div>
          <div className="metric-progress-track">
            <div className="metric-progress-fill indigo" style={{ width: `${webPct}%` }} />
          </div>
          <div className="metric-footer-text">
            <strong>{withWeb.toLocaleString()}</strong> of {total.toLocaleString()} leads have verified active domains
          </div>
        </div>
      </div>

      {/* Suppression & Compliance Notice Box */}
      <div className="compliance-banner-box">
        <div className="compliance-icon-badge">
          <ShieldAlert size={20} />
        </div>
        <div>
          <h3 className="compliance-headline">GDPR & PDPL Suppression Compliance Guard</h3>
          <p className="compliance-desc">
            Leads marked as <strong>Disqualified</strong> or <strong>Do Not Contact</strong> are permanently registered in the local suppression audit list. Any future scraper runs or re-imports automatically respect suppression keys to prevent accidental outreach.
          </p>
        </div>
      </div>
    </div>
  );
}
