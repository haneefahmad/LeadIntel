import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../api/client';
import { FileText, RotateCcw, Clock, DollarSign, CheckCircle2, Loader2 } from 'lucide-react';

export default function RunLogsView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getLogs();
      setLogs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="tab-view-container active-view">
      {/* Header */}
      <div className="view-panel-header">
        <div className="view-title-group">
          <div className="panel-badge-pill">
            <FileText size={13} />
            <span>Audit Trail & Mission History</span>
          </div>
          <h1 className="panel-main-title">Execution Run Logs</h1>
          <p className="panel-subtitle">
            Complete audit trail of all automated scraping missions, lead counts, and API costs.
          </p>
        </div>

        <div className="view-actions-group">
          <button
            type="button"
            className="action-btn btn-secondary"
            onClick={fetchLogs}
            disabled={loading}
          >
            <RotateCcw size={14} className={loading ? 'spin-animate' : ''} />
            <span>Refresh Logs</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="panel-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Date / Time</th>
                <th>Target Region</th>
                <th>Industry</th>
                <th style={{ textAlign: 'right' }}>Scraped</th>
                <th style={{ textAlign: 'right' }}>Added to Sheet</th>
                <th style={{ textAlign: 'right' }}>Cost (USD)</th>
                <th>Run Type</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="table-empty-row">
                    <div className="table-loading-spinner">
                      <Loader2 size={18} className="spin-animate" />
                      <span>Loading execution history...</span>
                    </div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="table-empty-row">
                    <div className="table-empty-state">
                      <Clock size={32} className="empty-icon" />
                      <div className="empty-title">No execution runs recorded yet</div>
                      <div className="empty-subtitle">
                        Launch a mission from Mission Control to record execution history.
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                logs.map(log => (
                  <tr key={log.Run_ID || log.run_id || Math.random()}>
                    <td>
                      <strong style={{ fontFamily: 'monospace', color: 'var(--text)' }}>
                        {log.Run_ID || log.run_id}
                      </strong>
                    </td>
                    <td>
                      <span>{log.Date || log.date}</span>
                      <span className="cell-muted" style={{ marginLeft: 6 }}>
                        {log.Time_Started || log.time_started}
                      </span>
                    </td>
                    <td>{log.City_Target || log.city || '—'}</td>
                    <td>{log.Industry || log.industry || '—'}</td>
                    <td style={{ textAlign: 'right' }}>
                      <strong>{(log.Records_Returned || log.records_returned || 0).toLocaleString()}</strong>
                    </td>
                    <td style={{ textAlign: 'right', color: '#10b981' }}>
                      +{(log.Added_to_Master || log.added_to_master || 0).toLocaleString()}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                      ${Number(log.Cost_USD || log.cost_usd || 0).toFixed(2)}
                    </td>
                    <td>
                      <span className="badge badge-subtle">
                        {log.Run_Type || log.run_type || 'Scrape'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
