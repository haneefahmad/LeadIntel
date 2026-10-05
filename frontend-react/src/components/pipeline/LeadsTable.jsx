import React, { useMemo, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { Eye, Loader2 } from 'lucide-react';

function cleanDomain(url) {
  if (!url) return '';
  return url.replace(/^https?:\/\//i, '').replace(/^www\./i, '').replace(/\/.*$/, '');
}

function getInitials(name) {
  if (!name) return 'DM';
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getStatusClass(status) {
  const st = (status || 'New').trim();
  switch (st) {
    case 'New': return 'badge-blue';
    case 'Contacted': return 'badge-purple';
    case 'Qualified': return 'badge-emerald';
    case 'Proposal':
    case 'Proposal_Sent': return 'badge-cyan';
    case 'Negotiation': return 'badge-amber';
    case 'Closed_Won':
    case 'Won': return 'badge-emerald';
    case 'Closed_Lost':
    case 'Lost': return 'badge-rose';
    case 'Disqualified': return 'badge-rose';
    default: return 'badge-gray';
  }
}

function getOutreachClass(val) {
  const st = (val || 'Not_Started').trim();
  if (st === 'Replied' || st === 'Meeting_Scheduled') return 'badge-emerald';
  if (st === 'In_Progress' || st === 'Contacted' || st === 'Email_Sent') return 'badge-cyan';
  if (st === 'Bounced' || st === 'Do_Not_Contact') return 'badge-rose';
  return 'badge-gray';
}

function InlineStatusSelect({ record, activeSheet, onUpdate, showToast }) {
  const currentVal = record.Lead_Status || record.Status || 'New';
  const [val, setVal] = useState(currentVal);
  const [saving, setSaving] = useState(false);

  const handleChange = async (e) => {
    e.stopPropagation();
    const newStatus = e.target.value;
    setVal(newStatus);
    try {
      setSaving(true);
      const res = await api.updateRecord(record.Record_ID, { status: newStatus }, activeSheet);
      if (res?.record) {
        onUpdate(res.record);
        showToast(`${record.Company_Name || 'Lead'} marked as ${newStatus}`, 'success');
      }
    } catch (err) {
      showToast(`Status update failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div onClick={(e) => e.stopPropagation()} style={{ display: 'inline-flex', alignItems: 'center' }}>
      <select
        value={val}
        onChange={handleChange}
        disabled={saving}
        className={`inline-crm-select ${getStatusClass(val)}`}
        title="Quick update lifecycle status"
      >
        <option value="New">New</option>
        <option value="Contacted">Contacted</option>
        <option value="In_Conversation">In Conversation</option>
        <option value="Qualified">Qualified</option>
        <option value="Proposal_Sent">Proposal</option>
        <option value="Meeting_Scheduled">Meeting</option>
        <option value="Negotiation">Negotiation</option>
        <option value="Won">Won</option>
        <option value="Lost">Lost</option>
        <option value="Disqualified">Disqualified</option>
      </select>
    </div>
  );
}

function InlineOutreachSelect({ record, activeSheet, onUpdate, showToast }) {
  const currentVal = record.Outreach_Status || 'Not_Started';
  const [val, setVal] = useState(currentVal);
  const [saving, setSaving] = useState(false);

  const handleChange = async (e) => {
    e.stopPropagation();
    const newStatus = e.target.value;
    setVal(newStatus);
    try {
      setSaving(true);
      const res = await api.updateRecord(record.Record_ID, { outreach_status: newStatus }, activeSheet);
      if (res?.record) {
        onUpdate(res.record);
        showToast(`${record.Company_Name || 'Lead'} outreach set to ${newStatus.replace(/_/g, ' ')}`, 'success');
      }
    } catch (err) {
      showToast(`Outreach update failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div onClick={(e) => e.stopPropagation()} style={{ display: 'inline-flex', alignItems: 'center' }}>
      <select
        value={val}
        onChange={handleChange}
        disabled={saving}
        className={`inline-crm-select ${getOutreachClass(val)}`}
        title="Quick update outreach status"
      >
        <option value="Not_Started">Not Started</option>
        <option value="Queued">Queued</option>
        <option value="Email_Sent">Email Sent</option>
        <option value="Phone_Called">Phone Called</option>
        <option value="In_Discussion">In Discussion</option>
        <option value="Replied">Replied</option>
        <option value="Meeting_Scheduled">Meeting</option>
        <option value="Bounced">Bounced</option>
        <option value="Do_Not_Contact">Do Not Contact</option>
      </select>
    </div>
  );
}

function InlineStageSelect({ record, activeSheet, onUpdate, showToast }) {
  const currentVal = record.Pipeline_Stage || 'Identified';
  const [val, setVal] = useState(currentVal);
  const [saving, setSaving] = useState(false);

  const handleChange = async (e) => {
    e.stopPropagation();
    const newStage = e.target.value;
    setVal(newStage);
    try {
      setSaving(true);
      const res = await api.updateRecord(record.Record_ID, { pipeline_stage: newStage }, activeSheet);
      if (res?.record) {
        onUpdate(res.record);
        showToast(`${record.Company_Name || 'Lead'} moved to ${newStage.replace(/_/g, ' ')}`, 'success');
      }
    } catch (err) {
      showToast(`Stage update failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div onClick={(e) => e.stopPropagation()} style={{ display: 'inline-flex', alignItems: 'center' }}>
      <select
        value={val}
        onChange={handleChange}
        disabled={saving}
        className="inline-crm-select badge-indigo"
        title="Quick advance pipeline stage"
      >
        <option value="Identified">1. Identified</option>
        <option value="Contacted">2. Contacted</option>
        <option value="Qualified">3. Qualified</option>
        <option value="Demo_Scheduled">4. Demo</option>
        <option value="Proposal">5. Proposal</option>
        <option value="Negotiation">6. Negotiation</option>
        <option value="Closed_Won">7. Closed Won</option>
        <option value="Closed_Lost">8. Closed Lost</option>
      </select>
    </div>
  );
}

export default function LeadsTable() {
  const { fieldCatalog, openModal, selectedRecordIds, setSelectedRecordIds, activeSheet, showToast } = useApp();
  const { records, loading, selectedColumns, updateLocalRecord } = usePipeline();

  const columnsMap = useMemo(() => {
    const map = {};
    (fieldCatalog?.fields || []).forEach(f => {
      map[f.id] = f;
    });
    return map;
  }, [fieldCatalog]);

  const displayCols = useMemo(() => {
    if (selectedColumns && selectedColumns.length > 0) {
      return selectedColumns;
    }
    return [
      'Record_ID',
      'Company_Name',
      'Company_Type',
      'Primary_Industry',
      'Country',
      'City',
      'Primary_Phone',
      'WhatsApp_Number',
      'Website_URL',
      'DM_Full_Name',
      'DM_Title',
      'DM_Direct_Email',
      'DM_Direct_Phone',
      'DM_LinkedIn_URL',
      'Outreach_Status',
      'Lead_Status',
    ];
  }, [selectedColumns]);

  const isAllSelected = records.length > 0 && records.every(r => selectedRecordIds.includes(r.Record_ID));
  const isSomeSelected = records.some(r => selectedRecordIds.includes(r.Record_ID));

  const toggleSelectAll = () => {
    if (isAllSelected) {
      const pageIds = new Set(records.map(r => r.Record_ID));
      setSelectedRecordIds(prev => prev.filter(id => !pageIds.has(id)));
    } else {
      const currentIds = records.map(r => r.Record_ID);
      setSelectedRecordIds(prev => Array.from(new Set([...prev, ...currentIds])));
    }
  };

  const toggleSelectRow = (recordId) => {
    setSelectedRecordIds(prev => 
      prev.includes(recordId) 
        ? prev.filter(id => id !== recordId) 
        : [...prev, recordId]
    );
  };

  const renderCell = (colId, r) => {
    const val = r[colId];

    switch (colId) {
      case 'Record_ID':
        return <span className="mono-badge">{val || '—'}</span>;

      case 'Company_Name':
      case 'Company_Name_EN': {
        const cName = r.Company_Name || r.Company_Name_EN || 'Untitled Organization';
        const cSub = r.Primary_Industry || r.Industry_Primary || r.Company_Type || '';
        return (
          <div 
            className="company-cell"
            onClick={(e) => {
              e.stopPropagation();
              openModal('dossier', r.Record_ID);
            }}
            style={{ cursor: 'pointer' }}
          >
            <span className="company-name">{cName}</span>
            {cSub && <span className="company-sub">{cSub}</span>}
          </div>
        );
      }

      case 'Country':
      case 'City':
        return val ? <span className="badge badge-gray">{val}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Company_Type':
      case 'Primary_Industry':
      case 'Industry_Primary':
        return val ? <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{val}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Primary_Phone':
      case 'Phone_Primary':
        return val ? (
          <a href={`tel:${val}`} className="cell-link-phone" onClick={(e) => e.stopPropagation()}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
            </svg>
            <span>{val}</span>
          </a>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'WhatsApp_Number':
        return val ? (
          <a 
            href={`https://wa.me/${val.replace(/[^0-9]/g, '')}`} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="badge badge-emerald" 
            onClick={(e) => e.stopPropagation()}
          >
            💬 {val}
          </a>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Website_URL': {
        if (!val) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
        const cleanUrl = val.startsWith('http') ? val : `https://${val}`;
        return (
          <a href={cleanUrl} target="_blank" rel="noopener noreferrer" className="cell-link-web" onClick={(e) => e.stopPropagation()}>
            {cleanDomain(val)} ↗
          </a>
        );
      }

      case 'Company_LinkedIn':
      case 'Company_LinkedIn_URL':
        return val ? (
          <a href={val} target="_blank" rel="noopener noreferrer" className="cell-link-web" onClick={(e) => e.stopPropagation()} style={{ color: '#0284c7' }}>
            Company ↗
          </a>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'DM_Full_Name':
      case 'DM1_Full_Name': {
        const dmName = r.DM_Full_Name || r.DM1_Full_Name || '';
        const dmTitle = r.DM_Title || r.DM1_Title || '';
        if (!dmName) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
        return (
          <div className="dm-cell">
            <div className="dm-avatar">{getInitials(dmName)}</div>
            <div className="dm-meta">
              <span className="dm-name">{dmName}</span>
              {dmTitle && <span className="dm-title" title={dmTitle}>{dmTitle}</span>}
            </div>
          </div>
        );
      }

      case 'DM_Title':
      case 'DM1_Title':
        return val ? <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{val}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'DM_Direct_Email':
      case 'DM1_Email':
        return val ? (
          <a href={`mailto:${val}`} className="email-verified-pill" onClick={(e) => e.stopPropagation()} title={`Email ${val}`}>
            <span className="dot"></span>
            <span>{val}</span>
          </a>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'General_Email':
      case 'Email_General':
        return val ? (
          <a href={`mailto:${val}`} style={{ color: 'var(--text-secondary)', textDecoration: 'underline', fontSize: '0.78rem' }} onClick={(e) => e.stopPropagation()}>
            {val}
          </a>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'DM_Direct_Phone':
      case 'DM1_Phone':
        return val ? (
          <a href={`tel:${val}`} className="cell-link-phone" onClick={(e) => e.stopPropagation()}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
            </svg>
            <span>{val}</span>
          </a>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'DM_LinkedIn_URL':
      case 'DM1_LinkedIn_URL':
        return val ? (
          <a href={val} target="_blank" rel="noopener noreferrer" className="cell-link-web" onClick={(e) => e.stopPropagation()} style={{ color: '#0284c7' }}>
            LinkedIn ↗
          </a>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Google_Rating': {
        const revs = r.Reviews_Count != null ? r.Reviews_Count : r.Google_Reviews_Count;
        return val ? (
          <span className="cell-rating-badge">
            ★ {val}{revs != null && <span className="cell-reviews-sub">({Number(revs).toLocaleString()})</span>}
          </span>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>;
      }

      case 'Outreach_Status':
        return (
          <InlineOutreachSelect 
            record={r} 
            activeSheet={activeSheet} 
            onUpdate={updateLocalRecord} 
            showToast={showToast} 
          />
        );

      case 'Lead_Status':
      case 'Status':
        return (
          <InlineStatusSelect 
            record={r} 
            activeSheet={activeSheet} 
            onUpdate={updateLocalRecord} 
            showToast={showToast} 
          />
        );

      case 'Pipeline_Stage':
        return (
          <InlineStageSelect 
            record={r} 
            activeSheet={activeSheet} 
            onUpdate={updateLocalRecord} 
            showToast={showToast} 
          />
        );

      case 'Deal_Value':
      case 'Deal_Value_SAR':
        return val != null && val !== '' ? <span className="mono-currency">${Number(val).toLocaleString()}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Date_Added':
      case 'Last_Updated':
        return val ? <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{String(val)}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Employee_Count':
      case 'Employee_Count_Est': {
        if (val == null || val === '') return <span style={{ color: 'var(--text-muted)' }}>—</span>;
        const cleanStr = String(val).replace(/,/g, '').trim();
        const num = Number(cleanStr);
        const formatted = !isNaN(num) && num > 0 ? num.toLocaleString() : String(val);
        return (
          <span className="badge badge-gray" style={{ fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span>👥</span>
            <span>{formatted}</span>
          </span>
        );
      }

      default:
        return val != null && val !== '' ? <span style={{ fontSize: '0.8rem' }}>{String(val)}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;
    }
  };

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            {/* Select All Checkbox */}
            <th style={{ width: 38, textAlign: 'center', verticalAlign: 'middle' }}>
              <input
                type="checkbox"
                checked={isAllSelected}
                ref={el => { if (el) el.indeterminate = isSomeSelected && !isAllSelected; }}
                onChange={toggleSelectAll}
                style={{ cursor: 'pointer' }}
                title="Select all visible leads"
              />
            </th>

            {/* Dynamic Columns */}
            {displayCols.map(colId => {
              const colDef = columnsMap[colId];
              const label = colDef?.label || colId.replace(/_/g, ' ');
              return (
                <th key={colId} className={`th-${colId}`}>
                  <span>{label}</span>
                </th>
              );
            })}

            {/* Row Action Header */}
            <th style={{ width: 60, textAlign: 'center' }}>
              Action
            </th>
          </tr>
        </thead>

        <tbody id="masterTableBody">
          {loading ? (
            <tr>
              <td colSpan={displayCols.length + 2} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                Loading records...
              </td>
            </tr>
          ) : records.length === 0 ? (
            <tr>
              <td colSpan={displayCols.length + 2} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                No leads found matching your search. Try adjusting the filters or running a new scrape.
              </td>
            </tr>
          ) : (
            records.map(record => {
              const isChecked = selectedRecordIds.includes(record.Record_ID);
              return (
                <tr 
                  key={record.Record_ID} 
                  className={`clickable-row ${isChecked ? 'selected-row' : ''}`}
                  onClick={() => openModal('dossier', record.Record_ID)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Row Select Checkbox */}
                  <td style={{ width: 38, textAlign: 'center', verticalAlign: 'middle' }} onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleSelectRow(record.Record_ID)}
                      style={{ cursor: 'pointer' }}
                    />
                  </td>

                  {/* Dynamic Data Cells */}
                  {displayCols.map(colId => (
                    <td key={colId} className={`cell-${colId}`}>
                      {renderCell(colId, record)}
                    </td>
                  ))}

                  {/* Action Button */}
                  <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      className="btn-ghost"
                      style={{ padding: '4px 8px', borderRadius: 4, cursor: 'pointer', background: 'transparent', border: 'none', color: 'var(--text-muted)' }}
                      onClick={() => openModal('dossier', record.Record_ID)}
                      title="Open Lead Dossier"
                    >
                      <Eye size={14} />
                    </button>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
