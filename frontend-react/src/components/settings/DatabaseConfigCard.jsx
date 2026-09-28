import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { useApp } from '../../context/AppContext';
import { 
  Database, 
  Server, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  RefreshCw, 
  HardDrive, 
  Shield, 
  ExternalLink,
  ChevronRight,
  RotateCcw
} from 'lucide-react';

export default function DatabaseConfigCard({ onDatabaseChanged }) {
  const { showToast, reloadStats } = useApp();

  const [dbConfig, setDbConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  // Form State
  const [provider, setProvider] = useState('postgresql'); // 'sqlite' | 'postgresql' | 'mysql' | 'custom'
  const [inputMode, setInputMode] = useState('fields'); // 'fields' | 'url'
  
  const [fields, setFields] = useState({
    host: 'localhost',
    port: '5432',
    database: 'leadintel',
    username: 'postgres',
    password: '',
    ssl_mode: '',
  });

  const [customUrl, setCustomUrl] = useState('');
  
  // Action States
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);

  // Load active DB config on mount
  useEffect(() => {
    loadDatabaseStatus();
  }, []);

  async function loadDatabaseStatus() {
    try {
      setLoading(true);
      const data = await api.getDatabaseConfig();
      setDbConfig(data);
      if (data.is_sqlite) {
        setProvider('sqlite');
      } else if (data.database_type === 'postgresql') {
        setProvider('postgresql');
      } else if (data.database_type === 'mysql') {
        setProvider('mysql');
      } else {
        setProvider('custom');
      }
    } catch (err) {
      console.error('Failed to load database config:', err);
    } finally {
      setLoading(false);
    }
  }

  // Handle Provider selection change
  const handleSelectProvider = (type) => {
    setProvider(type);
    setTestResult(null);
    if (type === 'postgresql') {
      setFields(f => ({ ...f, port: '5432' }));
    } else if (type === 'mysql') {
      setFields(f => ({ ...f, port: '3306' }));
    }
  };

  // Compute live connection string
  const computedUrl = () => {
    if (provider === 'sqlite') {
      return 'sqlite:///master.db (Local Embedded Storage)';
    }
    if (inputMode === 'url' || provider === 'custom') {
      return customUrl.trim();
    }
    const user = fields.username.trim();
    const pwd = fields.password ? '••••••••' : '';
    const auth = (user || pwd) ? `${user}:${pwd}@` : '';
    const host = fields.host.trim() || 'localhost';
    const port = fields.port.trim() ? `:${fields.port.trim()}` : '';
    const db = fields.database.trim() || 'leadintel';
    const ssl = fields.ssl_mode ? `?sslmode=${fields.ssl_mode}` : '';
    
    if (provider === 'postgresql') {
      return `postgresql+psycopg://${auth}${host}${port}/${db}${ssl}`;
    }
    if (provider === 'mysql') {
      return `mysql+pymysql://${auth}${host}${port}/${db}${ssl}`;
    }
    return '';
  };

  // Build actual payload for backend
  const buildPayload = () => {
    if (provider === 'sqlite') {
      return { db_type: 'sqlite' };
    }
    if (inputMode === 'url' || provider === 'custom') {
      return { database_url: customUrl.trim() };
    }
    return {
      db_type: provider,
      host: fields.host.trim(),
      port: fields.port ? parseInt(fields.port, 10) : undefined,
      database: fields.database.trim(),
      username: fields.username.trim(),
      password: fields.password,
      ssl_mode: fields.ssl_mode || undefined,
    };
  };

  // Test Database Connection
  const handleTestConnection = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const payload = buildPayload();
      const res = await api.testDatabaseConnection(payload);
      setTestResult(res);
      if (res.success) {
        showToast(res.message || 'Connection test successful!', 'success');
      } else {
        showToast(res.message || 'Connection test failed', 'error');
      }
    } catch (err) {
      setTestResult({ success: false, message: err.message });
      showToast(`Connection test failed: ${err.message}`, 'error');
    } finally {
      setTesting(false);
    }
  };

  // Save and Switch Database
  const handleSaveDatabase = async (e) => {
    e?.preventDefault();
    try {
      setSaving(true);
      setTestResult(null);
      const payload = buildPayload();
      const res = await api.saveDatabaseConfig(payload);
      showToast(res.message || 'Database connected successfully!', 'success');
      await loadDatabaseStatus();
      if (reloadStats) reloadStats();
      if (onDatabaseChanged) onDatabaseChanged();
    } catch (err) {
      console.error('Failed to save database config:', err);
      showToast(`Connection failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  // Reset to Local SQLite
  const handleResetToSqlite = async () => {
    try {
      setResetting(true);
      const res = await api.resetDatabaseToSqlite();
      showToast(res.message || 'Reset to local SQLite database.', 'info');
      setProvider('sqlite');
      setTestResult(null);
      await loadDatabaseStatus();
      if (reloadStats) reloadStats();
      if (onDatabaseChanged) onDatabaseChanged();
    } catch (err) {
      console.error('Failed to reset database:', err);
      showToast(`Reset failed: ${err.message}`, 'error');
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="panel-card" style={{ padding: 22, marginBottom: 20 }}>
      {/* Header & Status Indicator */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <Database size={17} style={{ color: '#818cf8' }} />
            <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 600, color: 'var(--text)' }}>
              Universal Database Connection
            </h3>
          </div>
          <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Connect to PostgreSQL, Supabase, Neon, AWS RDS, MySQL, MariaDB, or local SQLite.
          </p>
        </div>

        {/* Live Active Status Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {loading ? (
            <span className="badge badge-gray"><Loader2 size={11} className="spin-animate" /> Checking</span>
          ) : dbConfig?.connected ? (
            <span className="badge badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <CheckCircle2 size={12} />
              <span>{dbConfig.database_type.toUpperCase()} Connected</span>
              {dbConfig.details?.latency_ms && <span style={{ opacity: 0.8 }}>({dbConfig.details.latency_ms}ms)</span>}
            </span>
          ) : (
            <span className="badge badge-amber" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <AlertCircle size={12} /> Disconnected
            </span>
          )}
        </div>
      </div>

      {/* Active Database Details Bar */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        padding: '10px 14px', 
        borderRadius: 8, 
        backgroundColor: 'rgba(255, 255, 255, 0.03)', 
        border: '1px solid var(--border)',
        marginBottom: 20,
        fontSize: '0.78rem',
        flexWrap: 'wrap',
        gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 260 }}>
          <Server size={14} style={{ color: 'var(--text-muted)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Active Target:</span>
          <code style={{ color: '#818cf8', fontWeight: 600, fontSize: '0.76rem' }}>
            {dbConfig?.database_url_masked || 'sqlite:///master.db'}
          </code>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: 'var(--text-muted)' }}>Active Workspace Sheet: <strong>{dbConfig?.active_sheet || 'MasterDB'}</strong></span>
          {!dbConfig?.is_sqlite && (
            <button
              type="button"
              className="text-btn"
              onClick={handleResetToSqlite}
              disabled={resetting}
              style={{ color: '#f87171', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: 4 }}
              title="Disconnect from external server and revert to local SQLite master.db"
            >
              <RotateCcw size={11} />
              <span>{resetting ? 'Resetting...' : 'Revert to Local SQLite'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Provider Selector Tabs */}
      <div style={{ marginBottom: 18 }}>
        <label className="form-label" style={{ marginBottom: 8, fontSize: '0.78rem' }}>Select Database Provider</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8 }}>
          {[
            { id: 'sqlite', label: 'Local SQLite', sub: 'Embedded / Zero Setup' },
            { id: 'postgresql', label: 'PostgreSQL', sub: 'Supabase, Neon, RDS' },
            { id: 'mysql', label: 'MySQL / MariaDB', sub: 'Cloud or Local' },
            { id: 'custom', label: 'Custom URI', sub: 'MSSQL, Cockroach, etc.' },
          ].map(p => {
            const isSelected = provider === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => handleSelectProvider(p.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: 8,
                  border: isSelected ? '1px solid #818cf8' : '1px solid var(--border)',
                  backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.82rem', color: isSelected ? '#ffffff' : 'var(--text)' }}>
                  {p.label}
                </div>
                <div style={{ fontSize: '0.68rem', color: isSelected ? '#a5b4fc' : 'var(--text-muted)', marginTop: 2 }}>
                  {p.sub}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Provider Form Content */}
      {provider === 'sqlite' ? (
        <div style={{ 
          padding: 16, 
          borderRadius: 8, 
          backgroundColor: 'rgba(255, 255, 255, 0.02)', 
          border: '1px solid var(--border)',
          marginBottom: 18 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <HardDrive size={15} style={{ color: '#34d399' }} />
            <span style={{ fontWeight: 600, fontSize: '0.82rem', color: 'var(--text)' }}>
              Embedded SQLite Engine Active
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            SQLite is built into the engine with Write-Ahead Logging (WAL) enabled. Each campaign workspace corresponds to an isolated <code>.db</code> file in <code>backend/data/</code>. No database setup or server connection required.
          </p>
        </div>
      ) : (
        <div style={{ marginBottom: 18 }}>
          {/* Mode switch for Postgres/MySQL */}
          {provider !== 'custom' && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Connection Parameters</span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  type="button"
                  className={`text-btn ${inputMode === 'fields' ? 'active-text-btn' : ''}`}
                  onClick={() => setInputMode('fields')}
                  style={{ fontSize: '0.72rem', padding: '2px 8px' }}
                >
                  Structured Fields
                </button>
                <span style={{ color: 'var(--text-muted)' }}>•</span>
                <button
                  type="button"
                  className={`text-btn ${inputMode === 'url' ? 'active-text-btn' : ''}`}
                  onClick={() => setInputMode('url')}
                  style={{ fontSize: '0.72rem', padding: '2px 8px' }}
                >
                  Connection URI
                </button>
              </div>
            </div>
          )}

          {inputMode === 'fields' && provider !== 'custom' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              {/* Host */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Host / Endpoint</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="localhost or db.xyz.supabase.co"
                  value={fields.host}
                  onChange={(e) => {
                    setFields(f => ({ ...f, host: e.target.value }));
                    setTestResult(null);
                  }}
                />
              </div>

              {/* Port */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Port</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder={provider === 'postgresql' ? '5432' : '3306'}
                  value={fields.port}
                  onChange={(e) => {
                    setFields(f => ({ ...f, port: e.target.value }));
                    setTestResult(null);
                  }}
                />
              </div>

              {/* Database Name */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Database Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="leadintel"
                  value={fields.database}
                  onChange={(e) => {
                    setFields(f => ({ ...f, database: e.target.value }));
                    setTestResult(null);
                  }}
                />
              </div>

              {/* Username */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Username</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder={provider === 'postgresql' ? 'postgres' : 'root'}
                  value={fields.username}
                  onChange={(e) => {
                    setFields(f => ({ ...f, username: e.target.value }));
                    setTestResult(null);
                  }}
                />
              </div>

              {/* Password */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Password</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Database user password"
                  value={fields.password}
                  onChange={(e) => {
                    setFields(f => ({ ...f, password: e.target.value }));
                    setTestResult(null);
                  }}
                />
              </div>

              {/* SSL Mode */}
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>SSL Mode (Optional)</label>
                <select
                  className="form-select"
                  value={fields.ssl_mode}
                  onChange={(e) => {
                    setFields(f => ({ ...f, ssl_mode: e.target.value }));
                    setTestResult(null);
                  }}
                >
                  <option value="">Default (Off / Driver default)</option>
                  <option value="require">require (Cloud SSL / Supabase / Neon)</option>
                  <option value="prefer">prefer</option>
                  <option value="disable">disable</option>
                </select>
              </div>
            </div>
          ) : (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" style={{ fontSize: '0.75rem' }}>
                Connection String URI (SQLAlchemy Format)
              </label>
              <input
                type="text"
                className="form-input"
                placeholder={
                  provider === 'postgresql'
                    ? 'postgresql+psycopg://user:password@host:5432/dbname?sslmode=require'
                    : provider === 'mysql'
                    ? 'mysql+pymysql://user:password@host:3306/dbname'
                    : 'dialect+driver://user:password@host:port/database'
                }
                value={customUrl}
                onChange={(e) => {
                  setCustomUrl(e.target.value);
                  setTestResult(null);
                }}
              />
              <span className="form-help-text" style={{ fontSize: '0.7rem' }}>
                Examples: Supabase, Neon, AWS RDS, CockroachDB, Azure Database, PlanetScale, or self-hosted servers.
              </span>
            </div>
          )}

          {/* Generated Connection String Preview */}
          <div style={{ marginTop: 12, padding: '8px 12px', borderRadius: 6, backgroundColor: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Target URI: </span>
            <code style={{ fontSize: '0.73rem', color: '#a5b4fc', wordBreak: 'break-all' }}>
              {computedUrl() || 'Incomplete parameters'}
            </code>
          </div>
        </div>
      )}

      {/* Test Connection Result Alert */}
      {testResult && (
        <div style={{
          padding: '10px 14px',
          borderRadius: 8,
          marginBottom: 16,
          fontSize: '0.76rem',
          backgroundColor: testResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${testResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          color: testResult.success ? '#34d399' : '#f87171',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          {testResult.success ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
          <div style={{ flex: 1 }}>
            <div>{testResult.message}</div>
            {testResult.details?.server_version && testResult.details.server_version !== 'Unknown' && (
              <div style={{ fontSize: '0.68rem', opacity: 0.8, marginTop: 2 }}>
                Server: {testResult.details.server_version}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, flexWrap: 'wrap' }}>
        {provider !== 'sqlite' && (
          <button
            type="button"
            className="action-btn btn-secondary"
            onClick={handleTestConnection}
            disabled={testing || saving}
            style={{ fontSize: '0.8rem', padding: '7px 14px' }}
          >
            {testing ? <Loader2 size={13} className="spin-animate" /> : <span>⚡ Test Connection</span>}
          </button>
        )}

        <button
          type="button"
          className="action-btn btn-primary"
          onClick={provider === 'sqlite' ? handleResetToSqlite : handleSaveDatabase}
          disabled={saving || testing || resetting}
          style={{ fontSize: '0.8rem', padding: '7px 16px' }}
        >
          {saving || resetting ? (
            <Loader2 size={13} className="spin-animate" />
          ) : (
            <Database size={13} />
          )}
          <span>
            {provider === 'sqlite' ? 'Use Local SQLite' : 'Save & Connect Database'}
          </span>
        </button>
      </div>
    </div>
  );
}
