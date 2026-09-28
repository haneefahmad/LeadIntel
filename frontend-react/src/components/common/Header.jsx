import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { Sun, Moon } from 'lucide-react';

export default function Header() {
  const { 
    activeTab, 
    setActiveTab, 
    activeSheet, 
    sheets, 
    stats, 
    openModal, 
    switchSheet, 
    deleteSheet,
    stopServer,
    theme,
    toggleTheme,
  } = useApp();

  const [showStopConfirm, setShowStopConfirm] = useState(false);
  const { search, filters, selectedColumns } = usePipeline();

  const csvExportUrl = api.getCsvExportUrl({
    sheet: activeSheet,
    columns: selectedColumns?.join(','),
    q: search,
    city: filters.city,
    industry: filters.industry,
    status: filters.status,
    has_website: filters.has_website,
    has_email: filters.has_email,
    has_dm: filters.has_dm,
    has_phone: filters.has_phone,
  });

  const xlsxExportUrl = api.getExportUrl(activeSheet, selectedColumns);

  return (
    <header className="app-header">
      {/* ── Brand Logo & Text ── */}
      <div className="brand-container">
        <div className="brand-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="m4.93 4.93 4.24 4.24" />
            <path d="m14.83 9.17 4.24-4.24" />
            <path d="m14.83 14.83 4.24 4.24" />
            <path d="m9.17 14.83-4.24 4.24" />
            <circle cx="12" cy="4" r="4" />
          </svg>
        </div>
        <div className="brand-text">
          <h1>LeadIntel</h1>
        </div>
        <span className="badge badge-gray" style={{ fontSize: '0.68rem', marginLeft: 4 }}>v2.1</span>
      </div>

      {/* ── Main Navigation Tabs ── */}
      <nav className="nav-tabs" aria-label="Main Navigation">
        <button
          type="button"
          className={`nav-btn ${activeTab === 'database' ? 'active' : ''}`}
          id="tabNavDatabase"
          onClick={() => setActiveTab('database')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
          <span>Companies</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          id="tabNavAnalytics"
          onClick={() => setActiveTab('analytics')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
          </svg>
          <span>Analytics</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`}
          id="tabNavHistory"
          onClick={() => setActiveTab('history')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>Run History</span>
        </button>
      </nav>

      {/* ── Header Actions ── */}
      <div className="header-actions">
        {/* Master Sheet Selector */}
        <div className="sheet-switcher-box" title="Active Master Sheet Workspace">
          <label htmlFor="selectActiveSheet" className="sheet-switcher-label">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span>Sheet:</span>
          </label>
          <select
            id="selectActiveSheet"
            className="sheet-dropdown"
            value={activeSheet}
            onChange={(e) => switchSheet(e.target.value)}
            title="Switch active Master Sheet"
          >
            {sheets.map(s => (
              <option key={s.name} value={s.name}>
                {s.name}{s.records_count !== undefined ? ` (${s.records_count} leads)` : ''}
              </option>
            ))}
          </select>
          <div className="sheet-action-separator"></div>
          <button
            type="button"
            className="btn-icon"
            id="btnOpenNewSheetModal"
            onClick={() => openModal('sheets')}
            title="Manage & Create Sheets"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <button
            type="button"
            className="btn-icon btn-icon-danger"
            id="btnDeleteActiveSheet"
            onClick={() => deleteSheet(activeSheet)}
            title="Delete current sheet"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        </div>

        {/* Export Segmented Group */}
        <div className="export-actions-group" title="Download filtered dataset">
          <span className="export-group-label">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Export</span>
          </span>
          <a href={xlsxExportUrl} className="export-chip" id="btnExportExcel" download title="Download Excel (.xlsx)">XLSX</a>
          <a href={csvExportUrl} className="export-chip" id="btnExportCSV" download title="Download CSV (.csv)">CSV</a>
        </div>

        {/* Settings Button */}
        <button
          type="button"
          className="action-btn btn-secondary"
          id="btnOpenSettings"
          onClick={() => openModal('settings')}
          title="API & System Settings"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>Settings</span>
        </button>

        {/* Theme Toggle Button */}
        <button
          type="button"
          className="action-btn btn-secondary"
          id="btnThemeToggle"
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          style={{ padding: '6px 10px', height: 32 }}
          aria-label={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
        >
          {theme === 'dark' ? (
            <Sun size={14} style={{ color: '#fbbf24' }} />
          ) : (
            <Moon size={14} style={{ color: '#6366f1' }} />
          )}
        </button>

        {/* Stop Server Button */}
        <button
          type="button"
          className="action-btn btn-danger"
          id="btnStopServerHeader"
          onClick={() => setShowStopConfirm(true)}
          title="Stop backend server and release port 8000"
          style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#f87171' }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
            <line x1="12" y1="2" x2="12" y2="12" />
          </svg>
          <span>Stop Server</span>
        </button>

        {/* New Scrape Button */}
        <button
          type="button"
          className={`action-btn btn-primary ${activeTab === 'mission' ? 'active-scrape' : ''}`}
          id="btnNewScrapeHeader"
          onClick={() => setActiveTab('mission')}
          title="Start New Scrape Mission"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>New Scrape</span>
        </button>
      </div>

      {/* Stop Server Confirmation Modal */}
      {showStopConfirm && (
        <div className="modal-overlay" onClick={() => setShowStopConfirm(false)}>
          <div 
            className="panel-card" 
            style={{ maxWidth: 440, width: '100%', padding: '24px 20px', animation: 'modalFadeIn 0.15s ease-out' }} 
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
              <div style={{
                width: 38,
                height: 38,
                borderRadius: '50%',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                color: '#ef4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
                  <line x1="12" y1="2" x2="12" y2="12" />
                </svg>
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#ffffff' }}>Stop Backend Server?</h3>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>LeadIntel OS Process Shutdown</div>
              </div>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 20px 0' }}>
              Are you sure you want to stop the server? This will gracefully shut down the Uvicorn/FastAPI process and release port <strong>8000</strong>.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                type="button"
                className="action-btn btn-secondary"
                onClick={() => setShowStopConfirm(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="action-btn btn-danger"
                style={{ backgroundColor: '#ef4444', color: '#ffffff', borderColor: '#dc2626' }}
                onClick={() => {
                  setShowStopConfirm(false);
                  stopServer();
                }}
              >
                Stop Server
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
