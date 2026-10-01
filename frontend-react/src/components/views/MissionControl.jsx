import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import MultiSelectDropdown from '../common/MultiSelectDropdown';
import { 
  Rocket, 
  Globe2, 
  Play, 
  Square,
  Loader2, 
  Terminal, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

const COUNTRY_PRESETS = [
  { label: 'USA', country: 'United States' },
  { label: 'UK', country: 'United Kingdom' },
  { label: 'UAE', country: 'United Arab Emirates' },
  { label: 'Saudi Arabia', country: 'Saudi Arabia' },
  { label: 'Germany', country: 'Germany' },
  { label: 'Canada', country: 'Canada' },
  { label: 'Australia', country: 'Australia' },
  { label: 'Singapore', country: 'Singapore' },
  { label: 'India', country: 'India' },
];

export default function MissionControl() {
  const { activeSheet, systemConfig, reloadStats, showToast } = useApp();
  const { fetchRecords } = usePipeline();

  // Hierarchical Geo Selection State
  const [allCountriesList, setAllCountriesList] = useState([]);
  const [selectedCountries, setSelectedCountries] = useState(['United States']);
  const [availableStates, setAvailableStates] = useState([]);
  const [selectedStates, setSelectedStates] = useState([]);
  const [availableCities, setAvailableCities] = useState([]);
  const [selectedCities, setSelectedCities] = useState(['New York']);
  const [loadingGeo, setLoadingGeo] = useState(false);

  // Industry & Scope Selection
  const [selectedIndustries, setSelectedIndustries] = useState(['staffing_and_recruitment']);
  const [maxRecords, setMaxRecords] = useState(25);

  // Running Mission State
  const [runningJobId, setRunningJobId] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStage, setJobStage] = useState('');
  const [jobLogs, setJobLogs] = useState([]);
  const [jobFinished, setJobFinished] = useState(false);
  const [starting, setStarting] = useState(false);

  const eventSourceRef = useRef(null);
  const logsEndRef = useRef(null);

  // 1. Load All Countries on mount
  useEffect(() => {
    let isMounted = true;
    async function loadCountries() {
      try {
        const res = await api.getGeoCountries();
        if (isMounted && res && res.countries) {
          setAllCountriesList(res.countries);
        }
      } catch (err) {
        console.error('Failed to load countries:', err);
      }
    }
    loadCountries();
    return () => { isMounted = false; };
  }, []);

  // 2. Load States when Selected Countries change
  useEffect(() => {
    let isMounted = true;
    async function loadStates() {
      if (selectedCountries.length === 0) {
        setAvailableStates([]);
        setSelectedStates([]);
        return;
      }
      try {
        setLoadingGeo(true);
        const res = await api.getGeoStates(selectedCountries);
        if (isMounted && res && res.states) {
          const formatted = res.states.map(s => ({
            id: s.state,
            label: selectedCountries.length > 1 ? `${s.state} (${s.country})` : s.state,
            sub: `${s.cities_count} cities`,
            country: s.country,
          }));
          setAvailableStates(formatted);
          // Retain only states that are still available
          setSelectedStates(prev => prev.filter(st => res.states.some(s => s.state === st)));
        }
      } catch (err) {
        console.error('Failed to load states:', err);
      } finally {
        if (isMounted) setLoadingGeo(false);
      }
    }
    loadStates();
    return () => { isMounted = false; };
  }, [selectedCountries]);

  // 3. Load Cities when Selected Countries or States change
  useEffect(() => {
    let isMounted = true;
    async function loadCities() {
      if (selectedCountries.length === 0) {
        setAvailableCities([]);
        setSelectedCities([]);
        return;
      }
      try {
        const res = await api.getGeoCities(selectedCountries, selectedStates);
        if (isMounted && res && res.cities) {
          const formatted = res.cities.map(c => ({
            id: c.city,
            label: c.city,
            sub: selectedCountries.length > 1 ? `${c.state}, ${c.country}` : c.state,
            country: c.country,
            state: c.state,
          }));
          setAvailableCities(formatted);
        }
      } catch (err) {
        console.error('Failed to load cities:', err);
      }
    }
    loadCities();
    return () => { isMounted = false; };
  }, [selectedCountries, selectedStates]);

  // List of industries from systemConfig or fallback
  const allIndustries = useMemo(() => {
    if (systemConfig?.industries && systemConfig.industries.length > 0) {
      return systemConfig.industries;
    }
    return [
      { key: 'construction', name: 'Construction & Contracting', query_count: 4 },
      { key: 'engineering', name: 'Engineering & Consultancy', query_count: 4 },
      { key: 'software_and_it_services', name: 'Software & IT Services', query_count: 6 },
      { key: 'logistics', name: 'Logistics & Transportation', query_count: 5 },
      { key: 'manufacturing', name: 'Manufacturing', query_count: 4 },
      { key: 'healthcare', name: 'Healthcare & Clinics', query_count: 5 },
      { key: 'staffing_and_recruitment', name: 'Staffing & Recruitment', query_count: 6 },
      { key: 'business_consulting', name: 'Business Consulting Firms', query_count: 5 },
      { key: 'bfsi', name: 'BFSI (Banking & Financial Services)', query_count: 6 },
      { key: 'real_estate', name: 'Real Estate', query_count: 3 },
    ];
  }, [systemConfig]);

  // Default industry selection
  useEffect(() => {
    if (selectedIndustries.length === 0 && allIndustries.length > 0) {
      const defaultKey = allIndustries.find(i => i.key.includes('staffing') || i.key.includes('recruitment'))?.key || allIndustries[0].key;
      setSelectedIndustries([defaultKey]);
    }
  }, [allIndustries, selectedIndustries.length]);

  // Quick preset city chips derived from available cities
  const quickCityChips = useMemo(() => {
    if (availableCities.length === 0) return [];
    // Take first 12 prominent cities
    const unique = [];
    const seen = new Set();
    for (const c of availableCities) {
      if (!seen.has(c.id.toLowerCase())) {
        seen.add(c.id.toLowerCase());
        unique.push(c.id);
      }
      if (unique.length >= 12) break;
    }
    return unique;
  }, [availableCities]);

  // Calculate Google Places Scope & Cost
  const googleEstimates = useMemo(() => {
    const locCount = selectedCities.length > 0 
      ? selectedCities.length 
      : (availableCities.length > 0 ? availableCities.length : 1);

    const indCount = selectedIndustries.length;

    let totalQueries = 0;
    allIndustries.forEach(ind => {
      if (selectedIndustries.includes(ind.key)) {
        totalQueries += (ind.query_count || ind.queries?.length || 1);
      }
    });

    if (totalQueries === 0 && indCount > 0) totalQueries = indCount;

    const totalSearches = locCount * totalQueries;
    const estPlaces = totalSearches * maxRecords;
    const estCost = estPlaces * 0.011; // $0.011 per place

    return {
      locations: locCount,
      industries: indCount,
      queries: totalSearches,
      estPlaces,
      estCost,
    };
  }, [selectedCities.length, availableCities.length, selectedIndustries, allIndustries, maxRecords]);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [jobLogs]);

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, []);

  const connectToStream = (jobId) => {
    setRunningJobId(jobId);
    setJobProgress(0);
    setJobStage('Initializing scrape mission...');
    setJobLogs([`Connected to execution stream (Job: ${jobId})`]);
    setJobFinished(false);

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
            showToast(`Mission complete! Saved ${data.total_saved || 0} leads.`, 'success');
          } else if (data.status === 'failed') {
            showToast('Mission ended with error or stopped.', 'warning');
          }
        }
      } catch (err) {
        console.error('SSE error:', err);
      }
    };

    es.onerror = () => {
      setJobFinished(true);
      es.close();
    };
  };

  const handleStopMission = async () => {
    if (!runningJobId) return;
    try {
      showToast('Stopping mission...', 'info');
      setJobLogs(prev => [...prev, `[!] User requested to stop mission #${runningJobId}...`]);
      await api.stopJob(runningJobId);
      showToast('Stop signal dispatched. Mission halting...', 'warning');
    } catch (err) {
      console.error('Failed to stop job:', err);
      showToast(`Stop failed: ${err.message}`, 'error');
    }
  };

  // Country Preset Button Toggle
  const handleToggleCountryPreset = (countryName) => {
    if (selectedCountries.includes(countryName)) {
      setSelectedCountries(prev => prev.filter(c => c !== countryName));
    } else {
      setSelectedCountries(prev => [...prev, countryName]);
    }
  };

  // City Preset Button Toggle
  const handleToggleCityPreset = (cityName) => {
    if (selectedCities.includes(cityName)) {
      setSelectedCities(prev => prev.filter(c => c !== cityName));
    } else {
      setSelectedCities(prev => [...prev, cityName]);
    }
  };

  // Add Custom City from dropdown search
  const handleAddCustomCity = (customCity) => {
    if (!selectedCities.includes(customCity)) {
      setSelectedCities(prev => [...prev, customCity]);
    }
  };

  // Industry Actions
  const handleSelectAllIndustries = () => {
    setSelectedIndustries(allIndustries.map(i => i.key));
  };

  const handleClearAllIndustries = () => {
    setSelectedIndustries([]);
  };

  const handleToggleIndustry = (key) => {
    setSelectedIndustries(prev => 
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  };

  // Launch Google Places Scraper
  const handleLaunchGoogle = async (e) => {
    e.preventDefault();
    try {
      setStarting(true);
      if (selectedCountries.length === 0) {
        showToast('Please select at least one target country', 'warning');
        return;
      }

      // If user selected cities, use them; if not, use available cities
      let finalLocations = selectedCities;
      if (finalLocations.length === 0) {
        if (availableCities.length > 0) {
          finalLocations = availableCities.slice(0, 15).map(c => c.id);
        } else {
          finalLocations = ['New York'];
        }
      }

      if (selectedIndustries.length === 0) {
        showToast('Please select at least one industry category to scrape', 'warning');
        return;
      }

      const payload = {
        sheet_name: activeSheet,
        country: selectedCountries[0] || 'United States',
        countries: selectedCountries,
        states: selectedStates,
        cities: finalLocations,
        locations: finalLocations,
        industries: selectedIndustries,
        max_records: Number(maxRecords) || 25,
        added_by: 'Google Maps Scraper',
      };

      const res = await api.startScrape(payload);
      showToast(`Mission launched (Job ID: ${res.job_id})`, 'info');
      connectToStream(res.job_id);
    } catch (err) {
      console.error('Failed to launch scrape mission:', err);
      showToast(`Launch failed: ${err.message}`, 'error');
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="tab-view-container active-view">
      {/* View Header */}
      <div className="view-panel-header">
        <div className="view-title-group">
          <div className="panel-badge-pill">
            <Rocket size={13} />
            <span>Autonomous Intelligence Missions</span>
          </div>
          <h1 className="panel-main-title">
            Mission Control
            {activeSheet && <span className="panel-title-sheet"> / {activeSheet}</span>}
          </h1>
          <p className="panel-subtitle">
            Deploy multi-region scrapers across Google Places to discover high-value business leads.
          </p>
        </div>
      </div>

      <div className="mission-layout">
        {/* Left Column: Mission Configuration Forms */}
        <div className="panel-card" style={{ padding: 20 }}>
          <form onSubmit={handleLaunchGoogle} className="mission-form">
              
              {/* 1. Target Country / Countries Dropdown (Every country in the world) */}
              <MultiSelectDropdown
                id="wrapperCountry"
                label="Target Country (or Countries)"
                placeholder="Select Countries"
                searchPlaceholder="Search 195+ countries..."
                items={allCountriesList}
                selected={selectedCountries}
                onChange={setSelectedCountries}
                renderPresetChips={
                  <div className="location-presets">
                    {COUNTRY_PRESETS.map((preset) => (
                      <button
                        key={preset.label}
                        type="button"
                        className={`preset-chip ${selectedCountries.includes(preset.country) ? 'active-country' : ''}`}
                        onClick={() => handleToggleCountryPreset(preset.country)}
                        title={`Click to toggle ${preset.country}`}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                }
              />

              {/* 2. Target State / Province / Region Dropdown (Filtered by Country) */}
              <MultiSelectDropdown
                id="wrapperState"
                label="Target State / Province / Region"
                placeholder={selectedCountries.length === 0 ? "Select country first" : "All States (or select specific)"}
                searchPlaceholder="Search states or provinces..."
                items={availableStates}
                selected={selectedStates}
                onChange={setSelectedStates}
                disabled={selectedCountries.length === 0}
                disabledMessage="Please select at least one country first"
              />

              {/* 3. Target City (or Cities) Dropdown (Filtered by Country & State + Custom City Addition) */}
              <MultiSelectDropdown
                id="wrapperCity"
                label="Target City (or Cities)"
                placeholder={selectedCountries.length === 0 ? "Select country first" : (selectedCities.length === 0 ? "All Cities (or select specific)" : "Select Cities")}
                searchPlaceholder="Search cities or type custom city..."
                items={availableCities}
                selected={selectedCities}
                onChange={setSelectedCities}
                allowCustom={true}
                onAddCustom={handleAddCustomCity}
                disabled={selectedCountries.length === 0}
                disabledMessage="Please select at least one country first"
                renderPresetChips={
                  quickCityChips.length > 0 ? (
                    <div className="location-presets">
                      {quickCityChips.map((city) => (
                        <button
                          key={city}
                          type="button"
                          className={`preset-chip ${selectedCities.includes(city) ? 'active-country' : ''}`}
                          onClick={() => handleToggleCityPreset(city)}
                          title={`Click to add/remove ${city}`}
                        >
                          + {city}
                        </button>
                      ))}
                    </div>
                  ) : null
                }
              />

              {/* 4. Multi-Select Industry Grid */}
              <div className="form-group">
                <div className="industry-actions-bar">
                  <label className="form-label" style={{ marginBottom: 0 }}>
                    Industries ({selectedIndustries.length} selected)
                  </label>
                  <div>
                    <button type="button" className="text-btn" onClick={handleSelectAllIndustries}>
                      Select All
                    </button>
                    <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>•</span>
                    <button type="button" className="text-btn" onClick={handleClearAllIndustries}>
                      Clear
                    </button>
                  </div>
                </div>
                <div className="industry-selection-grid">
                  {allIndustries.map((ind) => {
                    const isChecked = selectedIndustries.includes(ind.key);
                    const qCount = ind.query_count || ind.queries?.length || 1;
                    return (
                      <label key={ind.key} className="industry-checkbox-label">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleIndustry(ind.key)}
                        />
                        <span>{ind.name}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                          ({qCount} queries)
                        </span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* 5. Max Leads Slider */}
              <div className="form-group">
                <label className="form-label">Max Leads per Search Term</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <input
                    type="range"
                    min="5"
                    max="200"
                    step="5"
                    value={maxRecords}
                    onChange={(e) => setMaxRecords(Number(e.target.value))}
                    style={{ flex: 1, accentColor: '#ffffff' }}
                  />
                  <span className="badge badge-gray" style={{ fontSize: '0.8rem', padding: '4px 8px' }}>
                    <span>{maxRecords}</span> leads
                  </span>
                </div>
              </div>

              {/* 6. Live Scope & Cost Estimator Box */}
              <div className="estimator-box">
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Estimated Scope & Cost
                </div>
                <div className="estimator-grid">
                  <div className="est-item">
                    <span className="est-label">Locations</span>
                    <span className="est-val">{googleEstimates.locations}</span>
                  </div>
                  <div className="est-item">
                    <span className="est-label">Industries</span>
                    <span className="est-val">{googleEstimates.industries}</span>
                  </div>
                  <div className="est-item">
                    <span className="est-label">Queries</span>
                    <span className="est-val">{googleEstimates.queries}</span>
                  </div>
                  <div className="est-item">
                    <span className="est-label">Est. Leads</span>
                    <span className="est-val">~{googleEstimates.estPlaces.toLocaleString()}</span>
                  </div>
                  <div className="est-item" style={{ gridColumn: 'span 2' }}>
                    <span className="est-label">Estimated Apify Cost</span>
                    <span className="est-val" style={{ color: 'var(--text)' }}>
                      ${googleEstimates.estCost.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Start / Stop Scraper Button */}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="submit"
                  className="action-btn btn-primary"
                  style={{ flex: 1, justifyContent: 'center', padding: 10, fontSize: '0.85rem' }}
                  disabled={starting || (runningJobId && !jobFinished)}
                >
                  {starting ? (
                    <Loader2 size={15} className="spin-animate" />
                  ) : (
                    <Play size={15} />
                  )}
                  <span>{starting ? 'Starting Mission...' : (runningJobId && !jobFinished) ? 'Scraper In Progress...' : 'Start Scraper'}</span>
                </button>
                {runningJobId && !jobFinished && (
                  <button
                    type="button"
                    className="action-btn btn-danger"
                    style={{ padding: '0 16px', fontSize: '0.85rem', backgroundColor: 'rgba(239, 68, 68, 0.2)', borderColor: 'rgba(239, 68, 68, 0.4)' }}
                    onClick={handleStopMission}
                    title="Stop running scrape mission"
                  >
                    <Square size={13} fill="currentColor" />
                    <span>Stop</span>
                  </button>
                )}
              </div>
            </form>
          </div>

        {/* Right Column: Live Mission Console */}
        <div className="panel-card" style={{ padding: 20, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: '0.85rem', color: 'var(--text)' }}>
              <Terminal size={15} style={{ color: 'var(--accent)' }} />
              <span>Autonomous Execution Console</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {runningJobId && !jobFinished && (
                <button
                  type="button"
                  className="action-btn btn-danger"
                  style={{ fontSize: '0.72rem', padding: '3px 10px', height: 24, backgroundColor: 'rgba(239, 68, 68, 0.2)', borderColor: 'rgba(239, 68, 68, 0.4)' }}
                  onClick={handleStopMission}
                  title="Halt active scrape mission"
                >
                  <Square size={11} fill="currentColor" />
                  <span>Stop Mission</span>
                </button>
              )}
              {runningJobId && (
                <span className={`badge ${jobFinished ? 'badge-emerald' : 'badge-cyan'}`}>
                  {jobFinished ? 'COMPLETED' : 'RUNNING'}
                </span>
              )}
            </div>
          </div>

          <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: 4 }}>
              <span>{jobStage || 'Standing by for mission parameters'}</span>
              <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{jobProgress}%</span>
            </div>
            <div className="progress-bar-track">
              <div 
                className="progress-bar-fill" 
                style={{ 
                  width: `${jobProgress}%`, 
                  background: '#6366f1',
                  transition: 'width 0.3s ease'
                }} 
              />
            </div>
          </div>

          <div className="terminal-wrapper" style={{ flex: 1, minHeight: 440 }}>
            <div className="terminal-header">
              <span>EXECUTION LOGS</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span>{jobLogs.length} entries</span>
                <button
                  type="button"
                  className="text-btn"
                  onClick={() => setJobLogs([])}
                  style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="terminal-content">
              {jobLogs.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', padding: 24, textAlign: 'center' }}>
                  Ready. Select parameters on the left and click "Start Scraper" to begin.
                </div>
              ) : (
                jobLogs.map((log, idx) => (
                  <div key={idx} className="log-entry">
                    <span className="log-msg">{log}</span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
