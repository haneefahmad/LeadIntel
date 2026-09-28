import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { Eye } from 'lucide-react';

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

function getStatusBadge(status) {
  const st = (status || 'New').trim();
  switch (st) {
    case 'New':
      return <span className="badge badge-blue">New</span>;
    case 'Contacted':
      return <span className="badge badge-purple">Contacted</span>;
    case 'Qualified':
      return <span className="badge badge-emerald">Qualified</span>;
    case 'Proposal':
    case 'Proposal_Sent':
      return <span className="badge badge-cyan">Proposal</span>;
    case 'Negotiation':
      return <span className="badge badge-amber">Negotiation</span>;
    case 'Closed_Won':
    case 'Won':
      return <span className="badge badge-emerald" style={{ background: 'rgba(16,185,129,0.25)' }}>Won</span>;
    case 'Closed_Lost':
    case 'Lost':
      return <span className="badge badge-rose">Lost</span>;
    case 'Disqualified':
      return <span className="badge badge-rose">Disqualified</span>;
    default:
      return <span className="badge badge-gray">{st.replace(/_/g, ' ')}</span>;
  }
}

function getOutreachBadge(val) {
  const st = (val || 'Not_Started').trim();
  let colorClass = 'badge-gray';
  if (st === 'Replied' || st === 'Meeting_Scheduled') colorClass = 'badge-emerald';
  else if (st === 'In_Progress' || st === 'Contacted') colorClass = 'badge-cyan';
  else if (st === 'Bounced' || st === 'Do_Not_Contact') colorClass = 'badge-rose';
  return <span className={`badge ${colorClass}`}>{st.replace(/_/g, ' ')}</span>;
}

export default function LeadsTable() {
  const { fieldCatalog, openModal, selectedRecordIds, setSelectedRecordIds } = useApp();
  const { records, loading, selectedColumns } = usePipeline();

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
        return getOutreachBadge(val);

      case 'Lead_Status':
      case 'Status':
        return getStatusBadge(val);

      case 'Pipeline_Stage':
        return val ? <span className="badge badge-indigo">{val}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Deal_Value':
      case 'Deal_Value_SAR':
        return val != null && val !== '' ? <span className="mono-currency">${Number(val).toLocaleString()}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

      case 'Date_Added':
      case 'Last_Updated':
        return val ? <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{String(val)}</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>;

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
