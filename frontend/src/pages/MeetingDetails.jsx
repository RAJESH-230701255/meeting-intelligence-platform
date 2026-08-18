import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function MeetingDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [meeting, setMeeting] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      api.get(`/api/meetings/${id}`).then(r => setMeeting(r.data)),
      api.get(`/api/meetings/${id}/transcript`).then(r => setTranscript(r.data)).catch(() => {}),
      api.get(`/api/meetings/${id}/analysis`).then(r => setAnalysis(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [id]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const res = await api.post(`/api/meetings/${id}/analyze`);
      setAnalysis(res.data);
      const meetingRes = await api.get(`/api/meetings/${id}`);
      setMeeting(meetingRes.data);
      setTab('summary');
    } catch (err) { setError(err.response?.data?.detail || 'AI analysis failed.'); }
    finally { setAnalyzing(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!meeting) return <div className="empty-state"><p>Meeting not found</p></div>;

  const tabs = ['overview', 'transcript', 'summary', 'decisions', 'action-items', 'participants'];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{meeting.title}</h1>
          <p className="page-subtitle">
            <span className={`badge ${meeting.meeting_type === 'INTERNAL' ? 'badge-progress' : 'badge-pending'}`}>{meeting.meeting_type}</span>
            {' '}
            <span className={`badge ${meeting.status === 'COMPLETED' ? 'badge-completed' : 'badge-pending'}`}>{meeting.status}</span>
          </p>
        </div>
        <div className="flex gap-sm">
          {meeting.meeting_type === 'INTERNAL' && (meeting.status === 'SCHEDULED' || meeting.status === 'IN_PROGRESS') && user?.role !== 'EMPLOYEE' && (
            <button className="btn btn-primary" onClick={() => navigate(`/meetings/${id}/room`)}>🎙️ Join Meeting</button>
          )}
          {transcript && !analysis && user?.role !== 'EMPLOYEE' && (
            <button className="btn btn-primary" onClick={runAnalysis} disabled={analyzing}>{analyzing ? '🔄 Analyzing...' : '🤖 Run AI Analysis'}</button>
          )}
          {transcript && analysis && user?.role !== 'EMPLOYEE' && (
            <button className="btn btn-secondary" onClick={runAnalysis} disabled={analyzing}>{analyzing ? '🔄 Re-analyzing...' : '🔄 Re-run Analysis'}</button>
          )}
          {analysis && analysis.action_items?.some(a => a.status === 'PENDING_REVIEW') && user?.role !== 'EMPLOYEE' && (
            <button className="btn btn-secondary" onClick={() => navigate(`/meetings/${id}/review`)}>📋 Review Action Items</button>
          )}
        </div>
      </div>

      {error && (
        <div style={{padding: '1rem', background: 'var(--danger)', color: 'white', borderRadius: 'var(--radius-md)', marginBottom: '1rem'}}>
          ⚠️ {error}
        </div>
      )}

      <div className="tabs">
        {tabs.map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="charts-grid">
          <div className="card">
            <h3 style={{marginBottom:'1rem'}}>Meeting Details</h3>
            <div style={{display:'grid',gap:'0.75rem',fontSize:'0.875rem'}}>
              <div><span style={{color:'var(--text-tertiary)'}}>Host:</span> {meeting.host_name}</div>
              <div><span style={{color:'var(--text-tertiary)'}}>Date:</span> {meeting.meeting_date || 'Not set'}</div>
              <div><span style={{color:'var(--text-tertiary)'}}>Type:</span> {meeting.meeting_type}</div>
              <div><span style={{color:'var(--text-tertiary)'}}>Status:</span> {meeting.status}</div>
              <div><span style={{color:'var(--text-tertiary)'}}>Participants:</span> {meeting.participants.length}</div>
              <div><span style={{color:'var(--text-tertiary)'}}>Tasks:</span> {meeting.task_count}</div>
              <div><span style={{color:'var(--text-tertiary)'}}>Transcript:</span> {meeting.has_transcript ? '✅ Available' : '❌ Not available'}</div>
              <div><span style={{color:'var(--text-tertiary)'}}>AI Summary:</span> {meeting.has_summary ? '✅ Generated' : '❌ Not generated'}</div>
            </div>
            {meeting.description && <div style={{marginTop:'1rem',padding:'1rem',background:'var(--bg-glass)',borderRadius:'var(--radius-md)',fontSize:'0.875rem',color:'var(--text-secondary)'}}>{meeting.description}</div>}
          </div>
          <div className="card">
            <h3 style={{marginBottom:'1rem'}}>Processing Status</h3>
            <div style={{display:'flex',flexDirection:'column',gap:'0.75rem'}}>
              {[{label: 'Meeting Created', done: true}, {label: 'Transcript', done: meeting.has_transcript}, {label: 'AI Analysis', done: !!analysis}, {label: 'Action Items Reviewed', done: analysis?.action_items?.every(a => a.status !== 'PENDING_REVIEW')}].map((step, i) => (
                <div key={i} style={{display:'flex',alignItems:'center',gap:'0.75rem'}}>
                  <div style={{width:24,height:24,borderRadius:'50%',background: step.done ? 'var(--success)' : 'var(--bg-input)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'0.75rem',color:'white',flexShrink:0}}>
                    {step.done ? '✓' : i + 1}
                  </div>
                  <span style={{fontSize:'0.875rem', color: step.done ? 'var(--text-primary)' : 'var(--text-tertiary)'}}>{step.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 'transcript' && (
        <div className="card">
          {transcript ? (
            <pre style={{whiteSpace:'pre-wrap',fontFamily:'inherit',fontSize:'0.875rem',lineHeight:'1.8',color:'var(--text-secondary)'}}>{transcript.content}</pre>
          ) : (
            <div className="empty-state"><p className="empty-state-text">No transcript available</p></div>
          )}
        </div>
      )}

      {tab === 'summary' && (
        <div className="card">
          {analysis ? (
            <div>
              <h3 style={{marginBottom:'1rem'}}>Meeting Summary</h3>
              <p style={{fontSize:'0.9rem',lineHeight:'1.7',color:'var(--text-secondary)',marginBottom:'1.5rem'}}>{analysis.summary}</p>
              {analysis.key_points?.length > 0 && (
                <div><h4 style={{marginBottom:'0.5rem',fontSize:'0.875rem',color:'var(--text-tertiary)',textTransform:'uppercase',letterSpacing:'0.05em'}}>Key Points</h4>
                  <ul style={{listStyle:'none',padding:0}}>
                    {analysis.key_points.map((p, i) => (
                      <li key={i} style={{padding:'0.5rem 0',borderBottom:'1px solid var(--border-color)',fontSize:'0.875rem',display:'flex',gap:'0.5rem'}}>
                        <span style={{color:'var(--accent-primary)'}}>•</span> {p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : <div className="empty-state"><p className="empty-state-text">No analysis available. Run AI analysis first.</p></div>}
        </div>
      )}

      {tab === 'decisions' && (
        <div className="card">
          {analysis?.decisions?.length > 0 ? (
            analysis.decisions.map((d, i) => (
              <div key={i} style={{padding:'1rem',background:'var(--bg-glass)',borderRadius:'var(--radius-md)',marginBottom:'0.75rem',border:'1px solid var(--border-color)'}}>
                <div style={{fontWeight:600,marginBottom:'0.25rem'}}>{d.decision}</div>
                {d.context && <div style={{fontSize:'0.8rem',color:'var(--text-tertiary)'}}>{d.context}</div>}
              </div>
            ))
          ) : <div className="empty-state"><p className="empty-state-text">No decisions identified</p></div>}
        </div>
      )}

      {tab === 'action-items' && (
        <div className="card">
          {analysis?.action_items?.length > 0 ? (
            analysis.action_items.map((a, i) => (
              <div key={i} className="action-item-card" style={{marginBottom:'0.75rem'}}>
                <div className="action-item-header"><span className="action-item-title">{a.title}</span><span className={`badge ${a.status === 'PENDING_REVIEW' ? 'badge-review' : a.status === 'COMPLETED' ? 'badge-completed' : 'badge-pending'}`}>{a.status?.replace('_', ' ')}</span></div>
                <div className="action-item-meta">
                  <span>👤 {a.assignee_name || 'Unassigned'}</span>
                  <span>📅 {a.deadline || 'No deadline'}</span>
                  <span>🏷️ {a.priority}</span>
                  {a.confidence && <span>🤖 {Math.round(a.confidence * 100)}% confidence</span>}
                </div>
              </div>
            ))
          ) : <div className="empty-state"><p className="empty-state-text">No action items found</p></div>}
        </div>
      )}

      {tab === 'participants' && (
        <div className="card">
          {meeting.participants.map(p => (
            <div key={p.id} className="participant-item" style={{padding:'0.75rem 0',borderBottom:'1px solid var(--border-color)'}}>
              <div className="participant-avatar">{p.user_name.split(' ').map(n => n[0]).join('').toUpperCase()}</div>
              <div><div className="participant-name">{p.user_name}</div><div className="participant-role">{p.role_in_meeting} · {p.user_email}</div></div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
