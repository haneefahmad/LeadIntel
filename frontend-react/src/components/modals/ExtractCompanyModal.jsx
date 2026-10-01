import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { 
  X, 
  Search, 
  Building2, 
  MapPin, 
  Globe, 
  UserCheck, 
  Mail, 
  Phone, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  ExternalLink,
  Layers
} from 'lucide-react';

export default function ExtractCompanyModal() {
  const { modalState, closeModal, activeSheet, sheets, showToast, reloadStats, openModal } = useApp();
  const { reloadRecords, setSearch } = usePipeline();

  const isOpen = !!modalState.extractCompany;

  // Form State
  const [companyName, setCompanyName] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('Saudi Arabia');
  const [domain, setDomain] = useState('');
  const [targetSheet, setTargetSheet] = useState(activeSheet || 'MasterDB');
  const [useApify, setUseApify] = useState(true);
  const [useApollo, setUseApollo] = useState(true);

  // Execution State
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSelectEngines = (engineType) => {
    if (engineType === 'both') {
      setUseApify(true);
      setUseApollo(true);
    } else if (engineType === 'apify') {
      setUseApify(true);
      setUseApollo(false);
    } else if (engineType === 'apollo') {
      setUseApify(false);
      setUseApollo(true);
    }
  };

  const handleExtract = async (e) => {
    e.preventDefault();
    if (!companyName.trim()) {
      showToast('Please enter a company name to extract.', 'warning');
      return;
    }

    const engines = [];
    if (useApify) engines.push('apify');
    if (useApollo) engines.push('apollo');

    if (engines.length === 0) {
      showToast('Please select at least one extraction engine (Apify or Apollo).', 'warning');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const payload = {
        company_name: companyName.trim(),
        city: city.trim(),
        country: country.trim(),
        domain: domain.trim(),
        engines,
        sheet_name: targetSheet || activeSheet || 'MasterDB',
      };

      const res = await api.extractCompany(payload);

      if (res && res.status === 'success') {
        setResult(res);
        showToast(res.message || 'Company intelligence extracted successfully!', 'success');
        // Refresh pipeline data and stats
        await reloadStats(targetSheet || activeSheet);
        await reloadRecords();
      } else {
        throw new Error(res?.detail || 'Extraction failed to return valid lead data.');
      }
    } catch (err) {
      console.error('Failed to extract company:', err);
      setError(err.message || 'Failed to extract company details.');
      showToast(`Extraction failed: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleViewInTable = () => {
    if (result?.record?.Company_Name) {
      setSearch(result.record.Company_Name);
    }
    closeModal('extractCompany');
  };

  const handleViewDossier = () => {
    const recId = result?.record?.Record_ID;
    closeModal('extractCompany');
    if (recId) {
      openModal('dossier', recId);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setCompanyName('');
    setDomain('');
    setCity('');
  };

  return (
    <div className="modal-overlay" onClick={() => closeModal('extractCompany')}>
      <div 
        className="modal-card modal-dialog-medium extract-company-modal" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        style={{ maxWidth: 680, width: '100%' }}
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge" style={{ background: 'var(--badge-blue-bg)', color: 'var(--badge-blue-text)' }}>
              <Building2 size={18} />
            </div>
            <div>
              <div className="modal-headline">Extract Company Intelligence</div>
              <div className="modal-subheadline">
                Extract Google Maps firmographics and Apollo.io decision makers for any specific company.
              </div>
            </div>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={() => closeModal('extractCompany')}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body" style={{ padding: '20px 24px' }}>
          {!result ? (
            <form onSubmit={handleExtract} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              {/* Target Sheet Selection */}
              <div>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, fontSize: '0.82rem', fontWeight: 600 }}>
                  <Layers size={14} /> Save to Campaign Sheet:
                </label>
                <select 
                  className="form-input" 
                  value={targetSheet} 
                  onChange={(e) => setTargetSheet(e.target.value)}
                  style={{ width: '100%', height: 38 }}
                >
                  {sheets.map(sh => (
                    <option key={sh.name} value={sh.name}>
                      {sh.name} {sh.name === activeSheet ? '(Active Sheet)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Company Name (Required) */}
              <div>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, fontSize: '0.82rem', fontWeight: 600 }}>
                  <Building2 size={14} /> Company Name <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Aramco Digital, Al Rajhi Bank, Microsoft, Lucid Motors..."
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  disabled={loading}
                  style={{ width: '100%', height: 40, fontSize: '0.92rem' }}
                />
              </div>

              {/* City and Country Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div>
                  <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, fontSize: '0.82rem', fontWeight: 600 }}>
                    <MapPin size={14} /> City / Region <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(optional)</span>
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Riyadh, Jeddah, Dubai, Austin"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    disabled={loading}
                    style={{ width: '100%', height: 38 }}
                  />
                </div>

                <div>
                  <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, fontSize: '0.82rem', fontWeight: 600 }}>
                    <Globe size={14} /> Country
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Saudi Arabia, UAE, United States"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    disabled={loading}
                    style={{ width: '100%', height: 38 }}
                  />
                </div>
              </div>

              {/* Website or Domain Hint (Optional) */}
              <div>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, fontSize: '0.82rem', fontWeight: 600 }}>
                  <Globe size={14} /> Website / Domain <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(optional, boosts Apollo match rate)</span>
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. aramcodigital.com or https://company.sa"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  disabled={loading}
                  style={{ width: '100%', height: 38 }}
                />
              </div>

              {/* Engine Selector */}
              <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border)', borderRadius: 10, padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span style={{ fontSize: '0.84rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Sparkles size={14} style={{ color: 'var(--accent)' }} /> Choose Extraction Engines:
                  </span>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button
                      type="button"
                      onClick={() => handleSelectEngines('both')}
                      style={{
                        background: useApify && useApollo ? 'var(--badge-blue-bg)' : 'transparent',
                        borderColor: useApify && useApollo ? 'var(--badge-blue-border)' : 'var(--border)',
                        color: useApify && useApollo ? 'var(--badge-blue-text)' : 'var(--text-muted)',
                        padding: '3px 8px',
                        fontSize: '0.72rem',
                        borderRadius: 4,
                        border: '1px solid',
                        cursor: 'pointer',
                      }}
                    >
                      Both (Recommended)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSelectEngines('apify')}
                      style={{
                        background: useApify && !useApollo ? 'var(--badge-green-bg)' : 'transparent',
                        borderColor: useApify && !useApollo ? 'var(--badge-green-border)' : 'var(--border)',
                        color: useApify && !useApollo ? 'var(--badge-green-text)' : 'var(--text-muted)',
                        padding: '3px 8px',
                        fontSize: '0.72rem',
                        borderRadius: 4,
                        border: '1px solid',
                        cursor: 'pointer',
                      }}
                    >
                      Apify Only
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSelectEngines('apollo')}
                      style={{
                        background: !useApify && useApollo ? 'var(--badge-blue-bg)' : 'transparent',
                        borderColor: !useApify && useApollo ? 'var(--badge-blue-border)' : 'var(--border)',
                        color: !useApify && useApollo ? 'var(--badge-blue-text)' : 'var(--text-muted)',
                        padding: '3px 8px',
                        fontSize: '0.72rem',
                        borderRadius: 4,
                        border: '1px solid',
                        cursor: 'pointer',
                      }}
                    >
                      Apollo Only
                    </button>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {/* Apify Card */}
                  <label 
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 10,
                      padding: '12px 14px',
                      borderRadius: 8,
                      border: `1px solid ${useApify ? 'var(--badge-green-border)' : 'var(--border)'}`,
                      background: useApify ? 'var(--badge-green-bg)' : 'transparent',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={useApify}
                      onChange={(e) => setUseApify(e.target.checked)}
                      disabled={loading}
                      style={{ marginTop: 2 }}
                    />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--badge-green-text)' }}>
                        Apify Google Maps
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2, lineHeight: 1.4 }}>
                        Extracts verified phone, website, Google rating, reviews, full address & maps link.
                      </div>
                    </div>
                  </label>

                  {/* Apollo Card */}
                  <label 
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 10,
                      padding: '12px 14px',
                      borderRadius: 8,
                      border: `1px solid ${useApollo ? 'var(--badge-blue-border)' : 'var(--border)'}`,
                      background: useApollo ? 'var(--badge-blue-bg)' : 'transparent',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={useApollo}
                      onChange={(e) => setUseApollo(e.target.checked)}
                      disabled={loading}
                      style={{ marginTop: 2 }}
                    />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--badge-blue-text)' }}>
                        Apollo.io B2B Contacts
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2, lineHeight: 1.4 }}>
                        Extracts C-Level decision makers, verified corporate emails, mobile numbers & LinkedIn.
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Error Notice */}
              {error && (
                <div style={{ 
                  background: 'rgba(239, 68, 68, 0.12)', 
                  border: '1px solid rgba(239, 68, 68, 0.3)', 
                  borderRadius: 8, 
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  color: '#f87171',
                  fontSize: '0.82rem'
                }}>
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 4 }}>
                <button
                  type="button"
                  className="action-btn btn-secondary"
                  onClick={() => closeModal('extractCompany')}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="action-btn btn-primary"
                  disabled={loading || !companyName.trim()}
                  style={{ minWidth: 170 }}
                >
                  {loading ? (
                    <>
                      <Loader2 size={15} className="spin-animate" />
                      <span>Extracting Details...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={15} />
                      <span>Extract & Enrich</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          ) : (
            /* Result Card View */
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: 8,
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                color: 'var(--badge-green-text)',
                fontSize: '0.86rem'
              }}>
                <CheckCircle2 size={18} />
                <span style={{ fontWeight: 500 }}>{result.message}</span>
              </div>

              {/* Company Summary Card */}
              <div style={{
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border)',
                borderRadius: 10,
                padding: 18,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: 'var(--text)' }}>
                      {result.record?.Company_Name}
                    </h3>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
                      {result.record?.Primary_Industry || 'General Business'} • {result.record?.City || 'Global'}, {result.record?.Country || ''}
                    </div>
                  </div>
                  <span style={{
                    background: 'var(--badge-blue-bg)',
                    color: 'var(--badge-blue-text)',
                    border: '1px solid var(--badge-blue-border)',
                    padding: '3px 8px',
                    borderRadius: 6,
                    fontSize: '0.72rem',
                    fontWeight: 600,
                  }}>
                    {result.record?.Record_ID}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginTop: 12 }}>
                  {/* Phone */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem' }}>
                    <Phone size={14} style={{ color: 'var(--badge-green-text)' }} />
                    <span>{result.record?.Primary_Phone || result.record?.WhatsApp_Number || 'No phone discovered'}</span>
                  </div>

                  {/* Website */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem' }}>
                    <Globe size={14} style={{ color: 'var(--accent)' }} />
                    {result.record?.Website_URL ? (
                      <a href={result.record.Website_URL} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 4 }}>
                        {result.record.Website_URL.replace(/^https?:\/\//, '')}
                        <ExternalLink size={11} />
                      </a>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>No website found</span>
                    )}
                  </div>

                  {/* Decision Maker */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem' }}>
                    <UserCheck size={14} style={{ color: 'var(--accent)' }} />
                    <span>
                      {result.record?.DM_Full_Name ? (
                        <strong>{result.record.DM_Full_Name} ({result.record.DM_Title || 'Executive'})</strong>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>No DM identified</span>
                      )}
                    </span>
                  </div>

                  {/* Verified Email */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem' }}>
                    <Mail size={14} style={{ color: 'var(--badge-amber-text)' }} />
                    {result.record?.DM_Direct_Email ? (
                      <span style={{ color: 'var(--badge-green-text)', fontWeight: 600 }}>
                        {result.record.DM_Direct_Email}
                        {result.record.DM_Email_Score ? ` (${result.record.DM_Email_Score}% score)` : ''}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>{result.record?.General_Email || 'No direct email'}</span>
                    )}
                  </div>
                </div>

                {result.engine_notes && result.engine_notes.length > 0 && (
                  <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border)', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    <strong>Engine Details:</strong> {result.engine_notes.join(' • ')}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                <button
                  type="button"
                  className="action-btn btn-secondary"
                  onClick={handleReset}
                >
                  <Search size={14} /> Extract Another Company
                </button>

                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    type="button"
                    className="action-btn btn-secondary"
                    onClick={handleViewDossier}
                  >
                    View Lead Dossier
                  </button>
                  <button
                    type="button"
                    className="action-btn btn-primary"
                    onClick={handleViewInTable}
                  >
                    View in Companies Table
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
