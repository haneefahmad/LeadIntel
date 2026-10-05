import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { Layers, CheckSquare, Tag, Users } from 'lucide-react';

const EMPLOYEE_BRACKETS = [
  { id: '1-10', label: '1 – 10 employees', short: '1–10' },
  { id: '11-50', label: '11 – 50 employees', short: '11–50' },
  { id: '51-200', label: '51 – 200 employees', short: '51–200' },
  { id: '201-500', label: '201 – 500 employees', short: '201–500' },
  { id: '501-1000', label: '501 – 1,000 employees', short: '501–1k' },
  { id: '1001-5000', label: '1,001 – 5,000 employees', short: '1k–5k' },
  { id: '5000+', label: '5,000+ enterprise', short: '5000+' },
  { id: 'no_count', label: 'Unspecified / Missing', short: 'Missing' },
];

function CompanySizeMultiSelect({ value, onChange, stats }) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  const selected = useMemo(() => {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    return String(value).split(',').map(s => s.trim()).filter(Boolean);
  }, [value]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const toggleBracket = (id) => {
    const next = selected.includes(id)
      ? selected.filter(x => x !== id)
      : [...selected, id];
    onChange(next.join(','));
  };

  const selectAll = () => {
    const allIds = EMPLOYEE_BRACKETS.map(b => b.id);
    onChange(allIds.join(','));
  };

  const clearAll = () => {
    onChange('');
  };

  const getLabel = () => {
    if (selected.length === 0) return 'All Company Sizes';
    if (selected.length === 1) {
      const found = EMPLOYEE_BRACKETS.find(b => b.id === selected[0]);
      return found ? found.label : selected[0];
    }
    if (selected.length === 2) {
      const s1 = EMPLOYEE_BRACKETS.find(b => b.id === selected[0])?.short || selected[0];
      const s2 = EMPLOYEE_BRACKETS.find(b => b.id === selected[1])?.short || selected[1];
      return `${s1}, ${s2}`;
    }
    return `${selected.length} Sizes Selected`;
  };

  return (
    <div className={`filter-pill-item ${selected.length > 0 ? 'is-active' : ''}`} ref={containerRef} id="pillFilterEmployees">
      <span className="pill-icon">👥</span>
      <button
        type="button"
        className="filter-pill-btn"
        onClick={() => setIsOpen(prev => !prev)}
        title="Filter by company size (Multiple Choice Selection)"
      >
        <span>{getLabel()}</span>
        {selected.length > 0 && (
          <span className="filter-pill-badge">{selected.length}</span>
        )}
        <svg 
          width="10" 
          height="10" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2.5" 
          style={{ 
            opacity: 0.7, 
            transform: isOpen ? 'rotate(180deg)' : 'none', 
            transition: 'transform 0.15s ease' 
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div className="multi-select-popover" onClick={(e) => e.stopPropagation()}>
          <div className="multi-select-header">
            <span className="multi-select-title">
              Company Size ({selected.length}/{EMPLOYEE_BRACKETS.length})
            </span>
            {selected.length > 0 && (
              <button
                type="button"
                onClick={clearAll}
                style={{ fontSize: '0.72rem', color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontWeight: 600 }}
              >
                Clear
              </button>
            )}
          </div>

          <div className="multi-select-options">
            {EMPLOYEE_BRACKETS.map(b => {
              const isChecked = selected.includes(b.id);
              let count = null;
              if (b.id === 'no_count') {
                const total = stats?.total || 0;
                const withCount = stats?.with_employee_count || 0;
                count = Math.max(0, total - withCount);
              } else if (stats?.by_employee_range) {
                count = stats.by_employee_range[b.id] ?? 0;
              }

              return (
                <label key={b.id} className={`multi-select-row ${isChecked ? 'is-checked' : ''}`}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleBracket(b.id)}
                      style={{ accentColor: '#6366f1', cursor: 'pointer', width: 14, height: 14 }}
                    />
                    <span>{b.label}</span>
                  </div>
                  {count != null && (
                    <span className="multi-select-count">{count.toLocaleString()}</span>
                  )}
                </label>
              );
            })}
          </div>

          <div className="multi-select-footer">
            <button
              type="button"
              onClick={selectAll}
              style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Select All
            </button>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="action-btn btn-primary"
              style={{ fontSize: '0.72rem', padding: '2px 10px', height: 'auto', minHeight: 24, borderRadius: 4, cursor: 'pointer' }}
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PipelineToolbar() {
  const { stats, openModal, selectedRecordIds, setSelectedRecordIds, activeSheet, showToast, reloadStats } = useApp();
  const { 
    search, 
    setSearch, 
    filters, 
    updateFilter, 
    resetFilters, 
    activeFilterCount, 
    selectedColumns,
    reloadRecords,
  } = usePipeline();

  const [batchUpdating, setBatchUpdating] = useState(false);

  // Batch CRM Status Update
  const handleBatchStatus = async (newStatus) => {
    if (!newStatus || selectedRecordIds.length === 0) return;
    try {
      setBatchUpdating(true);
      await Promise.all(
        selectedRecordIds.map(id => 
          api.updateRecord(id, { status: newStatus, updated_by: 'Batch CRM Update' }, activeSheet)
        )
      );
      showToast(`Updated status to "${newStatus}" for ${selectedRecordIds.length} leads!`, 'success');
      setSelectedRecordIds([]);
      await reloadStats(activeSheet);
      await reloadRecords();
    } catch (err) {
      console.error('Batch status update failed:', err);
      showToast(`Batch update failed: ${err.message}`, 'error');
    } finally {
      setBatchUpdating(false);
    }
  };

  // Batch Pipeline Stage Update
  const handleBatchStage = async (newStage) => {
    if (!newStage || selectedRecordIds.length === 0) return;
    try {
      setBatchUpdating(true);
      await Promise.all(
        selectedRecordIds.map(id => 
          api.updateRecord(id, { pipeline_stage: newStage, updated_by: 'Batch CRM Stage' }, activeSheet)
        )
      );
      showToast(`Moved ${selectedRecordIds.length} leads to "${newStage.replace(/_/g, ' ')}"!`, 'success');
      setSelectedRecordIds([]);
      await reloadStats(activeSheet);
      await reloadRecords();
    } catch (err) {
      console.error('Batch stage update failed:', err);
      showToast(`Batch stage update failed: ${err.message}`, 'error');
    } finally {
      setBatchUpdating(false);
    }
  };

  const cities = Object.entries(stats?.by_city || {})
    .filter(([c]) => c && c !== 'Unspecified')
    .sort((a, b) => b[1] - a[1]);

  const industries = Object.entries(stats?.by_industry || {})
    .filter(([ind]) => ind && ind !== 'General')
    .sort((a, b) => b[1] - a[1]);

  return (
    <div className="pipeline-control-panel">
      {/* ── Tier 1: Search, Selection & Primary Action Bar ── */}
      <div className="pipeline-top-bar">
        <div className="search-and-selection" style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <div className="search-input-wrapper">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              id="tableSearch"
              placeholder="Search by company, title, email, locat..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button
                type="button"
                id="btnClearSearch"
                className="btn-clear-search"
                onClick={() => setSearch('')}
                title="Clear search"
              >
                ×
              </button>
            )}
          </div>

          {/* Selection badge & Batch CRM actions */}
          {selectedRecordIds.length > 0 && (
            <div id="selectionActions" className="selection-pill" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="selection-pill-count">{selectedRecordIds.length} selected</span>

              {/* Batch Status Picker */}
              <select
                onChange={(e) => { handleBatchStatus(e.target.value); e.target.value = ''; }}
                defaultValue=""
                disabled={batchUpdating}
                style={{
                  fontSize: '0.72rem',
                  padding: '2px 6px',
                  borderRadius: 4,
                  border: '1px solid var(--border)',
                  background: 'var(--card)',
                  color: 'var(--text)',
                  cursor: 'pointer',
                }}
              >
                <option value="" disabled>Set Status...</option>
                <option value="New">Mark New</option>
                <option value="Contacted">Mark Contacted</option>
                <option value="Qualified">Mark Qualified</option>
                <option value="Proposal_Sent">Mark Proposal</option>
                <option value="Won">Mark Won</option>
                <option value="Disqualified">Mark Disqualified</option>
              </select>

              {/* Batch Stage Picker */}
              <select
                onChange={(e) => { handleBatchStage(e.target.value); e.target.value = ''; }}
                defaultValue=""
                disabled={batchUpdating}
                style={{
                  fontSize: '0.72rem',
                  padding: '2px 6px',
                  borderRadius: 4,
                  border: '1px solid var(--border)',
                  background: 'var(--card)',
                  color: 'var(--text)',
                  cursor: 'pointer',
                }}
              >
                <option value="" disabled>Set Stage...</option>
                <option value="Identified">1. Identified</option>
                <option value="Contacted">2. Contacted</option>
                <option value="Qualified">3. Qualified</option>
                <option value="Proposal">4. Proposal</option>
                <option value="Negotiation">5. Negotiation</option>
                <option value="Closed_Won">6. Closed Won</option>
              </select>

              <button
                type="button"
                className="selection-pill-clear"
                onClick={() => setSelectedRecordIds([])}
                title="Clear selection"
              >
                Clear
              </button>
            </div>
          )}
        </div>

        {/* Right: Action Suite (Enrichment Engine & View Options) */}
        <div className="pipeline-actions-group">
          <div className="enrichment-btn-group">
            <button
              type="button"
              className="enrich-btn"
              id="btnExtractCompany"
              onClick={() => openModal('extractCompany')}
              title="Extract single company firmographics & contacts via Apify or Apollo"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 21h18" />
                <path d="M5 21V7l8-4v18" />
                <path d="M19 21V11l-6-4" />
                <path d="M9 9v.01" />
                <path d="M9 12v.01" />
                <path d="M9 15v.01" />
                <path d="M9 18v.01" />
              </svg>
              <span>+ Extract Company</span>
            </button>

            <button
              type="button"
              className="enrich-btn enrich-apollo-btn"
              id="btnEnrichApollo"
              onClick={() => openModal('enrich', 'apollo')}
              title="Enrich verified emails, decision makers & firmographics via Apollo.io"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>⚡ Enrich Apollo</span>
              {selectedRecordIds.length > 0 && (
                <span className="mono-badge badge-indigo" style={{ padding: '0 5px', fontSize: '0.68rem', fontWeight: 700 }}>
                  {selectedRecordIds.length}
                </span>
              )}
            </button>

            <button
              type="button"
              className="enrich-btn enrich-apify-btn"
              id="btnEnrichApify"
              onClick={() => openModal('enrich', 'apify')}
              title="Enrich empty Google Maps/Places details via Apify"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
              </svg>
              <span>Enrich Apify</span>
              {selectedRecordIds.length > 0 && (
                <span className="mono-badge badge-emerald" style={{ padding: '0 5px', fontSize: '0.68rem', fontWeight: 700 }}>
                  {selectedRecordIds.length}
                </span>
              )}
            </button>
          </div>

          <div className="view-controls-group">
            <button
              type="button"
              className="action-btn btn-secondary"
              id="btnUploadDatasheet"
              onClick={() => openModal('sheets', { tab: 'upload' })}
              title="Upload an Excel (.xlsx) or CSV datasheet into this workspace"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <span>Upload Sheet</span>
            </button>

            <button
              type="button"
              className="action-btn btn-secondary columns-btn"
              id="btnOpenColumnsModal"
              onClick={() => openModal('columns')}
              title="Customize Visible Columns"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
                <line x1="15" y1="3" x2="15" y2="21" />
              </svg>
              <span>Columns</span>
              <span className="badge badge-indigo" id="badgeColumnCount" style={{ padding: '1px 6px', fontSize: '0.72rem', fontWeight: 600 }}>
                {selectedColumns?.length || 15}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* ── Tier 2: Dedicated Filter Bar ── */}
      <div className="pipeline-filter-bar">
        <div className="filter-bar-header">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          <span>Filters</span>
        </div>

        <div className="filter-pills-list">
          {/* Location Filter Pill */}
          <div className={`filter-pill-item ${filters.city ? 'is-active' : ''}`} id="pillFilterCity">
            <span className="pill-icon">📍</span>
            <select
              id="filterCity"
              className="filter-select"
              value={filters.city}
              onChange={(e) => updateFilter('city', e.target.value)}
            >
              <option value="">All Locations ({(stats?.total || 0).toLocaleString()})</option>
              {cities.map(([c, count]) => (
                <option key={c} value={c}>{c} ({count})</option>
              ))}
              {stats?.by_city?.['Unspecified'] && (
                <option value="Unspecified">Unspecified ({stats.by_city['Unspecified']})</option>
              )}
            </select>
          </div>

          {/* Industry Filter Pill */}
          <div className={`filter-pill-item ${filters.industry ? 'is-active' : ''}`} id="pillFilterIndustry">
            <span className="pill-icon">🏢</span>
            <select
              id="filterIndustry"
              className="filter-select"
              value={filters.industry}
              onChange={(e) => updateFilter('industry', e.target.value)}
            >
              <option value="">All Industries ({(stats?.total || 0).toLocaleString()})</option>
              {industries.map(([ind, count]) => (
                <option key={ind} value={ind}>{ind} ({count})</option>
              ))}
              {stats?.by_industry?.['General'] && (
                <option value="General">General ({stats.by_industry['General']})</option>
              )}
            </select>
          </div>

          {/* Company Size / Employee Count Multiple Choice Filter Pill */}
          <CompanySizeMultiSelect
            value={filters.employee_count}
            onChange={(val) => updateFilter('employee_count', val)}
            stats={stats}
          />

          {/* Status Filter Pill */}
          <div className={`filter-pill-item ${filters.status ? 'is-active' : ''}`} id="pillFilterStatus">
            <span className="pill-icon">🏷️</span>
            <select
              id="filterStatus"
              className="filter-select"
              value={filters.status}
              onChange={(e) => updateFilter('status', e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="New">New</option>
              <option value="Contacted">Contacted</option>
              <option value="In_Conversation">In Conversation</option>
              <option value="Proposal_Sent">Proposal Sent</option>
              <option value="Qualified">Qualified</option>
              <option value="Meeting_Scheduled">Meeting Scheduled</option>
              <option value="Won">Won</option>
              <option value="Lost">Lost</option>
              <option value="Disqualified">Disqualified</option>
            </select>
          </div>

          {/* Website Filter Pill */}
          <div className={`filter-pill-item ${filters.has_website ? 'is-active' : ''}`} id="pillFilterWebsite">
            <span className="pill-icon">🌐</span>
            <select
              id="filterWebsite"
              className="filter-select"
              value={filters.has_website}
              onChange={(e) => updateFilter('has_website', e.target.value)}
            >
              <option value="">All Websites</option>
              <option value="Yes">Has Website ({(stats?.with_website || 0).toLocaleString()})</option>
              <option value="No">No Website</option>
            </select>
          </div>

          {/* Email Filter Pill */}
          <div className={`filter-pill-item ${filters.has_email ? 'is-active' : ''}`} id="pillFilterEmail">
            <span className="pill-icon">✉️</span>
            <select
              id="filterEmail"
              className="filter-select"
              value={filters.has_email}
              onChange={(e) => updateFilter('has_email', e.target.value)}
            >
              <option value="">All Email</option>
              <option value="Yes">Has Email ({(stats?.with_email || 0).toLocaleString()})</option>
              <option value="No">No Email</option>
            </select>
          </div>

          {/* Decision Maker Filter Pill */}
          <div className={`filter-pill-item ${filters.has_dm ? 'is-active' : ''}`} id="pillFilterDm">
            <span className="pill-icon">👤</span>
            <select
              id="filterDm"
              className="filter-select"
              value={filters.has_dm}
              onChange={(e) => updateFilter('has_dm', e.target.value)}
            >
              <option value="">All Leadership</option>
              <option value="Yes">Has Decision Maker ({(stats?.with_dm || 0).toLocaleString()})</option>
              <option value="No">No Decision Maker</option>
            </select>
          </div>

          {/* Phone Filter Pill */}
          <div className={`filter-pill-item ${filters.has_phone ? 'is-active' : ''}`} id="pillFilterPhone">
            <span className="pill-icon">📞</span>
            <select
              id="filterPhone"
              className="filter-select"
              value={filters.has_phone}
              onChange={(e) => updateFilter('has_phone', e.target.value)}
            >
              <option value="">All Phones</option>
              <option value="Yes">Has Phone ({(stats?.with_phone || 0).toLocaleString()})</option>
              <option value="No">No Phone</option>
            </select>
          </div>

          {/* Reset Filters Button */}
          {activeFilterCount > 0 && (
            <button
              type="button"
              className="btn-reset-filters"
              id="btnResetFilters"
              onClick={resetFilters}
              title="Reset all search filters"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
              <span id="resetFiltersText">Clear Filters ({activeFilterCount})</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
