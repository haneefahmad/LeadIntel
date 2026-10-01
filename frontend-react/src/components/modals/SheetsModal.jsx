import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../api/client';
import { 
  X, 
  Layers, 
  Plus, 
  Trash2, 
  Check, 
  Upload, 
  FileSpreadsheet, 
  AlertTriangle, 
  Loader2,
  FileCheck,
  Info
} from 'lucide-react';

export default function SheetsModal() {
  const { modalState, closeModal, activeSheet, sheets, switchSheet, reloadSheets, showToast } = useApp();
  const isOpen = !!modalState.sheets;

  // Active tab inside modal: 'create' | 'upload'
  const [activeTab, setActiveTab] = useState('create');

  // Create Sheet State
  const [newSheetName, setNewSheetName] = useState('');
  const [creating, setCreating] = useState(false);

  // Upload Datasheet State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadSheetName, setUploadSheetName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Delete Sheet State
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (modalState.sheets && typeof modalState.sheets === 'object' && modalState.sheets.tab) {
      setActiveTab(modalState.sheets.tab);
    }
  }, [modalState.sheets]);

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

  // Handle File Selection
  const handleFileChange = (file) => {
    if (!file) return;
    const name = file.name;
    const ext = name.split('.').pop().toLowerCase();
    if (!['xlsx', 'csv', 'xls'].includes(ext)) {
      showToast('Please select a valid Excel (.xlsx, .xls) or CSV (.csv) file.', 'warning');
      return;
    }
    setUploadFile(file);

    // Auto-generate suggested sheet name from filename
    const stem = name.replace(/\.[^/.]+$/, '').replace(/[^a-zA-Z0-9_-]/g, '_');
    setUploadSheetName(stem.substring(0, 32));
  };

  // Handle Drag & Drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Handle Datasheet Upload
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      showToast('Please select a file to upload.', 'warning');
      return;
    }

    const cleanName = (uploadSheetName.trim() || uploadFile.name.replace(/\.[^/.]+$/, ''))
      .replace(/[^a-zA-Z0-9_-]/g, '_');

    try {
      setUploading(true);

      // Convert file to base64
      const reader = new FileReader();
      const base64Promise = new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result);
        reader.onerror = (error) => reject(error);
        reader.readAsDataURL(uploadFile);
      });

      const base64Data = await base64Promise;

      const payload = {
        sheet_name: cleanName,
        filename: uploadFile.name,
        file_base64: base64Data,
        set_active: true,
      };

      const res = await api.uploadSheet(payload);

      showToast(res.message || `Successfully imported ${res.rows_processed} leads into sheet "${cleanName}"!`, 'success');
      setUploadFile(null);
      setUploadSheetName('');
      await reloadSheets();
      await switchSheet(cleanName);
      closeModal('sheets');
    } catch (err) {
      console.error('Failed to upload sheet:', err);
      showToast(`Upload failed: ${err.message}`, 'error');
    } finally {
      setUploading(false);
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
          style={{ maxWidth: 660, width: '100%' }}
        >
          {/* Header */}
          <div className="modal-header">
            <div className="modal-title-group">
              <div className="modal-icon-badge">
                <Layers size={18} />
              </div>
              <div>
                <div className="modal-headline">Manage Campaign Sheets & Datasheets</div>
                <div className="modal-subheadline">
                  Switch between campaigns, create isolated sheets, or import an external Excel/CSV datasheet.
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

          {/* Tab Selector */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0 24px' }}>
            <button
              type="button"
              onClick={() => setActiveTab('create')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'create' ? '2px solid var(--accent, #6366f1)' : '2px solid transparent',
                color: activeTab === 'create' ? 'var(--text)' : 'var(--text-muted)',
                fontWeight: activeTab === 'create' ? 600 : 500,
                padding: '10px 16px',
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Plus size={14} /> Create Empty Sheet
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('upload')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'upload' ? '2px solid var(--accent, #6366f1)' : '2px solid transparent',
                color: activeTab === 'upload' ? 'var(--text)' : 'var(--text-muted)',
                fontWeight: activeTab === 'upload' ? 600 : 500,
                padding: '10px 16px',
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Upload size={14} /> Upload Datasheet (.xlsx, .csv)
            </button>
          </div>

          {/* Body */}
          <div className="modal-body sheets-modal-body" style={{ padding: '20px 24px' }}>
            {activeTab === 'create' ? (
              /* Create New Sheet Form */
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
            ) : (
              /* Upload Datasheet Form */
              <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {/* File Dropzone */}
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: `2px dashed ${dragActive ? 'var(--accent, #6366f1)' : 'var(--border)'}`,
                    borderRadius: 10,
                    padding: '24px 18px',
                    textAlign: 'center',
                    background: dragActive ? 'rgba(99, 102, 241, 0.08)' : 'var(--card-bg, rgba(255,255,255,0.02))',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    style={{ display: 'none' }}
                    onChange={(e) => handleFileChange(e.target.files?.[0])}
                  />

                  {uploadFile ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                      <FileCheck size={32} color="#10b981" />
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text)' }}>
                        {uploadFile.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {(uploadFile.size / 1024).toFixed(1)} KB • Click or drag to replace
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                      <FileSpreadsheet size={32} color="#818cf8" />
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text)' }}>
                        Click to select or drop Excel (.xlsx) / CSV file here
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Supports spreadsheets from LinkedIn, Google Maps, CRM exports, or manual lists.
                      </div>
                    </div>
                  )}
                </div>

                {/* Sheet Name Input */}
                {uploadFile && (
                  <div>
                    <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: 4, display: 'block' }}>
                      Campaign Sheet Name in Dashboard:
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Enter sheet name"
                      value={uploadSheetName}
                      onChange={(e) => setUploadSheetName(e.target.value)}
                      style={{ width: '100%', height: 38 }}
                      required
                    />
                  </div>
                )}

                {/* Auto-mapping notice */}
                <div style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 8,
                  background: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.25)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  fontSize: '0.76rem',
                  color: 'var(--text-muted)',
                  lineHeight: 1.4,
                }}>
                  <Info size={15} color="#818cf8" style={{ flexShrink: 0, marginTop: 1 }} />
                  <div>
                    <strong>Smart Auto-Mapping:</strong> Column headers like <em>Company, Website, Phone, City, Email, Decision Maker</em> are automatically mapped into our 39-column taxonomy. Once uploaded, you can view, filter, and run <strong>Enrich Apollo</strong> or <strong>Enrich Apify</strong> on this sheet anytime.
                  </div>
                </div>

                {/* Upload Button */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                  <button
                    type="submit"
                    className="action-btn btn-primary"
                    disabled={uploading || !uploadFile}
                    style={{ minWidth: 160 }}
                  >
                    {uploading ? (
                      <>
                        <Loader2 size={14} className="spin-animate" />
                        <span>Importing Leads...</span>
                      </>
                    ) : (
                      <>
                        <Upload size={14} />
                        <span>Upload & Import Sheet</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {/* Existing Sheets List */}
            <div className="sheets-list-section" style={{ marginTop: 22 }}>
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
