import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { 
  X, 
  Sparkles, 
  Zap, 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  Loader2, 
  Terminal, 
  Play, 
  ArrowRight 
} from 'lucide-react';

export default function EnrichModal() {
  const { modalState, closeModal, activeSheet, selectedRecordIds, reloadStats, showToast } = useApp();
  const { fetchRecords } = usePipeline();
  const engine = modalState.enrich; // 'apify' | 'apollo'

  const [preview, setPreview] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(true);
  const [starting, setStarting] = useState(false);
  const [apifyRunId, setApifyRunId] = useState('');

  // Active Job & Live Streaming
  const [activeJob, setActiveJob] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStage, setJobStage] = useState('');
  const [jobLogs, setJobLogs] = useState([]);
  const [jobFinished, setJobFinished] = useState(false);

  const eventSourceRef = useRef(null);
  const logsEndRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [jobLogs]);

  // Clean up SSE stream on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Fetch Preview
  const fetchPreview = useCallback(async () => {
    if (!engine) return;
    try {
      setLoadingPreview(true);
      const res = await api.previewEnrichment({
        sheet_name: activeSheet,
        engine: engine,
        selected_ids: selectedRecordIds.length > 0 ? selectedRecordIds : null,
      });
      setPreview(res);
    } catch (err) {
      console.error('Failed to load enrichment preview:', err);
      showToast(`Preview failed: ${err.message}`, 'error');
    } finally {
      setLoadingPreview(false);
    }
  }, [engine, activeSheet, selectedRecordIds, showToast]);

  useEffect(() => {
    fetchPreview();
  }, [fetchPreview]);

  if (!engine) return null;

  // Start Job
  const handleStart = async () => {
    try {
      setStarting(true);
      const payload = {
        sheet_name: activeSheet,
        engine: engine,
        selected_ids: selectedRecordIds.length > 0 ? selectedRecordIds : null,
        run_id: apifyRunId.trim() || null,
        added_by: 'Lead Intelligence Dashboard',
      };

      const res = await api.startEnrichment(payload);
      const jobId = res.job_id;
      setActiveJob(jobId);
      setJobStage('Initializing enrichment mission...');
      setJobLogs([`Mission launched (Job ID: ${jobId})`]);
      setJobFinished(false);

      // Connect to SSE stream
      const es = new EventSource(`/api/scrape/stream/${jobId}`);
      eventSourceRef.current = es;

      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.stage) setJobStage(data.stage);
          if (data.total_steps > 0) {
            const pct = Math.min(100, Math.round((data.completed_steps / data.total_steps) * 100));
            setJobProgress(pct);
          }

          if (data.new_logs && data.new_logs.length > 0) {
            setJobLogs(prev => [
              ...prev,
              ...data.new_logs.map(l => typeof l === 'string' ? l : `${l.time || ''} ${l.message || ''}`),
            ]);
          }

          if (data.finished || data.status === 'completed' || data.status === 'failed') {
            setJobFinished(true);
            es.close();
            reloadStats();
            fetchRecords();
            if (data.status === 'completed') {
              showToast(`Enrichment complete! Updated ${data.total_saved || 0} leads.`, 'success');
            } else if (data.status === 'failed') {
              showToast('Enrichment job terminated with notice.', 'warning');
            }
          }
        } catch (err) {
          console.error('SSE parse error:', err);
        }
      };

      es.onerror = () => {
        setJobFinished(true);
        es.close();
      };
    } catch (err) {
      console.error('Failed to start enrichment:', err);
      showToast(`Failed to start: ${err.message}`, 'error');
    } finally {
      setStarting(false);
    }
  };

  const getEngineMeta = () => {
    if (engine === 'apify') {
      return {
        title: 'Enrich Apify',
        subtitle: 'Google Maps Places & Website Contact Crawler',
        icon: <Sparkles size={18} className="engine-icon apify" />,
        badge: 'Google Places & Web Scanner',
      };
    }
    return {
      title: 'Enrich Apollo',
      subtitle: 'Apollo.io Verified Direct Emails & Firmographics',
      icon: <Zap size={18} className="engine-icon apollo" />,
      badge: 'Apollo.io B2B Intelligence',
    };
  };

  const meta = getEngineMeta();

  return (
    <div className="modal-overlay" onClick={() => !activeJob && closeModal('enrich')}>
      <div 
        className="modal-card modal-dialog-medium enrich-modal" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge">
              {meta.icon}
            </div>
            <div>
              <div className="modal-headline">{meta.title}</div>
              <div className="modal-subheadline">{meta.subtitle}</div>
            </div>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={() => closeModal('enrich')}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body enrich-body">
          {/* Active Job Progress View */}
          {activeJob ? (
            <div className="enrich-live-view">
              <div className="enrich-status-header">
                <div className="live-status-pill">
                  <span className="live-pulse-dot"></span>
                  <span>{jobFinished ? 'Mission Complete' : 'Enriching Leads in Background...'}</span>
                </div>
                <div className="live-progress-pct">{jobProgress}%</div>
              </div>

              {/* Progress Bar */}
              <div className="progress-track">
                <div 
                  className="progress-fill" 
                  style={{ width: `${jobProgress}%` }}
                />
              </div>

              <div className="progress-stage-label">{jobStage}</div>

              {/* Console Logs */}
              <div className="enrich-terminal-console">
                <div className="console-bar">
                  <Terminal size={12} />
                  <span>Execution Stream Console</span>
                </div>
                <div className="console-stream">
                  {jobLogs.map((log, idx) => (
                    <div key={idx} className="console-line">{log}</div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </div>

              {jobFinished && (
                <div className="modal-finished-actions">
                  <button
                    type="button"
                    className="action-btn btn-primary"
                    onClick={() => closeModal('enrich')}
                  >
                    Close & View Enriched Leads
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Pre-execution Preview View */
            <div className="enrich-preview-view">
              {loadingPreview ? (
                <div className="dossier-loading">
                  <Loader2 size={24} className="spin-animate" />
                  <span>Calculating eligible leads and cost estimate...</span>
                </div>
              ) : (
                <>
                  {/* Scope Summary Box */}
                  <div className="preview-scope-card">
                    <div className="scope-headline">
                      Target Campaign: <strong>{activeSheet}</strong>
                    </div>
                    <div className="scope-stats-row">
                      <div className="scope-stat-item">
                        <span className="scope-stat-label">Eligible Leads:</span>
                        <strong className="scope-stat-val emerald">
                          {preview?.eligible_count || 0}
                        </strong>
                        <span className="scope-stat-sub">
                          {selectedRecordIds.length > 0 
                            ? `(out of ${selectedRecordIds.length} selected)` 
                            : `(out of ${preview?.total_records_in_sheet || 0} in sheet)`}
                        </span>
                      </div>
                      <div className="scope-stat-item">
                        <span className="scope-stat-label">Est. Cost:</span>
                        <strong className="scope-stat-val">
                          {preview?.cost_estimate || '$0.00'}
                        </strong>
                      </div>
                    </div>
                  </div>

                  {/* Non-Destructive Guarantee */}
                  <div className="guarantee-box">
                    <ShieldCheck size={16} className="guarantee-icon" />
                    <div>
                      <strong>Strict Non-Destructive Update Guarantee:</strong>
                      <p>
                        This mission will <em>only</em> populate empty or missing fields. Existing phone numbers, websites, verified emails, and CRM statuses are 100% preserved.
                      </p>
                    </div>
                  </div>

                  {/* Target Fields Pill List */}
                  <div className="fields-target-section">
                    <span className="section-label">Fields Enriched by this Provider:</span>
                    <div className="fields-chip-grid">
                      {(preview?.fields_to_fill || []).map(f => (
                        <span key={f} className="field-chip">
                          <CheckCircle2 size={12} className="chip-icon" />
                          <span>{f.replace(/_/g, ' ')}</span>
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Apify Run ID attach input (optional) */}
                  {engine === 'apify' && (
                    <div className="form-group" style={{ marginTop: 12 }}>
                      <label className="form-label" style={{ fontSize: '0.78rem' }}>
                        Optional: Attach to existing Apify Run ID or leave blank for automated execution
                      </label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. XvwvVt1uuxDrsqrjB (leave empty for automatic scrape)"
                        value={apifyRunId}
                        onChange={(e) => setApifyRunId(e.target.value)}
                        style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
                      />
                    </div>
                  )}

                  {/* Configuration error if missing API key */}
                  {!preview?.is_configured && (
                    <div className="config-warning-box">
                      <AlertCircle size={15} />
                      <span>{preview?.config_error || 'Provider credentials not configured.'}</span>
                    </div>
                  )}

                  {/* Modal Action Buttons */}
                  <div className="modal-actions-footer">
                    <button
                      type="button"
                      className="action-btn btn-secondary"
                      onClick={() => closeModal('enrich')}
                    >
                      Cancel
                    </button>

                    <button
                      type="button"
                      className="action-btn btn-primary"
                      onClick={handleStart}
                      disabled={starting || !preview?.is_configured || (preview?.eligible_count === 0)}
                    >
                      {starting ? (
                        <>
                          <Loader2 size={14} className="spin-animate" />
                          <span>Launching Mission...</span>
                        </>
                      ) : (
                        <>
                          <Play size={14} />
                          <span>Start Enrichment ({preview?.eligible_count || 0} Leads)</span>
                        </>
                      )}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
