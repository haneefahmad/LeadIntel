import React from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';

export default function PipelineToolbar() {
  const { stats, openModal, selectedRecordIds, setSelectedRecordIds } = useApp();
  const { 
    search, 
    setSearch, 
    filters, 
    updateFilter, 
    resetFilters, 
    activeFilterCount, 
    selectedColumns 
  } = usePipeline();

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
        <div className="search-and-selection">
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

          {/* Selection badge & action */}
          {selectedRecordIds.length > 0 && (
            <div id="selectionActions" className="selection-pill">
              <span className="selection-pill-count">{selectedRecordIds.length} selected</span>
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
              className="enrich-btn enrich-apollo-btn"
              id="btnEnrichApollo"
              onClick={() => openModal('enrich', 'apollo')}
              title="Enrich verified emails, decision makers & firmographics via Apollo.io"
              style={{ borderColor: 'rgba(99, 102, 241, 0.4)', background: 'rgba(99, 102, 241, 0.12)' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>⚡ Enrich Apollo</span>
              {selectedRecordIds.length > 0 && (
                <span style={{ background: 'rgba(99, 102, 241, 0.3)', color: '#a5b4fc', borderRadius: 4, padding: '0 5px', fontSize: '0.68rem', fontWeight: 600 }}>
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
                <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', borderRadius: 4, padding: '0 4px', fontSize: '0.68rem' }}>
                  {selectedRecordIds.length}
                </span>
              )}
            </button>
          </div>

          <div className="view-controls-group">
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
