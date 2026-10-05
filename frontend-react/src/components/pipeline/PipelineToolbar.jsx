import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { 
  MapPin, 
  Building2, 
  Users, 
  Tag, 
  Globe, 
  Mail, 
  UserCheck, 
  Phone, 
  Filter, 
  X, 
  ChevronDown, 
  Search, 
  Check, 
  RotateCcw, 
  SlidersHorizontal,
  Sparkles,
  Layers
} from 'lucide-react';

const EMPLOYEE_BRACKETS = [
  { id: '1-10', label: '1 – 10 employees', short: '1–10' },
  { id: '11-50', label: '11 – 50 employees', short: '11–50' },
  { id: '51-200', label: '51 – 200 employees', short: '51–200' },
  { id: '201-500', label: '201 – 500 employees', short: '201–500' },
  { id: '501-1000', label: '501 – 1,000 employees', short: '501–1k' },
  { id: '1001-5000', label: '1,001 – 5,000 employees', short: '1k–5k' },
  { id: '5000+', label: '5,000+ enterprise', short: '5000+' },
  { id: 'has_count', label: 'Has Employee Count', short: 'With Size' },
  { id: 'no_count', label: 'Unspecified / Missing', short: 'Missing' },
];

const STATUS_OPTIONS = [
  { id: 'New', label: 'New', dotColor: '#3b82f6' },
  { id: 'Contacted', label: 'Contacted', dotColor: '#f59e0b' },
  { id: 'In_Conversation', label: 'In Conversation', dotColor: '#8b5cf6' },
  { id: 'Proposal_Sent', label: 'Proposal Sent', dotColor: '#ec4899' },
  { id: 'Qualified', label: 'Qualified', dotColor: '#10b981' },
  { id: 'Meeting_Scheduled', label: 'Meeting Scheduled', dotColor: '#06b6d4' },
  { id: 'Won', label: 'Won', dotColor: '#22c55e' },
  { id: 'Lost', label: 'Lost', dotColor: '#ef4444' },
  { id: 'Disqualified', label: 'Disqualified', dotColor: '#64748b' },
];

/**
 * Enterprise Filter Popover Component
 * Supports search, live item counts, multi-choice, keyboard dismissal, and instant quick-clearing.
 */
function FilterPopover({
  id,
  label,
  icon: Icon,
  value,
  onChange,
  options = [],
  isMulti = true,
  searchable = false,
  searchPlaceholder = 'Search...',
  isOpen = false,
  onToggle,
  onClose,
  alignRight = false,
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const selectedValues = useMemo(() => {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    return String(value)
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);
  }, [value]);

  useEffect(() => {
    if (!isOpen) {
      setSearchQuery('');
    }
  }, [isOpen]);

  const filteredOptions = useMemo(() => {
    if (!searchQuery.trim()) return options;
    const q = searchQuery.toLowerCase().trim();
    return options.filter(opt => (opt.label || opt.id || '').toLowerCase().includes(q));
  }, [options, searchQuery]);

  const handleSelectOption = (optId) => {
    if (isMulti) {
      const next = selectedValues.includes(optId)
        ? selectedValues.filter(x => x !== optId)
        : [...selectedValues, optId];
      onChange(next.join(','));
    } else {
      if (selectedValues.includes(optId)) {
        onChange('');
      } else {
        onChange(optId);
      }
      onClose?.();
    }
  };

  const handleSelectAll = (e) => {
    e?.stopPropagation();
    const allIds = filteredOptions.map(o => o.id);
    const combined = Array.from(new Set([...selectedValues, ...allIds]));
    onChange(combined.join(','));
  };

  const handleClear = (e) => {
    e?.stopPropagation();
    onChange('');
  };

  const getButtonText = () => {
    if (selectedValues.length === 0) return label;
    if (selectedValues.length === 1) {
      const found = options.find(o => o.id === selectedValues[0]);
      return found ? found.label : selectedValues[0];
    }
    if (selectedValues.length === 2) {
      const o1 = options.find(o => o.id === selectedValues[0])?.short || selectedValues[0];
      const o2 = options.find(o => o.id === selectedValues[1])?.short || selectedValues[1];
      return `${o1}, ${o2}`;
    }
    return `${label} (${selectedValues.length})`;
  };

  const isFiltered = selectedValues.length > 0;

  return (
    <div
      className={`filter-control-wrapper ${isFiltered ? 'is-active' : ''} ${isOpen ? 'is-open' : ''}`}
      id={`filter-${id}`}
    >
      <button
        type="button"
        className={`filter-control-btn ${isFiltered ? 'is-active' : ''} ${isOpen ? 'is-open' : ''}`}
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <span className="filter-control-icon">
          <Icon size={13} strokeWidth={2.2} />
        </span>
        <span className="filter-control-text" title={getButtonText()}>
          {getButtonText()}
        </span>
        {isFiltered && isMulti && selectedValues.length > 1 && (
          <span className="filter-control-count-pill">{selectedValues.length}</span>
        )}
        {isFiltered && (
          <span
            role="button"
            className="filter-quick-clear-btn"
            onClick={(e) => {
              e.stopPropagation();
              onChange('');
            }}
            title={`Clear ${label} filter`}
          >
            <X size={10} strokeWidth={2.6} />
          </span>
        )}
        <ChevronDown 
          size={12} 
          strokeWidth={2.2} 
          className={`filter-chevron ${isOpen ? 'is-open' : ''}`} 
        />
      </button>

      {isOpen && (
        <div
          className={`filter-popover-menu ${alignRight ? 'align-right' : ''}`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Popover Header */}
          <div className="filter-popover-header">
            <div className="filter-popover-title">
              <Icon size={12} strokeWidth={2.2} />
              <span>{label}</span>
              {isFiltered && (
                <span className="popover-selection-indicator">({selectedValues.length})</span>
              )}
            </div>
            <div className="popover-header-actions">
              {isMulti && (
                <button
                  type="button"
                  className="popover-action-text-btn"
                  onClick={handleSelectAll}
                >
                  All
                </button>
              )}
              {isFiltered && (
                <button
                  type="button"
                  className="popover-clear-btn"
                  onClick={handleClear}
                >
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* Search Box */}
          {searchable && (
            <div className="filter-popover-search">
              <Search size={12} strokeWidth={2.2} className="popover-search-icon" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoFocus
              />
              {searchQuery && (
                <button
                  type="button"
                  className="popover-search-clear"
                  onClick={() => setSearchQuery('')}
                >
                  <X size={10} strokeWidth={2.5} />
                </button>
              )}
            </div>
          )}

          {/* Options List */}
          <div className="filter-popover-list">
            {!isMulti && (
              <button
                type="button"
                className={`filter-popover-item ${!isFiltered ? 'is-selected' : ''}`}
                onClick={() => { onChange(''); onClose?.(); }}
              >
                <div className="item-main">
                  <span className="item-label">All {label}</span>
                </div>
                {!isFiltered && <Check size={12} strokeWidth={2.5} className="item-check-icon" />}
              </button>
            )}

            {filteredOptions.length === 0 ? (
              <div className="filter-popover-empty">No matching options found</div>
            ) : (
              filteredOptions.map(opt => {
                const isSelected = selectedValues.includes(opt.id);
                return (
                  <button
                    key={opt.id}
                    type="button"
                    className={`filter-popover-item ${isSelected ? 'is-selected' : ''}`}
                    onClick={() => handleSelectOption(opt.id)}
                  >
                    <div className="item-main">
                      {isMulti ? (
                        <span className={`custom-checkbox ${isSelected ? 'is-checked' : ''}`}>
                          {isSelected && <Check size={10} strokeWidth={3} />}
                        </span>
                      ) : (
                        opt.dotColor && (
                          <span className="status-dot" style={{ backgroundColor: opt.dotColor }} />
                        )
                      )}
                      {isMulti && opt.dotColor && (
                        <span className="status-dot" style={{ backgroundColor: opt.dotColor }} />
                      )}
                      <span className="item-label" title={opt.label}>{opt.label}</span>
                    </div>

                    <div className="item-meta">
                      {opt.count != null && (
                        <span className="item-count-badge">
                          {Number(opt.count).toLocaleString()}
                        </span>
                      )}
                      {!isMulti && isSelected && (
                        <Check size={12} strokeWidth={2.5} className="item-check-icon" />
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Footer for multi-select */}
          {isMulti && (
            <div className="filter-popover-footer">
              <span className="popover-footer-summary">
                {selectedValues.length} selected
              </span>
              <button
                type="button"
                className="btn-apply-popover"
                onClick={onClose}
              >
                Done
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Compact Channel / Data-Quality Filter Popover
 * For Website, Email, Decision Maker, Phone.
 */
function ChannelFilterPopover({
  id,
  label,
  icon: Icon,
  value,
  onChange,
  yesCount,
  totalCount,
  isOpen = false,
  onToggle,
  onClose,
  alignRight = false,
}) {
  const isActive = value === 'Yes' || value === 'No';

  return (
    <div
      className={`filter-control-wrapper ${isActive ? 'is-active' : ''} ${isOpen ? 'is-open' : ''}`}
      id={`filter-${id}`}
    >
      <button
        type="button"
        className={`filter-control-btn ${isActive ? 'is-active' : ''} ${isOpen ? 'is-open' : ''}`}
        onClick={onToggle}
        title={`Filter by ${label}`}
        aria-expanded={isOpen}
      >
        <span className="filter-control-icon">
          <Icon size={13} strokeWidth={2.2} />
        </span>
        <span className="filter-control-text">
          {value === 'Yes' ? `Has ${label}` : value === 'No' ? `No ${label}` : label}
        </span>
        {isActive && (
          <span
            role="button"
            className="filter-quick-clear-btn"
            onClick={(e) => {
              e.stopPropagation();
              onChange('');
            }}
            title={`Clear ${label} filter`}
          >
            <X size={10} strokeWidth={2.6} />
          </span>
        )}
        <ChevronDown 
          size={12} 
          strokeWidth={2.2} 
          className={`filter-chevron ${isOpen ? 'is-open' : ''}`} 
        />
      </button>

      {isOpen && (
        <div
          className={`filter-popover-menu compact-channel-menu ${alignRight ? 'align-right' : ''}`}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="filter-popover-header">
            <div className="filter-popover-title">
              <Icon size={12} strokeWidth={2.2} />
              <span>{label}</span>
            </div>
            {isActive && (
              <button 
                type="button" 
                className="popover-clear-btn" 
                onClick={() => { onChange(''); onClose?.(); }}
              >
                Reset
              </button>
            )}
          </div>

          <div className="filter-popover-list">
            <button
              type="button"
              className={`filter-popover-item ${!value ? 'is-selected' : ''}`}
              onClick={() => { onChange(''); onClose?.(); }}
            >
              <div className="item-main">
                <span className="item-label">All (Any)</span>
              </div>
              {!value && <Check size={12} strokeWidth={2.5} className="item-check-icon" />}
            </button>

            <button
              type="button"
              className={`filter-popover-item ${value === 'Yes' ? 'is-selected' : ''}`}
              onClick={() => { onChange('Yes'); onClose?.(); }}
            >
              <div className="item-main">
                <span className="status-dot dot-green" />
                <span className="item-label">Has {label}</span>
              </div>
              <div className="item-meta">
                {yesCount != null && (
                  <span className="item-count-badge">{(yesCount).toLocaleString()}</span>
                )}
                {value === 'Yes' && <Check size={12} strokeWidth={2.5} className="item-check-icon" />}
              </div>
            </button>

            <button
              type="button"
              className={`filter-popover-item ${value === 'No' ? 'is-selected' : ''}`}
              onClick={() => { onChange('No'); onClose?.(); }}
            >
              <div className="item-main">
                <span className="status-dot dot-muted" />
                <span className="item-label">No {label}</span>
              </div>
              <div className="item-meta">
                {totalCount != null && yesCount != null && (
                  <span className="item-count-badge">
                    {Math.max(0, totalCount - yesCount).toLocaleString()}
                  </span>
                )}
                {value === 'No' && <Check size={12} strokeWidth={2.5} className="item-check-icon" />}
              </div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PipelineToolbar() {
  const { 
    stats, 
    openModal, 
    selectedRecordIds, 
    setSelectedRecordIds, 
    activeSheet, 
    showToast, 
    reloadStats 
  } = useApp();

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
  const [openDropdown, setOpenDropdown] = useState(null);
  const toolbarRef = useRef(null);

  const toggleDropdown = (id) => {
    setOpenDropdown(prev => prev === id ? null : id);
  };

  const closeDropdown = () => {
    setOpenDropdown(null);
  };

  // Close dropdown on outside click or Escape key
  useEffect(() => {
    if (!openDropdown) return;
    const handleGlobalMouseDown = (e) => {
      if (toolbarRef.current && !toolbarRef.current.contains(e.target)) {
        setOpenDropdown(null);
      }
    };
    const handleGlobalKeyDown = (e) => {
      if (e.key === 'Escape') {
        setOpenDropdown(null);
      }
    };
    document.addEventListener('mousedown', handleGlobalMouseDown);
    document.addEventListener('keydown', handleGlobalKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleGlobalMouseDown);
      document.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, [openDropdown]);

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

  // City options from stats
  const cityOptions = useMemo(() => {
    const list = Object.entries(stats?.by_city || {})
      .filter(([c]) => c && c !== 'Unspecified')
      .sort((a, b) => b[1] - a[1])
      .map(([c, count]) => ({ id: c, label: c, count }));
    if (stats?.by_city?.['Unspecified']) {
      list.push({ id: 'Unspecified', label: 'Unspecified', count: stats.by_city['Unspecified'] });
    }
    return list;
  }, [stats?.by_city]);

  // Industry options from stats
  const industryOptions = useMemo(() => {
    const list = Object.entries(stats?.by_industry || {})
      .filter(([ind]) => ind && ind !== 'General')
      .sort((a, b) => b[1] - a[1])
      .map(([ind, count]) => ({ id: ind, label: ind, count }));
    if (stats?.by_industry?.['General']) {
      list.push({ id: 'General', label: 'General / Other', count: stats.by_industry['General'] });
    }
    return list;
  }, [stats?.by_industry]);

  // Company size options with live counts
  const employeeOptions = useMemo(() => {
    return EMPLOYEE_BRACKETS.map(b => {
      let count = null;
      if (b.id === 'no_count') {
        const total = stats?.total || 0;
        const withCount = stats?.with_employee_count || 0;
        count = Math.max(0, total - withCount);
      } else if (b.id === 'has_count') {
        count = stats?.with_employee_count ?? 0;
      } else if (stats?.by_employee_range) {
        count = stats.by_employee_range[b.id] ?? 0;
      }
      return { ...b, count };
    });
  }, [stats?.by_employee_range, stats?.total, stats?.with_employee_count]);

  // Status options with counts
  const statusOptions = useMemo(() => {
    return STATUS_OPTIONS.map(s => {
      const count = stats?.by_status?.[s.id] ?? stats?.by_status?.[s.label];
      return { ...s, count };
    });
  }, [stats?.by_status]);

  // Compute Active Filter Chips for the dedicated tray
  const activeChips = useMemo(() => {
    const chips = [];

    if (search.trim()) {
      chips.push({
        key: 'search',
        label: 'Search',
        displayValue: `"${search.trim()}"`,
        icon: <Search size={11} strokeWidth={2.2} />,
        onRemove: () => setSearch(''),
      });
    }

    if (filters.city) {
      const parts = filters.city.split(',').map(s => s.trim()).filter(Boolean);
      chips.push({
        key: 'city',
        label: 'Location',
        displayValue: parts.length > 2 ? `${parts.length} locations` : parts.join(', '),
        icon: <MapPin size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('city', ''),
      });
    }

    if (filters.industry) {
      const parts = filters.industry.split(',').map(s => s.trim()).filter(Boolean);
      chips.push({
        key: 'industry',
        label: 'Industry',
        displayValue: parts.length > 2 ? `${parts.length} industries` : parts.join(', '),
        icon: <Building2 size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('industry', ''),
      });
    }

    if (filters.employee_count) {
      const parts = filters.employee_count.split(',').map(s => s.trim()).filter(Boolean);
      chips.push({
        key: 'employee_count',
        label: 'Size',
        displayValue: parts.length > 2 ? `${parts.length} sizes` : parts.join(', '),
        icon: <Users size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('employee_count', ''),
      });
    }

    if (filters.status) {
      const parts = filters.status.split(',').map(s => s.trim().replace(/_/g, ' ')).filter(Boolean);
      chips.push({
        key: 'status',
        label: 'Status',
        displayValue: parts.length > 2 ? `${parts.length} statuses` : parts.join(', '),
        icon: <Tag size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('status', ''),
      });
    }

    if (filters.has_website) {
      chips.push({
        key: 'has_website',
        label: 'Website',
        displayValue: filters.has_website === 'Yes' ? 'Has Website' : 'No Website',
        icon: <Globe size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('has_website', ''),
      });
    }

    if (filters.has_email) {
      chips.push({
        key: 'has_email',
        label: 'Email',
        displayValue: filters.has_email === 'Yes' ? 'Has Email' : 'No Email',
        icon: <Mail size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('has_email', ''),
      });
    }

    if (filters.has_dm) {
      chips.push({
        key: 'has_dm',
        label: 'Leader',
        displayValue: filters.has_dm === 'Yes' ? 'Has Decision Maker' : 'No Decision Maker',
        icon: <UserCheck size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('has_dm', ''),
      });
    }

    if (filters.has_phone) {
      chips.push({
        key: 'has_phone',
        label: 'Phone',
        displayValue: filters.has_phone === 'Yes' ? 'Has Phone' : 'No Phone',
        icon: <Phone size={11} strokeWidth={2.2} />,
        onRemove: () => updateFilter('has_phone', ''),
      });
    }

    return chips;
  }, [search, filters, setSearch, updateFilter]);

  return (
    <div className="pipeline-control-panel" ref={toolbarRef}>
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
                <option value="Demo_Scheduled">4. Demo</option>
                <option value="Proposal">5. Proposal</option>
                <option value="Negotiation">6. Negotiation</option>
                <option value="Closed_Won">7. Closed Won</option>
                <option value="Closed_Lost">8. Closed Lost</option>
              </select>

              <button
                type="button"
                onClick={() => setSelectedRecordIds([])}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.72rem' }}
                title="Deselect all"
              >
                Clear
              </button>
            </div>
          )}
        </div>

        {/* Primary Action Buttons */}
        <div className="table-actions" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <div className="enrichment-btn-group">
            <button
              type="button"
              className="enrich-btn enrich-apollo-btn"
              id="btnEnrichApollo"
              onClick={() => openModal('enrich', 'apollo')}
              title="Enrich Decision Makers and B2B emails via Apollo.io"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
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

      {/* ── Tier 2: Enhanced Executive Filter Bar ── */}
      <div className="pipeline-filter-bar">
        <div className="filter-bar-header">
          <div className="filter-bar-title-wrap">
            <Filter size={13} strokeWidth={2.4} />
            <span>Filters</span>
          </div>
          {activeFilterCount > 0 && (
            <span className="filter-bar-count-badge">
              {activeFilterCount}
            </span>
          )}
        </div>

        <div className="filter-divider" />

        {/* Primary Filter Popovers */}
        <div className="filter-controls-list">
          {/* 1. Location (City) */}
          <FilterPopover
            id="city"
            label="Location"
            icon={MapPin}
            value={filters.city}
            onChange={(val) => updateFilter('city', val)}
            options={cityOptions}
            isMulti={true}
            searchable={cityOptions.length > 5}
            searchPlaceholder="Search locations..."
            isOpen={openDropdown === 'city'}
            onToggle={() => toggleDropdown('city')}
            onClose={closeDropdown}
          />

          {/* 2. Industry */}
          <FilterPopover
            id="industry"
            label="Industry"
            icon={Building2}
            value={filters.industry}
            onChange={(val) => updateFilter('industry', val)}
            options={industryOptions}
            isMulti={true}
            searchable={industryOptions.length > 5}
            searchPlaceholder="Search industries..."
            isOpen={openDropdown === 'industry'}
            onToggle={() => toggleDropdown('industry')}
            onClose={closeDropdown}
          />

          {/* 3. Company Size (Multiple Choice) */}
          <FilterPopover
            id="employees"
            label="Company Size"
            icon={Users}
            value={filters.employee_count}
            onChange={(val) => updateFilter('employee_count', val)}
            options={employeeOptions}
            isMulti={true}
            isOpen={openDropdown === 'employees'}
            onToggle={() => toggleDropdown('employees')}
            onClose={closeDropdown}
          />

          {/* 4. Lead Status */}
          <FilterPopover
            id="status"
            label="Lead Status"
            icon={Tag}
            value={filters.status}
            onChange={(val) => updateFilter('status', val)}
            options={statusOptions}
            isMulti={true}
            isOpen={openDropdown === 'status'}
            onToggle={() => toggleDropdown('status')}
            onClose={closeDropdown}
          />

          <div className="filter-mini-divider" />

          {/* 5. Website Channel */}
          <ChannelFilterPopover
            id="has_website"
            label="Website"
            icon={Globe}
            value={filters.has_website}
            onChange={(val) => updateFilter('has_website', val)}
            yesCount={stats?.with_website}
            totalCount={stats?.total}
            isOpen={openDropdown === 'has_website'}
            onToggle={() => toggleDropdown('has_website')}
            onClose={closeDropdown}
          />

          {/* 6. Email Channel */}
          <ChannelFilterPopover
            id="has_email"
            label="Email"
            icon={Mail}
            value={filters.has_email}
            onChange={(val) => updateFilter('has_email', val)}
            yesCount={stats?.with_email}
            totalCount={stats?.total}
            isOpen={openDropdown === 'has_email'}
            onToggle={() => toggleDropdown('has_email')}
            onClose={closeDropdown}
          />

          {/* 7. Decision Maker */}
          <ChannelFilterPopover
            id="has_dm"
            label="Leader"
            icon={UserCheck}
            value={filters.has_dm}
            onChange={(val) => updateFilter('has_dm', val)}
            yesCount={stats?.with_dm}
            totalCount={stats?.total}
            isOpen={openDropdown === 'has_dm'}
            onToggle={() => toggleDropdown('has_dm')}
            onClose={closeDropdown}
            alignRight={true}
          />

          {/* 8. Phone Channel */}
          <ChannelFilterPopover
            id="has_phone"
            label="Phone"
            icon={Phone}
            value={filters.has_phone}
            onChange={(val) => updateFilter('has_phone', val)}
            yesCount={stats?.with_phone}
            totalCount={stats?.total}
            isOpen={openDropdown === 'has_phone'}
            onToggle={() => toggleDropdown('has_phone')}
            onClose={closeDropdown}
            alignRight={true}
          />
        </div>

        {/* Global Reset Button in header row */}
        {activeFilterCount > 0 && (
          <button
            type="button"
            className="btn-reset-filters-subtle"
            onClick={resetFilters}
            title="Reset all filters"
          >
            <RotateCcw size={11} strokeWidth={2.4} />
            <span>Reset</span>
          </button>
        )}
      </div>

      {/* ── Tier 3: Active Filter Chips Tray (when filters applied) ── */}
      {activeChips.length > 0 && (
        <div className="active-filters-tray">
          <div className="active-filters-label">
            <SlidersHorizontal size={12} strokeWidth={2.2} />
            <span>Applied Filters ({activeChips.length}):</span>
          </div>

          <div className="active-chips-scroll">
            {activeChips.map((chip) => (
              <span key={chip.key} className="active-filter-chip">
                <span className="chip-icon">{chip.icon}</span>
                <span className="chip-key">{chip.label}:</span>
                <span className="chip-val" title={chip.displayValue}>{chip.displayValue}</span>
                <button
                  type="button"
                  className="chip-remove-btn"
                  onClick={chip.onRemove}
                  title={`Remove ${chip.label} filter`}
                >
                  <X size={11} strokeWidth={2.5} />
                </button>
              </span>
            ))}
          </div>

          <button
            type="button"
            className="btn-clear-all-chips"
            onClick={resetFilters}
            title="Clear all filters"
          >
            <RotateCcw size={11} strokeWidth={2.4} />
            <span>Clear All</span>
          </button>
        </div>
      )}
    </div>
  );
}
