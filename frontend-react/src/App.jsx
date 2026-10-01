import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { PipelineProvider } from './context/PipelineContext';
import Header from './components/common/Header';
import ToastContainer from './components/common/ToastContainer';
import PipelineView from './components/views/PipelineView';
import MissionControl from './components/views/MissionControl';
import AuditorView from './components/views/AuditorView';
import RunLogsView from './components/views/RunLogsView';
import DossierModal from './components/modals/DossierModal';
import EnrichModal from './components/modals/EnrichModal';
import SheetsModal from './components/modals/SheetsModal';
import ColumnsModal from './components/modals/ColumnsModal';
import SettingsModal from './components/modals/SettingsModal';
import ExtractCompanyModal from './components/modals/ExtractCompanyModal';

import ErrorBoundary from './components/common/ErrorBoundary';

function MainLayout() {
  const { activeTab, loadingInitial, isServerStopped } = useApp();

  if (isServerStopped) {
    return (
      <div 
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#0a0b10',
          padding: 24,
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <div 
          className="panel-card" 
          style={{
            maxWidth: 480,
            width: '100%',
            textAlign: 'center',
            padding: '36px 28px',
            borderRadius: 12,
            border: '1px solid rgba(239, 68, 68, 0.25)',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div 
            style={{
              width: 58,
              height: 58,
              borderRadius: '50%',
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 18px auto',
              color: '#ef4444',
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
              <line x1="12" y1="2" x2="12" y2="12" />
            </svg>
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text)', margin: '0 0 8px 0' }}>
            Server Stopped Successfully
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '0 0 24px 0' }}>
            The LeadIntel backend server process has cleanly terminated and port <strong>8000</strong> has been released. You can safely close this browser tab.
          </p>
          <div 
            style={{
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '14px 16px',
              textAlign: 'left',
            }}
          >
            <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', marginBottom: 6, fontWeight: 500 }}>
              To restart the server, run in your terminal:
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <code style={{ color: 'var(--accent)', fontWeight: 600, fontSize: '0.85rem', fontFamily: 'monospace' }}>
                python run_web.py
              </code>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loadingInitial) {
    return (
      <div className="app-initial-loader">
        <div className="loader-spark">✦</div>
        <h2>Initializing LeadIntel OS...</h2>
        <p>Connecting to database, active campaigns, and provider schemas.</p>
      </div>
    );
  }

  return (
    <div className="app-layout">
      {/* Universal Top Header */}
      <Header />

      {/* Main Standard Wrapper */}
      <main className="main-wrapper">
        <ErrorBoundary fallbackTitle="View Rendering Error">
          {(activeTab === 'database' || activeTab === 'pipeline') && <PipelineView />}
          {activeTab === 'mission' && <MissionControl />}
          {(activeTab === 'analytics' || activeTab === 'auditor') && <AuditorView />}
          {(activeTab === 'history' || activeTab === 'logs') && <RunLogsView />}
        </ErrorBoundary>
      </main>

      {/* Global Modals */}
      <ErrorBoundary fallbackTitle="Lead Dossier Modal Error">
        <DossierModal />
      </ErrorBoundary>
      <ErrorBoundary fallbackTitle="Enrichment Modal Error">
        <EnrichModal />
      </ErrorBoundary>
      <ErrorBoundary fallbackTitle="Campaign Sheets Modal Error">
        <SheetsModal />
      </ErrorBoundary>
      <ErrorBoundary fallbackTitle="Column Customizer Modal Error">
        <ColumnsModal />
      </ErrorBoundary>
      <ErrorBoundary fallbackTitle="Settings Modal Error">
        <SettingsModal />
      </ErrorBoundary>
      <ErrorBoundary fallbackTitle="Extract Company Modal Error">
        <ExtractCompanyModal />
      </ErrorBoundary>

      {/* Toast Alerts Container */}
      <ToastContainer />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <PipelineProvider>
        <MainLayout />
      </PipelineProvider>
    </AppProvider>
  );
}
