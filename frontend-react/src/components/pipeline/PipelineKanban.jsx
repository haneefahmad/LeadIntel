import React, { useMemo, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { usePipeline } from '../../context/PipelineContext';
import { api } from '../../api/client';
import { 
  Building2, 
  User, 
  Mail, 
  Phone, 
  DollarSign, 
  ExternalLink, 
  ChevronRight, 
  ChevronLeft,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Clock,
  MoreHorizontal
} from 'lucide-react';

const STAGES = [
  { id: 'Identified', label: 'Identified' },
  { id: 'Contacted', label: 'Contacted' },
  { id: 'Qualified', label: 'Qualified' },
  { id: 'Proposal', label: 'Proposal' },
  { id: 'Negotiation', label: 'Negotiation' },
  { id: 'Closed_Won', label: 'Closed Won' },
];

function normalizeStage(rawStage) {
  if (!rawStage) return 'Identified';
  const s = rawStage.trim();
  if (['Won', 'Closed_Won', 'closed_won'].includes(s)) return 'Closed_Won';
  if (['Proposal', 'Proposal_Sent', 'Demo_Scheduled'].includes(s)) return 'Proposal';
  if (['Negotiation', 'In_Discussion'].includes(s)) return 'Negotiation';
  if (['Qualified', 'In_Conversation'].includes(s)) return 'Qualified';
  if (['Contacted', 'Email_Sent', 'Phone_Called'].includes(s)) return 'Contacted';
  return 'Identified';
}

export default function PipelineKanban() {
  const { openModal, activeSheet, showToast } = useApp();
  const { records, updateLocalRecord, loading } = usePipeline();

  const [updatingId, setUpdatingId] = useState(null);

  // Group records by stage
  const { stageGroups, stageTotals, totalPipelineValue } = useMemo(() => {
    const groups = {
      Identified: [],
      Contacted: [],
      Qualified: [],
      Proposal: [],
      Negotiation: [],
      Closed_Won: [],
    };

    const totals = {
      Identified: 0,
      Contacted: 0,
      Qualified: 0,
      Proposal: 0,
      Negotiation: 0,
      Closed_Won: 0,
    };

    let totalVal = 0;

    records.forEach(r => {
      const stage = normalizeStage(r.Pipeline_Stage || r.Status);
      if (groups[stage]) {
        groups[stage].push(r);
        const val = Number(r.Deal_Value || r.Deal_Value_SAR) || 0;
        totals[stage] += val;
        totalVal += val;
      } else {
        groups.Identified.push(r);
      }
    });

    return { stageGroups: groups, stageTotals: totals, totalPipelineValue: totalVal };
  }, [records]);

  // Quick move lead stage
  const handleMoveStage = async (e, record, targetStage) => {
    e.stopPropagation();
    if (!record || !record.Record_ID) return;
    try {
      setUpdatingId(record.Record_ID);
      const res = await api.updateRecord(
        record.Record_ID, 
        { pipeline_stage: targetStage, updated_by: 'Kanban Quick Move' }, 
        activeSheet
      );
      if (res?.record) {
        updateLocalRecord(res.record);
        showToast(`${record.Company_Name || 'Lead'} moved to ${targetStage.replace(/_/g, ' ')}!`, 'success');
      }
    } catch (err) {
      console.error('Failed to move stage:', err);
      showToast(`Failed to update stage: ${err.message}`, 'error');
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="crm-kanban-wrapper" style={{ padding: '0 0 20px 0' }}>
      {/* Kanban Header Summary */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 18px',
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        marginBottom: 16,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text)' }}>
            Sales Pipeline Funnel
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {records.length} leads in active workflow
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Total Pipeline Value: <strong style={{ color: 'var(--text)', fontSize: '0.92rem' }}>
              ${totalPipelineValue.toLocaleString()}
            </strong>
          </div>
        </div>
      </div>

      {/* Kanban Columns Grid */}
      <div className="crm-kanban-board" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(6, minmax(240px, 1fr))',
        gap: 12,
        overflowX: 'auto',
        alignItems: 'start',
        paddingBottom: 10,
      }}>
        {STAGES.map((stage, idx) => {
          const leads = stageGroups[stage.id] || [];
          const stageTotal = stageTotals[stage.id] || 0;

          return (
            <div 
              key={stage.id}
              className={`crm-kanban-column stage-col-${stage.id}`}
            >
              {/* Column Header */}
              <div 
                className="crm-kanban-col-header" 
                style={{ borderTop: '3px solid var(--stage-accent)' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <span style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: 'var(--stage-accent)',
                      display: 'inline-block',
                    }} />
                    <span style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text)' }}>
                      {stage.label}
                    </span>
                  </div>
                  <span style={{
                    background: 'var(--stage-bg)',
                    color: 'var(--stage-accent)',
                    border: '1px solid var(--stage-border)',
                    borderRadius: 10,
                    padding: '1px 7px',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                  }}>
                    {leads.length}
                  </span>
                </div>

                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  {stageTotal > 0 ? `$${stageTotal.toLocaleString()}` : '$0'}
                </div>
              </div>

              {/* Cards List */}
              <div style={{
                padding: 10,
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                flex: 1,
              }}>
                {leads.length === 0 ? (
                  <div style={{
                    padding: '30px 10px',
                    textAlign: 'center',
                    color: 'var(--text-muted)',
                    fontSize: '0.76rem',
                    fontStyle: 'italic',
                  }}>
                    No deals in this stage
                  </div>
                ) : (
                  leads.map(lead => {
                    const cName = lead.Company_Name || lead.Company_Name_EN || 'Untitled Lead';
                    const dmName = lead.DM_Full_Name || lead.DM1_Full_Name || '';
                    const dmTitle = lead.DM_Title || lead.DM1_Title || '';
                    const dmEmail = lead.DM_Direct_Email || lead.DM1_Email || '';
                    const dealVal = Number(lead.Deal_Value || lead.Deal_Value_SAR) || 0;

                    return (
                      <div
                        key={lead.Record_ID}
                        onClick={() => openModal('dossier', lead.Record_ID)}
                        className="crm-kanban-card"
                      >
                        {/* Company & ID */}
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 6 }}>
                          <span style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text)', lineHeight: 1.3 }}>
                            {cName}
                          </span>
                          <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {lead.Record_ID}
                          </span>
                        </div>

                        {/* Industry & City */}
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {lead.Primary_Industry || lead.Company_Type || 'Business'}
                          {lead.City ? ` • ${lead.City}` : ''}
                        </div>

                        {/* Decision Maker Info */}
                        {dmName && (
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            background: 'var(--bg-subtle)',
                            padding: '4px 6px',
                            borderRadius: 6,
                            fontSize: '0.73rem',
                          }}>
                            <User size={12} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                            <span style={{ color: 'var(--text-secondary)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {dmName} {dmTitle ? `(${dmTitle})` : ''}
                            </span>
                          </div>
                        )}

                        {/* Verified Email Pill */}
                        {dmEmail && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.7rem', color: 'var(--badge-green-text)' }}>
                            <Mail size={11} />
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {dmEmail}
                            </span>
                          </div>
                        )}

                        {/* Bottom Row: Deal Value & Quick Stage Advancement */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginTop: 4,
                          paddingTop: 8,
                          borderTop: '1px solid var(--border-subtle, var(--border))',
                        }}>
                          {dealVal > 0 ? (
                            <span style={{
                              fontWeight: 700,
                              fontSize: '0.78rem',
                              color: 'var(--badge-green-text)',
                              background: 'var(--badge-green-bg)',
                              border: '1px solid var(--badge-green-border)',
                              padding: '2px 6px',
                              borderRadius: 4,
                            }}>
                              ${dealVal.toLocaleString()}
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>No deal value</span>
                          )}

                          {/* Quick stage selector with 1-click arrows */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: 3 }} onClick={(e) => e.stopPropagation()}>
                            {idx > 0 && (
                              <button
                                type="button"
                                className="kanban-stage-arrow-btn"
                                onClick={(e) => handleMoveStage(e, lead, STAGES[idx - 1].id)}
                                disabled={updatingId === lead.Record_ID}
                                title={`Move back to ${STAGES[idx - 1].label}`}
                              >
                                <ChevronLeft size={12} />
                              </button>
                            )}

                            <select
                              value={stage.id}
                              onChange={(e) => handleMoveStage(e, lead, e.target.value)}
                              disabled={updatingId === lead.Record_ID}
                              className="kanban-stage-dropdown"
                            >
                              {STAGES.map(s => (
                                <option key={s.id} value={s.id}>
                                  {s.label}
                                </option>
                              ))}
                            </select>

                            {idx < STAGES.length - 1 && (
                              <button
                                type="button"
                                className="kanban-stage-arrow-btn kanban-stage-arrow-next"
                                onClick={(e) => handleMoveStage(e, lead, STAGES[idx + 1].id)}
                                disabled={updatingId === lead.Record_ID}
                                title={`Advance to ${STAGES[idx + 1].label}`}
                              >
                                <ChevronRight size={12} />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
