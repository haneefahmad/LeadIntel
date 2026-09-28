import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../api/client';
import { Database, Key, CheckCircle2, AlertCircle, Loader2, Zap, Sun, Moon } from 'lucide-react';
import DatabaseConfigCard from '../settings/DatabaseConfigCard';

export default function SettingsModal() {
  const { modalState, closeModal, showToast, stopServer, reloadStats, theme, setTheme } = useApp();
  const isOpen = modalState.settings;

  const [activeTab, setActiveTab] = useState('database'); // 'database' | 'appearance' | 'api'
  const [settings, setSettings] = useState({
    apify_token: '',
    apollo_api_key: '',
  });

  const [masked, setMasked] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testingApollo, setTestingApollo] = useState(false);
  const [apolloTestResult, setApolloTestResult] = useState(null);
  const [confirmingStop, setConfirmingStop] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    async function loadSettings() {
      try {
        setLoading(true);
        const data = await api.getSettings();
        setMasked(data);
      } catch (err) {
        console.error('Failed to load settings:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
    setApolloTestResult(null);
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTestApollo = async () => {
    try {
      setTestingApollo(true);
      setApolloTestResult(null);
      const res = await api.testApollo({
        apollo_api_key: settings.apollo_api_key.trim() || undefined,
      });
      setApolloTestResult(res);
      if (res.success) {
        showToast('Apollo connected & verified successfully!', 'success');
      } else {
        showToast(res.message || 'Apollo test failed.', 'error');
      }
    } catch (err) {
      setApolloTestResult({ success: false, message: err.message });
      showToast(`Apollo test failed: ${err.message}`, 'error');
    } finally {
      setTestingApollo(false);
    }
  };

  const handleSaveApiKeys = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {};
      if (settings.apify_token.trim()) payload.apify_token = settings.apify_token.trim();
      if (settings.apollo_api_key.trim()) payload.apollo_api_key = settings.apollo_api_key.trim();

      await api.saveSettings(payload);
      showToast('API credentials saved successfully!', 'success');
      closeModal('settings');
    } catch (err) {
      console.error('Failed to save settings:', err);
      showToast(`Save failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  const isApolloConfigured = Boolean(masked?.apollo_configured);

  return (
    <div className="modal-overlay" onClick={() => closeModal('settings')}>
      <div 
        className="panel-card" 
        style={{ maxWidth: 640, width: '100%', animation: 'modalFadeIn 0.18s ease-out', maxHeight: '90vh', overflowY: 'auto' }} 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header" style={{ padding: '0 0 12px 0', marginBottom: 14 }}>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>System Settings & Integrations</h3>
          <button 
            type="button" 
            className="modal-close-btn" 
            onClick={() => closeModal('settings')} 
            aria-label="Close"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Modal Navigation Tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 18, borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
          <button
            type="button"
            className={`nav-btn ${activeTab === 'database' ? 'active' : ''}`}
            onClick={() => setActiveTab('database')}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Database size={14} />
            <span>Universal Database</span>
          </button>
          <button
            type="button"
            className={`nav-btn ${activeTab === 'appearance' ? 'active' : ''}`}
            onClick={() => setActiveTab('appearance')}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Sun size={14} />
            <span>Appearance</span>
          </button>
          <button
            type="button"
            className={`nav-btn ${activeTab === 'api' ? 'active' : ''}`}
            onClick={() => setActiveTab('api')}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Key size={14} />
            <span>API Credentials</span>
          </button>
        </div>

        {activeTab === 'database' && (
          <div>
            <DatabaseConfigCard onDatabaseChanged={reloadStats} />
          </div>
        )}

        {activeTab === 'appearance' && (
          <div style={{ padding: '4px 0 16px 0' }}>
            <h4 style={{ margin: '0 0 4px 0', fontSize: '0.92rem', fontWeight: 600, color: 'var(--text)' }}>
              Color Theme Preference
            </h4>
            <p style={{ margin: '0 0 16px 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Choose your interface color style. Your selection is automatically saved in your browser.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
              {/* Dark Theme */}
              <div
                onClick={() => setTheme('dark')}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setTheme('dark')}
                style={{
                  cursor: 'pointer',
                  padding: '14px 16px',
                  borderRadius: 'var(--radius)',
                  border: theme === 'dark' ? '2px solid #6366f1' : '1px solid var(--border)',
                  background: theme === 'dark' ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  background: '#09090b',
                  border: '1px solid #27272a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fbbf24',
                  flexShrink: 0,
                }}>
                  <Moon size={18} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text)' }}>Dark Theme</span>
                    {theme === 'dark' && <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>Active</span>}
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>High-contrast dark palette</span>
                </div>
              </div>

              {/* Light Theme */}
              <div
                onClick={() => setTheme('light')}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setTheme('light')}
                style={{
                  cursor: 'pointer',
                  padding: '14px 16px',
                  borderRadius: 'var(--radius)',
                  border: theme === 'light' ? '2px solid #6366f1' : '1px solid var(--border)',
                  background: theme === 'light' ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  background: '#ffffff',
                  border: '1px solid #cbd5e1',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#d97706',
                  flexShrink: 0,
                }}>
                  <Sun size={18} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text)' }}>Light Theme</span>
                    {theme === 'light' && <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>Active</span>}
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>High-visibility light palette</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'api' && (
          <form onSubmit={handleSaveApiKeys}>
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span>Apify API Token</span>
                <span className={`badge ${masked?.apify_configured ? 'badge-emerald' : 'badge-amber'}`} style={{ fontSize: '0.68rem' }}>
                  {masked?.apify_configured ? `Configured (${masked.apify_masked})` : 'Missing'}
                </span>
              </label>
              <input
                type="password"
                className="form-input"
                placeholder={masked?.apify_configured ? 'Enter new token to overwrite' : 'apify_api_...'}
                value={settings.apify_token}
                onChange={(e) => setSettings(s => ({ ...s, apify_token: e.target.value }))}
              />
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                Required for Google Places lead scraper. Get at <a href="https://console.apify.com/account/integrations" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text)', textDecoration: 'underline' }}>console.apify.com</a>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <label className="form-label" style={{ margin: 0 }}>
                  <span>Apollo.io API Key</span>
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className={`badge ${isApolloConfigured ? 'badge-emerald' : (masked?.apollo_status && masked.apollo_status !== 'Ready' ? 'badge-amber' : 'badge-gray')}`} style={{ fontSize: '0.68rem' }}>
                    {isApolloConfigured ? `Configured (${masked?.apollo_masked})` : 'Not Configured'}
                  </span>
                  <button
                    type="button"
                    className="action-btn btn-secondary"
                    style={{ fontSize: '0.7rem', padding: '3px 8px', height: 24 }}
                    onClick={handleTestApollo}
                    disabled={testingApollo}
                  >
                    {testingApollo ? 'Testing...' : '⚡ Test Connection'}
                  </button>
                </div>
              </div>
              <input
                type="password"
                className="form-input"
                placeholder={isApolloConfigured ? 'Enter new API key to overwrite' : 'Paste Apollo API Key'}
                value={settings.apollo_api_key}
                onChange={(e) => {
                  setSettings(s => ({ ...s, apollo_api_key: e.target.value }));
                  setApolloTestResult(null);
                }}
              />
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                Used for direct verified email & phone lookup at Apollo.io.
              </div>

              {apolloTestResult && (
                <div 
                  style={{ 
                    marginTop: 8, 
                    padding: '6px 10px', 
                    borderRadius: 6, 
                    fontSize: '0.73rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    backgroundColor: apolloTestResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: apolloTestResult.success ? '#10b981' : '#ef4444',
                    border: `1px solid ${apolloTestResult.success ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`
                  }}
                >
                  <span>{apolloTestResult.success ? '✓' : '✗'}</span>
                  <span>{apolloTestResult.message}</span>
                </div>
              )}
            </div>

            {/* Server Process Control */}
            <div 
              style={{ 
                marginBottom: 20, 
                padding: '12px 14px', 
                borderRadius: 8, 
                backgroundColor: 'rgba(255, 255, 255, 0.02)', 
                border: '1px solid rgba(255, 255, 255, 0.08)' 
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }}></span>
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#ffffff' }}>Server Status: Active</span>
                </div>
                <span className="badge badge-gray" style={{ fontSize: '0.68rem', fontFamily: 'monospace' }}>Port 8000</span>
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '0 0 10px 0', lineHeight: 1.4 }}>
                FastAPI backend is serving API requests and SSE pipelines on <code style={{ color: '#818cf8' }}>http://localhost:8000</code>.
              </p>
              {!confirmingStop ? (
                <button
                  type="button"
                  className="action-btn btn-danger"
                  style={{ fontSize: '0.75rem', padding: '5px 10px', height: 'auto' }}
                  onClick={() => setConfirmingStop(true)}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
                    <line x1="12" y1="2" x2="12" y2="12" />
                  </svg>
                  <span>Stop Backend Server</span>
                </button>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 500 }}>Confirm shutdown?</span>
                  <button
                    type="button"
                    className="action-btn btn-secondary"
                    style={{ fontSize: '0.7rem', padding: '3px 8px', height: 26 }}
                    onClick={() => setConfirmingStop(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="action-btn btn-danger"
                    style={{ fontSize: '0.7rem', padding: '3px 10px', height: 26, backgroundColor: '#ef4444', color: '#fff' }}
                    onClick={() => {
                      closeModal('settings');
                      stopServer();
                    }}
                  >
                    Yes, Terminate Process
                  </button>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button 
                type="button" 
                className="action-btn btn-secondary" 
                onClick={() => closeModal('settings')}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="action-btn btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
