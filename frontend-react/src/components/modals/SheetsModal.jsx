import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../api/client';
import { 
  X, 
  Layers, 
  Plus, 
  Trash2, 
  Check, 
  Database, 
  AlertTriangle, 
  Loader2 
} from 'lucide-react';

export default function SheetsModal() {
  const { modalState, closeModal, activeSheet, sheets, switchSheet, reloadSheets, showToast } = useApp();
  const isOpen = modalState.sheets;

  const [newSheetName, setNewSheetName] = useState('');
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  if (!isOpen) return null;

  // Handle Create Sheet
  const handleCreate = async (e) => {
    e.preventDefault();
    const cleanName = newSheetName.trim().replace(/[^a-zA-Z0-9_-]/g, '');
    if (!cleanName) {
      showToast('Please enter a valid sheet name (letters, numbers, hyphens)', 'warning');
      return;
    }

    try {
      setCreating(true);
      await api.createSheet(cleanName, true);
      showToast(`Campaign sheet "${cleanName}" created and activated!`, 'success');
      setNewSheetName('');
      await reloadSheets();
      await switchSheet(cleanName);
      closeModal('sheets');
    } catch (err) {
      console.error('Failed to create sheet:', err);
      showToast(`Creation failed: ${err.message}`, 'error');
    } finally {
      setCreating(false);
    }
  };

  // Handle Delete Confirmation
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      setDeleting(true);
      await api.deleteSheet(deleteTarget.name);
      showToast(`Campaign sheet "${deleteTarget.name}" deleted.`, 'success');
      setDeleteTarget(null);
      await reloadSheets();
      if (activeSheet === deleteTarget.name) {
        await switchSheet('MasterDB');
      }
    } catch (err) {
      console.error('Failed to delete sheet:', err);
      showToast(`Delete failed: ${err.message}`, 'error');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <div className="modal-overlay" onClick={() => closeModal('sheets')}>
        <div 
          className="modal-card modal-dialog-medium sheets-modal" 
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
        >
          {/* Header */}
          <div className="modal-header">
            <div className="modal-title-group">
              <div className="modal-icon-badge">
                <Layers size={18} />
              </div>
              <div>
                <div className="modal-headline">Manage Campaign Sheets</div>
                <div className="modal-subheadline">
                  Organize leads into isolated campaigns, target markets, or client databases.
                </div>
              </div>
            </div>

            <button
              type="button"
              className="modal-close-btn"
              onClick={() => closeModal('sheets')}
              aria-label="Close modal"
            >
              <X size={18} />
            </button>
          </div>

          {/* Body */}
          <div className="modal-body sheets-modal-body">
            {/* Create New Sheet Form */}
            <form onSubmit={handleCreate} className="create-sheet-box">
              <label className="form-label" style={{ fontWeight: 600 }}>Create New Campaign Sheet</label>
              <div className="create-sheet-input-row">
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. MiamiStaffing, DubaiRealEstate, Q4Logistics"
                  value={newSheetName}
                  onChange={(e) => setNewSheetName(e.target.value)}
                />
                <button
                  type="submit"
                  className="action-btn btn-primary"
                  disabled={creating || !newSheetName.trim()}
                >
                  {creating ? <Loader2 size={14} className="spin-animate" /> : <Plus size={14} />}
                  <span>Create & Activate</span>
                </button>
              </div>
            </form>

            {/* Existing Sheets List */}
            <div className="sheets-list-section">
              <div className="sheets-list-header">
                <span className="section-label">Active & Saved Campaigns ({sheets.length})</span>
              </div>

              <div className="sheets-cards-grid">
                {sheets.map(sh => {
                  const isActive = sh.name === activeSheet;
                  return (
                    <div 
                      key={sh.name} 
                      className={`sheet-item-card ${isActive ? 'is-active-sheet' : ''}`}
                    >
                      <div className="sheet-card-info">
                        <div className="sheet-card-title-row">
                          <strong className="sheet-card-name">{sh.name}</strong>
                          {isActive && <span className="active-tag">Active</span>}
                          {sh.is_default && <span className="default-tag">Master</span>}
                        </div>
                        <div className="sheet-card-meta">
                          <span>{(sh.records_count || 0).toLocaleString()} leads</span>
                          {sh.has_xlsx && <span>• XLSX Ready</span>}
                        </div>
                      </div>

                      <div className="sheet-card-actions">
                        {!isActive ? (
                          <button
                            type="button"
                            className="btn-sheet-switch"
                            onClick={() => {
                              switchSheet(sh.name);
                              closeModal('sheets');
                            }}
                          >
                            Switch
                          </button>
                        ) : (
                          <span className="current-active-label">
                            <Check size={14} /> Current
                          </span>
                        )}

                        {!sh.is_default && (
                          <button
                            type="button"
                            className="btn-sheet-delete"
                            onClick={() => setDeleteTarget(sh)}
                            title={`Delete ${sh.name}`}
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Sub-Modal */}
      {deleteTarget && (
        <div className="modal-backdrop sub-backdrop" style={{ zIndex: 1100 }}>
          <div className="delete-modal-card">
            <div className="modal-header">
              <div className="modal-title" style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={18} />
                <span style={{ fontWeight: 600 }}>Delete Campaign Sheet</span>
              </div>
              <button 
                type="button" 
                className="modal-close-btn" 
                onClick={() => setDeleteTarget(null)}
              >
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: '0.9rem', lineHeight: 1.5, marginBottom: 12 }}>
                Are you sure you want to permanently delete the sheet <strong>{deleteTarget.name}</strong>?
              </p>
              <div className="warning-notice-box">
                ⚠️ <strong>Warning:</strong> This will erase the SQLite database, Excel workbook, and all saved leads for this campaign. This action cannot be undone.
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
                <button
                  type="button"
                  className="action-btn btn-secondary"
                  onClick={() => setDeleteTarget(null)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="action-btn"
                  style={{ background: '#ef4444', color: '#fff', borderColor: '#dc2626' }}
                  onClick={handleDeleteConfirm}
                  disabled={deleting}
                >
                  {deleting ? 'Deleting...' : 'Permanently Delete'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
