import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { 
  X, 
  Building2, 
  ExternalLink, 
  Mail, 
  Phone, 
  MapPin, 
  Star, 
  User, 
  Briefcase, 
  Calendar, 
  Tag, 
  DollarSign, 
  FileText, 
  ShieldAlert, 
  Save, 
  Loader2 
} from 'lucide-react';

export default function DossierModal() {
  const { modalState, closeModal, activeSheet, showToast } = useApp();
  const { updateLocalRecord } = usePipeline();
  const recordId = modalState.dossier;

  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [suppressing, setSuppressing] = useState(false);

  // Form CRM fields
  const [form, setForm] = useState({
    status: '',
    pipeline_stage: '',
    outreach_status: '',
    assigned_to: '',
    deal_value: '',
    tags: '',
    notes: '',
    total_touches: 0,
    replies_received: 0,
    next_action_date: '',
    next_action_type: '',
  });

  // Fetch record details
  const fetchDetail = useCallback(async () => {
    if (!recordId) return;
    try {
      setLoading(true);
      const data = await api.getRecordDetail(recordId, activeSheet);
      setRecord(data);
      setForm({
        status: data.Lead_Status || 'New',
        pipeline_stage: data.Pipeline_Stage || 'Identified',
        outreach_status: data.Outreach_Status || 'Not_Started',
        assigned_to: data.Assigned_To || '',
        deal_value: data.Deal_Value != null ? data.Deal_Value : '',
        tags: data.Tags || '',
        notes: data.CRM_Notes || data.Notes || '',
        total_touches: data.Total_Touches || 0,
        replies_received: data.Replies_Received || 0,
        next_action_date: data.Next_Action_Date || '',
        next_action_type: data.Next_Action_Type || '',
      });
    } catch (err) {
      console.error('Failed to fetch lead detail:', err);
      showToast(`Failed to load dossier: ${err.message}`, 'error');
      closeModal('dossier');
    } finally {
      setLoading(false);
    }
  }, [recordId, activeSheet, showToast, closeModal]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  if (!recordId) return null;

  // Handle Save
  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        status: form.status,
        pipeline_stage: form.pipeline_stage,
        outreach_status: form.outreach_status,
        assigned_to: form.assigned_to,
        deal_value_sar: form.deal_value ? Number(form.deal_value) : null,
        tags: form.tags,
        notes: form.notes,
        total_touches: Number(form.total_touches) || 0,
        replies_received: Number(form.replies_received) || 0,
        next_action_date: form.next_action_date || null,
        next_action_type: form.next_action_type || null,
        updated_by: 'Dashboard Mini-CRM',
      };

      const res = await api.updateRecord(recordId, payload, activeSheet);
      showToast(`Lead ${recordId} updated successfully!`, 'success');
      if (res.record) {
        setRecord(res.record);
        updateLocalRecord(res.record);
      }
    } catch (err) {
      console.error('Failed to save CRM updates:', err);
      showToast(`Save failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  // Handle Compliance Suppression
  const handleSuppress = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to suppress lead ${recordId}?\n\nThis will mark the lead as Disqualified and Do_Not_Contact, and permanently register the organization to the Compliance Suppression List.`
    );
    if (!confirmed) return;

    try {
      setSuppressing(true);
      await api.suppressRecord(recordId, {
        reason: 'User Opt-out / Compliance Request via Dashboard',
        suppressed_by: 'Dashboard Mini-CRM',
        notes: `Suppressed from company dossier on ${new Date().toISOString()}`,
      }, activeSheet);

      showToast(`Lead ${recordId} suppressed and registered to compliance list.`, 'success');
      setForm(prev => ({
        ...prev,
        status: 'Disqualified',
        outreach_status: 'Do_Not_Contact',
      }));

      // Refresh record in table
      const refreshed = await api.getRecordDetail(recordId, activeSheet);
      setRecord(refreshed);
      updateLocalRecord(refreshed);
    } catch (err) {
      console.error('Failed to suppress lead:', err);
      showToast(`Suppression failed: ${err.message}`, 'error');
    } finally {
      setSuppressing(false);
    }
  };

  const companyName = record?.Company_Name || record?.Company_Name_EN || 'Company Dossier';
  const dmName = record?.DM_Full_Name || record?.DM1_Full_Name || '';
  const dmTitle = record?.DM_Title || record?.DM1_Title || '';
  const dmEmail = record?.DM_Direct_Email || record?.DM1_Email || '';
  const dmPhone = record?.DM_Direct_Phone || record?.DM1_Phone || '';
  const dmLinkedIn = record?.DM_LinkedIn_URL || record?.DM1_LinkedIn_URL || '';
  const companyLinkedIn = record?.Company_LinkedIn || record?.Company_LinkedIn_URL || '';
  const primaryPhone = record?.Primary_Phone || record?.Phone_Primary || '';
  const generalEmail = record?.General_Email || record?.Email_General || '';
  const websiteUrl = record?.Website_URL || '';
  const googleMapsUrl = record?.Google_Maps_URL || '';

  return (
    <div className="modal-overlay" onClick={() => closeModal('dossier')}>
      <div 
        className="modal-card modal-dialog-large dossier-modal" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge">
              <Building2 size={18} />
            </div>
            <div>
              <div className="modal-headline">
                <span>{companyName}</span>
                <span className="record-chip">[{recordId}]</span>
              </div>
              <div className="modal-subheadline">
                {record?.City && <span>{record.City}, </span>}
                {record?.State && <span>{record.State} • </span>}
                {record?.Primary_Industry || 'Business Lead'}
              </div>
            </div>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={() => closeModal('dossier')}
            aria-label="Close dossier"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body dossier-body">
          {loading ? (
            <div className="dossier-loading">
              <Loader2 size={24} className="spin-animate" />
              <span>Loading executive dossier...</span>
            </div>
          ) : (
            <div className="dossier-grid">
              {/* Left Column: Intelligence Dossier Cards */}
              <div className="dossier-intel-column">
                {/* Quick Actions Bar */}
                <div className="dossier-quick-actions">
                  {dmEmail && (
                    <a href={`mailto:${dmEmail}`} className="quick-action-link primary">
                      <Mail size={13} />
                      <span>Email DM</span>
                    </a>
                  )}
                  {dmPhone && (
                    <a href={`tel:${dmPhone}`} className="quick-action-link emerald">
                      <Phone size={13} />
                      <span>Call DM</span>
                    </a>
                  )}
                  {generalEmail && !dmEmail && (
                    <a href={`mailto:${generalEmail}`} className="quick-action-link">
                      <Mail size={13} />
                      <span>General Email</span>
                    </a>
                  )}
                  {primaryPhone && !dmPhone && (
                    <a href={`tel:${primaryPhone}`} className="quick-action-link">
                      <Phone size={13} />
                      <span>Call Office</span>
                    </a>
                  )}
                  {websiteUrl && (
                    <a href={websiteUrl.startsWith('http') ? websiteUrl : `https://${websiteUrl}`} target="_blank" rel="noopener noreferrer" className="quick-action-link">
                      <ExternalLink size={13} />
                      <span>Website</span>
                    </a>
                  )}
                  {dmLinkedIn && (
                    <a href={dmLinkedIn} target="_blank" rel="noopener noreferrer" className="quick-action-link linkedin">
                      <ExternalLink size={13} />
                      <span>DM LinkedIn</span>
                    </a>
                  )}
                  {companyLinkedIn && (
                    <a href={companyLinkedIn} target="_blank" rel="noopener noreferrer" className="quick-action-link linkedin">
                      <ExternalLink size={13} />
                      <span>Company LinkedIn</span>
                    </a>
                  )}
                </div>

                {/* Section 1: Decision Maker & Leadership */}
                <div className="dossier-card">
                  <div className="card-header-bar">
                    <User size={15} />
                    <span>Decision Maker & Leadership</span>
                  </div>
                  <div className="card-content-grid">
                    <div className="intel-row">
                      <span className="intel-label">Executive Name:</span>
                      <strong className="intel-val">{dmName || <span className="cell-muted">Not discovered</span>}</strong>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Job Title:</span>
                      <span className="intel-val">{dmTitle || <span className="cell-muted">—</span>}</span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Direct Email:</span>
                      <span className="intel-val">
                        {dmEmail ? <a href={`mailto:${dmEmail}`} className="intel-link">{dmEmail}</a> : <span className="cell-muted">—</span>}
                      </span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Direct Phone:</span>
                      <span className="intel-val">
                        {dmPhone ? <a href={`tel:${dmPhone}`} className="intel-link">{dmPhone}</a> : <span className="cell-muted">—</span>}
                      </span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Authority Level:</span>
                      <span className="intel-val">{record?.DM_Authority_Level || <span className="cell-muted">—</span>}</span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Email Status:</span>
                      <span className="intel-val">{record?.DM_Email_Status || <span className="cell-muted">Not verified</span>}</span>
                    </div>
                  </div>
                </div>

                {/* Section 2: Company Firmographics & Contact */}
                <div className="dossier-card">
                  <div className="card-header-bar">
                    <Briefcase size={15} />
                    <span>Company Firmographics & Presence</span>
                  </div>
                  <div className="card-content-grid">
                    <div className="intel-row">
                      <span className="intel-label">Primary Industry:</span>
                      <span className="intel-val">{record?.Primary_Industry || <span className="cell-muted">—</span>}</span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Sub-Industry:</span>
                      <span className="intel-val">{record?.Secondary_Industry || <span className="cell-muted">—</span>}</span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Company Type:</span>
                      <span className="intel-val">{record?.Company_Type || <span className="cell-muted">—</span>}</span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Employee Count:</span>
                      <span className="intel-val">{record?.Employee_Count || <span className="cell-muted">—</span>}</span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">General Email:</span>
                      <span className="intel-val">
                        {generalEmail ? <a href={`mailto:${generalEmail}`} className="intel-link">{generalEmail}</a> : <span className="cell-muted">—</span>}
                      </span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Primary Switchboard:</span>
                      <span className="intel-val">
                        {primaryPhone ? <a href={`tel:${primaryPhone}`} className="intel-link">{primaryPhone}</a> : <span className="cell-muted">—</span>}
                      </span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">WhatsApp Number:</span>
                      <span className="intel-val">{record?.WhatsApp_Number || <span className="cell-muted">—</span>}</span>
                    </div>
                    <div className="intel-row">
                      <span className="intel-label">Address:</span>
                      <span className="intel-val">{record?.Full_Address || <span className="cell-muted">—</span>}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Mini-CRM Management Form */}
              <div className="dossier-crm-column">
                <form onSubmit={handleSave} className="dossier-crm-form">
                  <div className="crm-form-header">
                    <Tag size={15} />
                    <span>Pipeline & Outreach Management</span>
                  </div>

                  {/* Pipeline Stage Stepper */}
                  <div className="form-group">
                    <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>Sales Pipeline Stage</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--accent)', fontWeight: 600 }}>
                        {form.pipeline_stage ? form.pipeline_stage.replace(/_/g, ' ') : 'Identified'}
                      </span>
                    </label>

                    {/* Visual Stage Stepper */}
                    <div className="crm-stage-stepper" style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: 4,
                      marginBottom: 8,
                    }}>
                      {[
                        { id: 'Identified', label: '1. Identified' },
                        { id: 'Contacted', label: '2. Contacted' },
                        { id: 'Qualified', label: '3. Qualified' },
                        { id: 'Proposal', label: '4. Proposal' },
                        { id: 'Negotiation', label: '5. Negotiation' },
                        { id: 'Closed_Won', label: '6. Won' },
                      ].map(stg => {
                        const isCurrent = form.pipeline_stage === stg.id || 
                          (stg.id === 'Proposal' && form.pipeline_stage === 'Proposal_Sent') ||
                          (stg.id === 'Closed_Won' && form.pipeline_stage === 'Won');

                        return (
                          <button
                            key={stg.id}
                            type="button"
                            onClick={() => setForm(f => ({ ...f, pipeline_stage: stg.id }))}
                            style={{
                              padding: '5px 4px',
                              fontSize: '0.7rem',
                              fontWeight: isCurrent ? 700 : 500,
                              borderRadius: 6,
                              border: `1px solid ${isCurrent ? 'var(--accent)' : 'var(--border)'}`,
                              background: isCurrent ? 'var(--badge-blue-bg)' : 'var(--card)',
                              color: isCurrent ? 'var(--badge-blue-text)' : 'var(--text-muted)',
                              cursor: 'pointer',
                              textAlign: 'center',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            {stg.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Lead Status & Outreach Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                    <div className="form-group">
                      <label className="form-label">Lifecycle Status</label>
                      <select
                        className="form-select"
                        value={form.status}
                        onChange={(e) => setForm(f => ({ ...f, status: e.target.value }))}
                      >
                        <option value="New">New Lead</option>
                        <option value="Contacted">Contacted</option>
                        <option value="In_Conversation">In Conversation</option>
                        <option value="Proposal_Sent">Proposal Sent</option>
                        <option value="Qualified">Qualified</option>
                        <option value="Meeting_Scheduled">Meeting</option>
                        <option value="Won">Closed / Won</option>
                        <option value="Lost">Lost</option>
                        <option value="Disqualified">Disqualified</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Outreach Cadence</label>
                      <select
                        className="form-select"
                        value={form.outreach_status}
                        onChange={(e) => setForm(f => ({ ...f, outreach_status: e.target.value }))}
                      >
                        <option value="Not_Started">Not Started</option>
                        <option value="Queued">Queued</option>
                        <option value="Email_Sent">Email Sent</option>
                        <option value="Phone_Called">Phone Called</option>
                        <option value="In_Discussion">In Discussion</option>
                        <option value="Replied">Replied</option>
                        <option value="Meeting_Scheduled">Meeting Set</option>
                        <option value="Bounced">Email Bounced</option>
                        <option value="Do_Not_Contact">Do Not Contact</option>
                      </select>
                    </div>
                  </div>

                  {/* Touchpoints Counter */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, margin: '4px 0 8px 0' }}>
                    <div style={{
                      background: 'var(--bg-subtle, rgba(0,0,0,0.02))',
                      border: '1px solid var(--border)',
                      borderRadius: 6,
                      padding: '8px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>Total Touches</span>
                        <strong style={{ fontSize: '0.92rem', color: 'var(--text)' }}>{form.total_touches || 0}</strong>
                      </div>
                      <button
                        type="button"
                        onClick={() => setForm(f => ({ ...f, total_touches: (Number(f.total_touches) || 0) + 1 }))}
                        style={{
                          fontSize: '0.68rem',
                          padding: '3px 7px',
                          borderRadius: 4,
                          border: '1px solid var(--border)',
                          background: 'var(--card)',
                          color: 'var(--text)',
                          cursor: 'pointer',
                        }}
                      >
                        + Touch
                      </button>
                    </div>

                    <div style={{
                      background: 'var(--bg-subtle, rgba(0,0,0,0.02))',
                      border: '1px solid var(--border)',
                      borderRadius: 6,
                      padding: '8px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>Replies Received</span>
                        <strong style={{ fontSize: '0.92rem', color: 'var(--badge-green-text)' }}>{form.replies_received || 0}</strong>
                      </div>
                      <button
                        type="button"
                        onClick={() => setForm(f => ({ ...f, replies_received: (Number(f.replies_received) || 0) + 1, outreach_status: 'Replied' }))}
                        style={{
                          fontSize: '0.68rem',
                          padding: '3px 7px',
                          borderRadius: 4,
                          border: '1px solid var(--border)',
                          background: 'var(--card)',
                          color: 'var(--text)',
                          cursor: 'pointer',
                        }}
                      >
                        + Reply
                      </button>
                    </div>
                  </div>

                  {/* Deal Value & SDR Assignment */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                    <div className="form-group">
                      <label className="form-label">Deal Value ($)</label>
                      <input
                        type="number"
                        step="any"
                        className="form-input"
                        placeholder="e.g. 15000"
                        value={form.deal_value}
                        onChange={(e) => setForm(f => ({ ...f, deal_value: e.target.value }))}
                      />
                      <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                        {[5000, 15000, 30000, 50000].map(amt => (
                          <button
                            key={amt}
                            type="button"
                            onClick={() => setForm(f => ({ ...f, deal_value: amt }))}
                            style={{
                              fontSize: '0.65rem',
                              padding: '1px 5px',
                              borderRadius: 3,
                              border: '1px solid var(--border)',
                              background: 'var(--bg-subtle, transparent)',
                              color: 'var(--text-secondary)',
                              cursor: 'pointer',
                            }}
                          >
                            +${amt / 1000}k
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Assigned SDR / Rep</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. Sarah Jenkins"
                        value={form.assigned_to}
                        onChange={(e) => setForm(f => ({ ...f, assigned_to: e.target.value }))}
                      />
                    </div>
                  </div>

                  {/* Next Scheduled Action */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                    <div className="form-group">
                      <label className="form-label">Next Action Date</label>
                      <input
                        type="date"
                        className="form-input"
                        value={form.next_action_date || ''}
                        onChange={(e) => setForm(f => ({ ...f, next_action_date: e.target.value }))}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Next Action Type</label>
                      <select
                        className="form-select"
                        value={form.next_action_type || ''}
                        onChange={(e) => setForm(f => ({ ...f, next_action_type: e.target.value }))}
                      >
                        <option value="">Select action...</option>
                        <option value="Follow-up Email">Follow-up Email</option>
                        <option value="Phone Call">Phone Call</option>
                        <option value="Product Demo">Product Demo</option>
                        <option value="Send Proposal">Send Proposal</option>
                        <option value="Contract Review">Contract Review</option>
                      </select>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="form-group">
                    <label className="form-label">Tags (comma separated)</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="hot-lead, saudi-vision, enterprise"
                      value={form.tags}
                      onChange={(e) => setForm(f => ({ ...f, tags: e.target.value }))}
                    />
                  </div>

                  {/* CRM Notes */}
                  <div className="form-group">
                    <label className="form-label">Internal CRM Notes</label>
                    <textarea
                      rows={3}
                      className="form-textarea"
                      placeholder="Add strategic account notes, qualification details, conversation summary..."
                      value={form.notes}
                      onChange={(e) => setForm(f => ({ ...f, notes: e.target.value }))}
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="crm-form-actions">
                    <button
                      type="button"
                      className="btn-suppress-action"
                      onClick={handleSuppress}
                      disabled={suppressing || saving}
                      title="Mark as Disqualified and register to suppression list"
                    >
                      <ShieldAlert size={14} />
                      <span>{suppressing ? 'Suppressing...' : 'Suppress Lead'}</span>
                    </button>

                    <button
                      type="submit"
                      className="btn-save-crm-action"
                      disabled={saving}
                    >
                      {saving ? (
                        <>
                          <Loader2 size={14} className="spin-animate" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <Save size={14} />
                          <span>Save Changes</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
