/**
 * LeadIntel API Service Layer
 * Centralized fetch client for FastAPI backend with query serialization and error handling.
 */

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `/api${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch {
      errorDetail = await response.text() || errorDetail;
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return await response.json();
  }
  return await response.text();
}

export const api = {
  // System & Meta
  getConfig: () => request('/config'),
  getFields: () => request('/fields'),
  getSettings: () => request('/settings'),
  saveSettings: (settings) => request('/settings', { method: 'POST', body: settings }),
  testApollo: (payload = {}) => request('/settings/test-apollo', { method: 'POST', body: payload }),

  // Universal Database Connection
  getDatabaseConfig: () => request('/database/config'),
  testDatabaseConnection: (payload) => request('/database/test', { method: 'POST', body: payload }),
  saveDatabaseConfig: (payload) => request('/database/config', { method: 'POST', body: payload }),
  resetDatabaseToSqlite: () => request('/database/reset-sqlite', { method: 'POST' }),

  // Sheets / Campaigns
  getSheets: () => request('/sheets'),
  selectSheet: (sheetName) => request('/sheets/select', { method: 'POST', body: { sheet: sheetName } }),
  createSheet: (name, setActive = true) => request('/sheets', { method: 'POST', body: { name, set_active: setActive } }),
  deleteSheet: (name) => request(`/sheets/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  // Stats & KPIs
  getStats: (sheet) => {
    const qs = sheet ? `?sheet=${encodeURIComponent(sheet)}` : '';
    return request(`/stats${qs}`);
  },

  // Records & Leads
  getRecords: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.set(key, val);
      }
    });
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request(`/records${qs}`);
  },

  getRecordDetail: (recordId, sheet) => {
    const qs = sheet ? `?sheet=${encodeURIComponent(sheet)}` : '';
    return request(`/records/${encodeURIComponent(recordId)}${qs}`);
  },

  updateRecord: (recordId, payload, sheet) => {
    const qs = sheet ? `?sheet=${encodeURIComponent(sheet)}` : '';
    return request(`/records/${encodeURIComponent(recordId)}${qs}`, {
      method: 'PATCH',
      body: payload,
    });
  },

  suppressRecord: (recordId, payload = {}, sheet) => {
    const qs = sheet ? `?sheet=${encodeURIComponent(sheet)}` : '';
    return request(`/records/${encodeURIComponent(recordId)}/suppress${qs}`, {
      method: 'POST',
      body: payload,
    });
  },

  // Scraping Missions & Job Control
  startScrape: (payload) => request('/scrape/start', { method: 'POST', body: payload }),
  getScrapeStatus: (jobId) => request(`/scrape/status/${jobId}`),
  stopJob: (jobId) => request(`/scrape/jobs/${encodeURIComponent(jobId)}/stop`, { method: 'POST' }),

  // Server Control
  shutdownServer: () => request('/server/shutdown', { method: 'POST' }),

  // Lead Enrichment
  previewEnrichment: (payload) => request('/enrich/preview', { method: 'POST', body: payload }),
  startEnrichment: (payload) => request('/enrich/start', { method: 'POST', body: payload }),

  // Geographic Hierarchy
  getGeoCountries: () => request('/geo/countries'),
  getGeoStates: (countries) => request('/geo/states', { method: 'POST', body: { countries } }),
  getGeoCities: (countries, states) => request('/geo/cities', { method: 'POST', body: { countries, states } }),
  getGeoHierarchy: () => request('/geo/hierarchy'),

  // Audit & Run Logs
  getLogs: () => request('/logs'),

  // Export URLs
  getExportUrl: (sheet, columns) => {
    const params = new URLSearchParams();
    if (sheet) params.set('sheet', sheet);
    if (columns && columns.length > 0) params.set('columns', columns.join(','));
    return `/api/export?${params.toString()}`;
  },

  getCsvExportUrl: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.set(key, val);
      }
    });
    return `/api/export/csv?${query.toString()}`;
  },
};
