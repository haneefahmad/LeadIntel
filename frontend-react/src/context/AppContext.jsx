import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  // Navigation
  const [activeTab, setActiveTab] = useState('database'); // 'database' (Companies) | 'mission' | 'analytics' | 'history'

  // Theme State ('dark' | 'light')
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('leadintel_theme');
    if (saved) return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('leadintel_theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  // Sheets & Configuration
  const [activeSheet, setActiveSheet] = useState('');
  const [sheets, setSheets] = useState([]);
  const [systemConfig, setSystemConfig] = useState(null);
  const [fieldCatalog, setFieldCatalog] = useState(null);
  const [stats, setStats] = useState(null);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Selected records for multi-row operations / enrichment
  const [selectedRecordIds, setSelectedRecordIds] = useState([]);

  // Modals state
  const [modalState, setModalState] = useState({
    sheets: false,
    settings: false,
    deleteSheet: null,
    columns: false,
    dossier: null, // record_id string or null
    enrich: null, // engine string: 'apify' | 'apollo' or null
  });

  // Toast notifications
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Modal helpers
  const openModal = useCallback((name, payload = true) => {
    setModalState(prev => ({ ...prev, [name]: payload }));
  }, []);

  const closeModal = useCallback((name) => {
    setModalState(prev => ({ ...prev, [name]: null }));
  }, []);

  // Load Initial Metadata
  const loadInitialData = useCallback(async () => {
    try {
      setLoadingInitial(true);
      const [configData, sheetsData, fieldsData] = await Promise.all([
        api.getConfig(),
        api.getSheets(),
        api.getFields(),
      ]);

      setSystemConfig(configData);
      setFieldCatalog(fieldsData);
      setSheets(sheetsData.sheets || []);

      const active = sheetsData.active_sheet || (sheetsData.sheets?.[0]?.name) || 'MasterDB';
      setActiveSheet(active);

      // Load stats for the active sheet
      const statsData = await api.getStats(active);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load initial application state:', err);
      showToast(`Initialization failed: ${err.message}`, 'error');
    } finally {
      setLoadingInitial(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Switch Active Sheet
  const switchSheet = useCallback(async (sheetName) => {
    if (!sheetName || sheetName === activeSheet) return;
    try {
      await api.selectSheet(sheetName);
      setActiveSheet(sheetName);
      setSelectedRecordIds([]);

      // Refresh sheets & stats
      const [sheetsData, statsData] = await Promise.all([
        api.getSheets(),
        api.getStats(sheetName),
      ]);
      setSheets(sheetsData.sheets || []);
      setStats(statsData);
      showToast(`Switched active campaign to "${sheetName}"`, 'success');
    } catch (err) {
      console.error('Failed to switch sheet:', err);
      showToast(`Failed to switch sheet: ${err.message}`, 'error');
    }
  }, [activeSheet, showToast]);

  // Refresh Stats
  const reloadStats = useCallback(async (sheet = activeSheet) => {
    try {
      const statsData = await api.getStats(sheet);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to reload stats:', err);
    }
  }, [activeSheet]);

  // Refresh Sheets list
  const reloadSheets = useCallback(async () => {
    try {
      const sheetsData = await api.getSheets();
      setSheets(sheetsData.sheets || []);
    } catch (err) {
      console.error('Failed to reload sheets:', err);
    }
  }, []);

  // Delete Custom Sheet
  const deleteSheet = useCallback(async (sheetName) => {
    if (!sheetName) return;
    if (sheetName === 'MasterDB') {
      showToast('Cannot delete default MasterDB sheet.', 'error');
      return;
    }
    const confirmed = window.confirm(`Are you sure you want to permanently delete sheet "${sheetName}" and all its records?`);
    if (!confirmed) return;

    try {
      await api.deleteSheet(sheetName);
      showToast(`Sheet "${sheetName}" deleted successfully!`, 'success');
      await switchSheet('MasterDB');
    } catch (err) {
      console.error('Failed to delete sheet:', err);
      showToast(`Delete failed: ${err.message}`, 'error');
    }
  }, [showToast, switchSheet]);

  // Server State
  const [isServerStopped, setIsServerStopped] = useState(false);

  const stopServer = useCallback(async () => {
    try {
      showToast('Shutting down server...', 'info');
      await api.shutdownServer();
    } catch (err) {
      console.log('Shutdown request dispatched:', err);
    } finally {
      setIsServerStopped(true);
    }
  }, [showToast]);

  const value = {
    activeTab,
    setActiveTab,
    theme,
    setTheme,
    toggleTheme,
    activeSheet,
    sheets,
    systemConfig,
    fieldCatalog,
    stats,
    loadingInitial,
    selectedRecordIds,
    setSelectedRecordIds,
    modalState,
    openModal,
    closeModal,
    toasts,
    showToast,
    removeToast,
    switchSheet,
    deleteSheet,
    reloadStats,
    reloadSheets,
    isServerStopped,
    setIsServerStopped,
    stopServer,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
