import React from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import KpiCards from '../pipeline/KpiCards';
import PipelineToolbar from '../pipeline/PipelineToolbar';
import LeadsTable from '../pipeline/LeadsTable';
import PipelineKanban from '../pipeline/PipelineKanban';
import Pagination from '../pipeline/Pagination';

export default function PipelineView() {
  const { stats } = useApp();
  const { viewMode } = usePipeline();

  return (
    <div className="tab-pane active" id="tab-database">
      {/* KPI Summary Row */}
      <KpiCards />

      {/* Main Companies Panel Card */}
      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Companies & Pipeline</div>
            <div className="panel-subtitle">Search, filter, manage lead status, and track sales pipeline progress.</div>
          </div>
          <div>
            <span id="totalTableCount" className="badge badge-gray">
              {stats?.total !== undefined ? `${stats.total.toLocaleString()} Leads` : 'Loading...'}
            </span>
          </div>
        </div>

        {/* Enhanced 2-Tier Pipeline Control Panel */}
        <PipelineToolbar />

        {/* View Switcher: Table vs Visual Kanban Board */}
        {viewMode === 'kanban' ? (
          <PipelineKanban />
        ) : (
          <>
            <LeadsTable />
            <Pagination />
          </>
        )}
      </div>
    </div>
  );
}
