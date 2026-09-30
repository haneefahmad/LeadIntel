import React, { useState, useMemo, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { 
  X, 
  SlidersHorizontal, 
  Search, 
  Check, 
  RotateCcw, 
  Sparkles,
  Loader2 
} from 'lucide-react';

export default function ColumnsModal() {
  const { modalState, closeModal, fieldCatalog, showToast } = useApp();
  const { selectedColumns, setSelectedColumns } = usePipeline();
  const isOpen = modalState.columns;

  const [search, setSearch] = useState('');
  const [tempSelected, setTempSelected] = useState(() => 
    Array.isArray(selectedColumns) ? selectedColumns : []
  );

  // Sync tempSelected on open
  useEffect(() => {
    if (isOpen) {
      setTempSelected(Array.isArray(selectedColumns) ? [...selectedColumns] : []);
      setSearch('');
    }
  }, [isOpen, selectedColumns]);

  const categories = Array.isArray(fieldCatalog?.categories) ? fieldCatalog.categories : [];
  const allFields = Array.isArray(fieldCatalog?.fields) ? fieldCatalog.fields : [];
  const presets = (fieldCatalog?.presets && typeof fieldCatalog.presets === 'object') ? fieldCatalog.presets : {};

  // Safe selected array
  const safeSelected = Array.isArray(tempSelected) ? tempSelected : [];

  // Filtered fields based on search - called unconditionally before any early return
  const filteredFields = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return allFields;
    return allFields.filter(f => 
      (f && f.id && f.id.toLowerCase().includes(q)) || 
      (f && f.label && f.label.toLowerCase().includes(q)) ||
      (f && f.description && f.description.toLowerCase().includes(q))
    );
  }, [allFields, search]);

  // Group fields by category - called unconditionally before any early return
  const categorized = useMemo(() => {
    const groups = {};
    categories.forEach(cat => {
      if (cat && cat.id) groups[cat.id] = [];
    });
    filteredFields.forEach(f => {
      if (!f || !f.id) return;
      const catId = f.category || 'other';
      if (!groups[catId]) groups[catId] = [];
      groups[catId].push(f);
    });
    return groups;
  }, [categories, filteredFields]);

  // ── Early returns strictly after all hooks have been invoked ──────────────
  if (!isOpen) return null;

  // If schema is still loading
  if (!fieldCatalog || allFields.length === 0) {
    return (
      <div className="modal-overlay" onClick={() => closeModal('columns')}>
        <div className="modal-card modal-dialog-small" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <div className="modal-title-group">
              <div className="modal-icon-badge">
                <SlidersHorizontal size={18} />
              </div>
              <div className="modal-headline">Loading Column Schema...</div>
            </div>
            <button
              type="button"
              className="modal-close-btn"
              onClick={() => closeModal('columns')}
              aria-label="Close modal"
            >
              <X size={18} />
            </button>
          </div>
          <div className="modal-body" style={{ textAlign: 'center', padding: '32px 20px' }}>
            <Loader2 size={24} className="spin-animate" style={{ color: '#6366f1', margin: '0 auto 12px' }} />
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem' }}>
              Retrieving 39-column taxonomy catalog from backend...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Toggle single column
  const toggleColumn = (colId) => {
    if (!colId) return;
    setTempSelected(prev => {
      const current = Array.isArray(prev) ? prev : [];
      return current.includes(colId) 
        ? current.filter(c => c !== colId) 
        : [...current, colId];
    });
  };

  // Apply Preset
  const applyPreset = (presetKey) => {
    const preset = presets[presetKey];
    if (preset && Array.isArray(preset.columns)) {
      setTempSelected([...preset.columns]);
      showToast(`Applied "${preset.name || presetKey}" preset`, 'info');
    }
  };

  // Quick buttons
  const selectAll = () => {
    setTempSelected(allFields.map(f => f.id).filter(Boolean));
  };

  const clearAll = () => {
    setTempSelected(['Company_Name']); // Always retain company name
  };

  const resetDefault = () => {
    applyPreset('executive');
  };

  // Save & Apply
  const handleApply = () => {
    if (safeSelected.length === 0) {
      showToast('Please select at least one column to display', 'warning');
      return;
    }
    setSelectedColumns(safeSelected);
    showToast(`Updated view to ${safeSelected.length} active columns`, 'success');
    closeModal('columns');
  };

  return (
    <div className="modal-overlay" onClick={() => closeModal('columns')}>
      <div 
        className="modal-card modal-dialog-large columns-modal" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge">
              <SlidersHorizontal size={18} />
            </div>
            <div>
              <div className="modal-headline">Customize Table Columns & Export</div>
              <div className="modal-subheadline">
                Select fields for your dashboard table and live XLSX/CSV downloads.
              </div>
            </div>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={() => closeModal('columns')}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body columns-modal-body">
          {/* Campaign Presets Bar */}
          <div className="column-presets-container">
            <div className="presets-header">
              <span className="presets-title">⚡ CAMPAIGN PRESETS</span>
            </div>
            <div className="preset-buttons-grid">
              {Object.entries(presets).map(([key, p]) => (
                <button
                  key={key}
                  type="button"
                  className="preset-btn"
                  onClick={() => applyPreset(key)}
                  title={p?.description || ''}
                >
                  {p?.badge && <span className="preset-badge">{p.badge}</span>}
                  <span className="preset-name">{p?.name || key}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Quick Toolbar */}
          <div className="columns-quick-toolbar">
            <div className="search-input-wrapper" style={{ flex: 1 }}>
              <Search size={14} className="search-icon" />
              <input
                type="text"
                className="search-input"
                placeholder="Search 39 fields (e.g. Phone, LinkedIn, Decision Maker, City)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="quick-buttons-group">
              <button type="button" className="btn-micro" onClick={selectAll}>Select All</button>
              <button type="button" className="btn-micro" onClick={clearAll}>Clear All</button>
              <button type="button" className="btn-micro" onClick={resetDefault}>Reset Default</button>
            </div>
          </div>

          {/* Categorized Columns Grid */}
          <div className="columns-categories-container">
            {categories.map(cat => {
              if (!cat || !cat.id) return null;
              const catFields = categorized[cat.id] || [];
              if (catFields.length === 0) return null;

              const activeInCat = catFields.filter(f => safeSelected.includes(f.id)).length;

              return (
                <div key={cat.id} className="columns-category-card">
                  <div className="columns-category-header">
                    <div className="category-header-title">
                      <span>{cat.name || cat.id}</span>
                    </div>
                    <span className="multiselect-badge">
                      {activeInCat} / {catFields.length}
                    </span>
                  </div>
                  <div className="columns-category-grid">
                    {catFields.map(f => {
                      const isChecked = safeSelected.includes(f.id);
                      return (
                        <label 
                          key={f.id} 
                          className={`column-checkbox-item ${isChecked ? 'checked' : ''}`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => toggleColumn(f.id)}
                          />
                          <div className="col-label-text">
                            <span style={{ fontWeight: isChecked ? 600 : 400 }}>{f.label || f.id}</span>
                            {f.description && (
                              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 1 }}>
                                {f.description}
                              </div>
                            )}
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="modal-actions-footer columns-modal-footer">
          <div className="columns-selected-indicator" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            <strong style={{ color: '#818cf8' }}>{safeSelected.length}</strong> of {allFields.length} columns active
          </div>
          <div className="footer-actions-right" style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="action-btn btn-secondary"
              onClick={() => closeModal('columns')}
            >
              Cancel
            </button>
            <button
              type="button"
              className="action-btn btn-primary"
              onClick={handleApply}
            >
              Apply & Save View
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
