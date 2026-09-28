import React from 'react';
import { usePipeline } from '../../context/PipelineContext';

export default function Pagination() {
  const { 
    totalRecords, 
    totalPages, 
    currentPage, 
    setCurrentPage, 
    limit, 
    setLimit, 
    loading 
  } = usePipeline();

  const startRecord = totalRecords === 0 ? 0 : (currentPage - 1) * limit + 1;
  const endRecord = Math.min(currentPage * limit, totalRecords);

  return (
    <div className="pagination-bar">
      <span id="paginationInfo">
        Showing {startRecord.toLocaleString()}–{endRecord.toLocaleString()} of {totalRecords.toLocaleString()} records (Page {currentPage} of {totalPages || 1})
      </span>
      <div className="pagination-controls">
        <select
          className="page-btn"
          value={limit}
          onChange={(e) => {
            setLimit(Number(e.target.value));
            setCurrentPage(1);
          }}
          style={{ marginRight: 8, cursor: 'pointer' }}
          title="Records per page"
        >
          <option value={10}>10 / page</option>
          <option value={25}>25 / page</option>
          <option value={50}>50 / page</option>
          <option value={100}>100 / page</option>
        </select>

        <button
          type="button"
          className="page-btn"
          id="btnPrevPage"
          disabled={currentPage <= 1 || loading}
          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
        >
          Previous
        </button>

        <span style={{ fontSize: '0.8rem', padding: '0 6px', color: 'var(--text-muted)' }}>
          {currentPage} / {totalPages || 1}
        </span>

        <button
          type="button"
          className="page-btn"
          id="btnNextPage"
          disabled={currentPage >= totalPages || loading}
          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
