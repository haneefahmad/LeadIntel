import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../api/client';
import { useApp } from './AppContext';

const PipelineContext = createContext(null);

const DEFAULT_FILTERS = {
  city: '',
  industry: '',
  status: '',
  has_website: '',
  has_email: '',
  has_dm: '',
  has_phone: '',
};

export function PipelineProvider({ children }) {
  const { activeSheet, fieldCatalog, showToast } = useApp();

  const [records, setRecords] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(false);

  // View Mode: 'table' | 'kanban'
  const [viewMode, setViewMode] = useState(() => {
    return localStorage.getItem('leadintel_view_mode') || 'table';
  });

  const updateViewMode = useCallback((mode) => {
    setViewMode(mode);
    localStorage.setItem('leadintel_view_mode', mode);
  }, []);

  // Columns selection state with localStorage persistence
  const [selectedColumns, setSelectedColumns] = useState(() => {
    try {
      const saved = localStorage.getItem('leadintel_selected_columns');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn('Failed to parse saved columns:', e);
    }
    return [];
  });

  // Persist selected columns to localStorage
  const updateSelectedColumns = useCallback((cols) => {
    const safeCols = Array.isArray(cols) ? cols : [];
    setSelectedColumns(safeCols);
    try {
      localStorage.setItem('leadintel_selected_columns', JSON.stringify(safeCols));
    } catch (e) {
      console.warn('Failed to save columns to localStorage:', e);
    }
  }, []);

  // When fieldCatalog loads, if selectedColumns is empty, set default preset
  useEffect(() => {
    if (fieldCatalog && (!Array.isArray(selectedColumns) || selectedColumns.length === 0)) {
      const defaultCols = fieldCatalog.presets?.executive?.columns || [
        "Record_ID", "Company_Name", "Primary_Industry", "State", "City",
        "Website_URL", "Primary_Phone", "WhatsApp_Number", "General_Email",
        "DM_Full_Name", "DM_Title", "DM_Direct_Email", "Lead_Status"
      ];
      updateSelectedColumns(defaultCols);
    }
  }, [fieldCatalog, selectedColumns, updateSelectedColumns]);

  // Compute active filter condition count
  const activeFilterCount = useMemo(() => {
    let count = search.trim() ? 1 : 0;
    Object.values(filters).forEach(val => {
      if (val) count += 1;
    });
    return count;
  }, [search, filters]);

  // Load records from API
  const fetchRecords = useCallback(async () => {
    if (!activeSheet) return;
    try {
      setLoading(true);
      const params = {
        sheet: activeSheet,
        q: search.trim(),
        city: filters.city,
        industry: filters.industry,
        status: filters.status,
        has_website: filters.has_website,
        has_email: filters.has_email,
        has_dm: filters.has_dm,
        has_phone: filters.has_phone,
        page: currentPage,
        limit: limit,
      };

      const res = await api.getRecords(params);
      setRecords(res.records || []);
      setTotalRecords(res.total || 0);
      setTotalPages(res.pages || Math.max(1, Math.ceil((res.total || 0) / limit)));
    } catch (err) {
      console.error('Failed to fetch records:', err);
      showToast(`Failed to load leads: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [activeSheet, search, filters, currentPage, limit, showToast]);

  // Refetch when sheet, search, filters, page, or limit changes
  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  // Reset to page 1 on active sheet change
  useEffect(() => {
    setCurrentPage(1);
  }, [activeSheet]);

  // Set single filter
  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  }, []);

  // Reset all filters
  const resetFilters = useCallback(() => {
    setSearch('');
    setFilters(DEFAULT_FILTERS);
    setCurrentPage(1);
    showToast('All search and table filters reset', 'info');
  }, [showToast]);

  // KPI card quick click-to-filter
  const applyKpiFilter = useCallback((filterType) => {
    if (filterType === 'all') {
      resetFilters();
      return;
    }

    setFilters(prev => {
      const next = { ...DEFAULT_FILTERS };
      if (filterType === 'dm') {
        next.has_dm = prev.has_dm === 'Yes' ? '' : 'Yes';
      } else if (filterType === 'email') {
        next.has_email = prev.has_email === 'Yes' ? '' : 'Yes';
      } else if (filterType === 'phone') {
        next.has_phone = prev.has_phone === 'Yes' ? '' : 'Yes';
      } else if (filterType === 'website') {
        next.has_website = prev.has_website === 'Yes' ? '' : 'Yes';
      }
      return next;
    });
    setCurrentPage(1);
  }, [resetFilters]);

  // Update a single record in-place after edit/suppression
  const updateLocalRecord = useCallback((updatedRecord) => {
    if (!updatedRecord || !updatedRecord.Record_ID) return;
    setRecords(prev => prev.map(r => r.Record_ID === updatedRecord.Record_ID ? updatedRecord : r));
  }, []);

  const value = {
    records,
    totalRecords,
    totalPages,
    currentPage,
    setCurrentPage,
    limit,
    setLimit,
    search,
    setSearch: (s) => { setSearch(s); setCurrentPage(1); },
    filters,
    updateFilter,
    resetFilters,
    activeFilterCount,
    applyKpiFilter,
    loading,
    fetchRecords,
    reloadRecords: fetchRecords,
    selectedColumns,
    setSelectedColumns: updateSelectedColumns,
    updateLocalRecord,
    viewMode,
    setViewMode: updateViewMode,
  };

  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>;
}

export function usePipeline() {
  const context = useContext(PipelineContext);
  if (!context) {
    throw new Error('usePipeline must be used within a PipelineProvider');
  }
  return context;
}
