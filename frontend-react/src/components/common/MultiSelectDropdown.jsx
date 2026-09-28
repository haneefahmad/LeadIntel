import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Search, ChevronDown, Plus, X } from 'lucide-react';

/**
 * Universal Multi-Select Dropdown Component
 * Supports search filtering, Select All / Clear, custom item addition,
 * dynamic badges, keyboard navigation, and selected item pills.
 */
export default function MultiSelectDropdown({
  id,
  label,
  placeholder = 'Select options...',
  searchPlaceholder = 'Search...',
  items = [], // array of string or { id, label, sub }
  selected = [], // array of ids/strings
  onChange,
  allowCustom = false,
  onAddCustom,
  disabled = false,
  disabledMessage = '',
  maxDisplayPills = 15,
  renderPresetChips = null,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const wrapperRef = useRef(null);
  const searchInputRef = useRef(null);

  // Normalize items to { id, label, sub }
  const normalizedItems = useMemo(() => {
    return items.map((item) => {
      if (typeof item === 'string') {
        return { id: item, label: item, sub: '' };
      }
      return {
        id: item.id || item.value || item.name || item.label,
        label: item.label || item.name || item.id,
        sub: item.sub || item.state || item.country || '',
      };
    });
  }, [items]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      // Auto focus search input when opened
      setTimeout(() => {
        if (searchInputRef.current) {
          searchInputRef.current.focus();
        }
      }, 50);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Filter items based on search query
  const filteredItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return normalizedItems;
    return normalizedItems.filter((item) => {
      return (
        item.label.toLowerCase().includes(q) ||
        (item.sub && item.sub.toLowerCase().includes(q))
      );
    });
  }, [normalizedItems, searchQuery]);

  // Check if search query matches existing item or is novel
  const canAddCustom = useMemo(() => {
    if (!allowCustom) return false;
    const q = searchQuery.trim();
    if (!q) return false;
    const match = normalizedItems.some(
      (item) => item.label.toLowerCase() === q.toLowerCase()
    );
    return !match;
  }, [allowCustom, searchQuery, normalizedItems]);

  // Toggle single item
  const handleToggle = (itemId) => {
    if (selected.includes(itemId)) {
      onChange(selected.filter((id) => id !== itemId));
    } else {
      onChange([...selected, itemId]);
    }
  };

  // Select all currently filtered items
  const handleSelectAll = () => {
    const idsToAdd = filteredItems.map((i) => i.id);
    const newSet = new Set([...selected, ...idsToAdd]);
    onChange(Array.from(newSet));
  };

  // Clear all selections
  const handleClear = () => {
    onChange([]);
  };

  // Remove a single pill
  const handleRemovePill = (itemId, e) => {
    e.stopPropagation();
    onChange(selected.filter((id) => id !== itemId));
  };

  // Add custom item
  const handleAddCustom = () => {
    const q = searchQuery.trim();
    if (!q) return;
    if (onAddCustom) {
      onAddCustom(q);
    } else {
      onChange([...selected, q]);
    }
    setSearchQuery('');
  };

  // Trigger title text
  const triggerTitle = useMemo(() => {
    if (disabled && disabledMessage) return disabledMessage;
    if (selected.length === 0) return placeholder;
    if (selected.length === 1) return selected[0];
    if (selected.length === 2) return `${selected[0]}, ${selected[1]}`;
    return `${selected[0]}, ${selected[1]} (+${selected.length - 2} more)`;
  }, [selected, placeholder, disabled, disabledMessage]);

  return (
    <div className="form-group" style={{ marginBottom: 14 }}>
      {label && (
        <label className="form-label" htmlFor={id ? `btn-${id}` : undefined}>
          {label}
        </label>
      )}

      <div className="custom-multiselect-wrapper" ref={wrapperRef} id={id}>
        {/* Trigger Button */}
        <button
          type="button"
          id={id ? `btn-${id}` : undefined}
          className={`multiselect-trigger ${isOpen ? 'active' : ''}`}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          aria-haspopup="true"
          aria-expanded={isOpen}
          style={{ opacity: disabled ? 0.6 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
        >
          <div className="multiselect-trigger-content">
            <span className="multiselect-title" title={triggerTitle}>
              {triggerTitle}
            </span>
            <span className="multiselect-badge">
              {selected.length === 0
                ? (disabled ? '—' : 'All')
                : `${selected.length} selected`}
            </span>
          </div>
          <ChevronDown size={14} className="chevron-icon" />
        </button>

        {/* Dropdown Panel */}
        {isOpen && !disabled && (
          <div className="multiselect-panel">
            {/* Search Box */}
            <div className="multiselect-search-box">
              <Search size={14} />
              <input
                ref={searchInputRef}
                type="text"
                className="multiselect-search-input"
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    if (canAddCustom) handleAddCustom();
                  }
                }}
              />
            </div>

            {/* Actions Bar */}
            <div className="multiselect-actions-bar">
              <div className="multiselect-quick-actions">
                <button
                  type="button"
                  className="text-btn"
                  onClick={handleSelectAll}
                >
                  Select All
                </button>
                <span className="divider-dot">•</span>
                <button
                  type="button"
                  className="text-btn"
                  onClick={handleClear}
                >
                  Clear
                </button>
              </div>
              <span className="multiselect-status-text">
                {filteredItems.length} available
              </span>
            </div>

            {/* Custom Item Addition Row */}
            {canAddCustom && (
              <div
                className="add-custom-city-row"
                onClick={handleAddCustom}
                title={`Click to add "${searchQuery.trim()}"`}
              >
                <Plus size={12} />
                <span>
                  Add custom: "<strong>{searchQuery.trim()}</strong>"
                </span>
              </div>
            )}

            {/* Options List */}
            <div className="multiselect-options-list">
              {filteredItems.length === 0 && !canAddCustom ? (
                <div style={{ padding: '12px 14px', fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                  No matching options found
                </div>
              ) : (
                filteredItems.map((item) => {
                  const isChecked = selected.includes(item.id);
                  return (
                    <label
                      key={item.id}
                      className={`multiselect-option-item ${isChecked ? 'selected' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggle(item.id)}
                      />
                      <span>{item.label}</span>
                      {item.sub && (
                        <span className="multiselect-option-sub">
                          {item.sub}
                        </span>
                      )}
                    </label>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* Selected Pills Container */}
        {selected.length > 0 && (
          <div className="multiselect-pills-container">
            {selected.slice(0, maxDisplayPills).map((itemId) => (
              <span key={itemId} className="multiselect-pill">
                <span>{itemId}</span>
                <span
                  className="pill-remove"
                  onClick={(e) => handleRemovePill(itemId, e)}
                  title={`Remove ${itemId}`}
                >
                  <X size={11} />
                </span>
              </span>
            ))}
            {selected.length > maxDisplayPills && (
              <span className="multiselect-pill" style={{ opacity: 0.75 }}>
                +{selected.length - maxDisplayPills} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Preset Chips (e.g. Quick countries or cities) */}
      {renderPresetChips && (
        <div style={{ marginTop: 6 }}>
          {renderPresetChips}
        </div>
      )}
    </div>
  );
}
