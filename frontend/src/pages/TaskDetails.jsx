import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function TaskDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    api.get(`/api/tasks/${id}`).then(r => setTask(r.data)).catch(() => navigate('/tasks')).finally(() => setLoading(false));
  }, [id]);

  const updateStatus = async (newStatus) => {
    setUpdating(true);
    try {
      const res = await api.put(`/api/tasks/${id}`, { status: newStatus });
      setTask(res.data);
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
    finally { setUpdating(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!task) return <div className="empty-state"><p>Task not found</p></div>;

  const statusBadge = (s) => ({ PENDING: 'badge-pending', IN_PROGRESS: 'badge-progress', COMPLETED: 'badge-completed', CONFIRMED: 'badge-pending' }[s] || 'badge-pending');
  const priorityBadge = (p) => ({ LOW: 'badge-low', MEDIUM: 'badge-medium', HIGH: 'badge-high', URGENT: 'badge-urgent' }[p] || 'badge-medium');

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{task.title}</h1>
          <p className="page-subtitle">
            <span className={`badge ${statusBadge(task.status)}`}>{task.status.replace('_', ' ')}</span>
            {' '}
            <span className={`badge ${priorityBadge(task.priority)}`}>{task.priority}</span>
            {task.source === 'AI_EXTRACTED' && <span className="badge badge-review" style={{marginLeft:'0.25rem'}}>🤖 AI Extracted</span>}
          </p>
        </div>
        <div className="flex gap-sm">
          {user?.role === 'EMPLOYEE' && task.status === 'PENDING' && (
            <button className="btn btn-primary" onClick={() => updateStatus('IN_PROGRESS')} disabled={updating}>▶️ Start Working</button>
          )}
          {user?.role === 'EMPLOYEE' && task.status === 'IN_PROGRESS' && (
            <button className="btn btn-success" onClick={() => updateStatus('COMPLETED')} disabled={updating}>✅ Mark Complete</button>
          )}
          {task.meeting_id && (
            <button className="btn btn-secondary" onClick={() => navigate(`/meetings/${task.meeting_id}`)}>📅 View Meeting</button>
          )}
        </div>
      </div>

      <div className="charts-grid">
        <div className="card">
          <h3 style={{marginBottom:'1rem'}}>Task Details</h3>
          <div style={{display:'grid',gap:'0.75rem',fontSize:'0.875rem'}}>
            <div><span style={{color:'var(--text-tertiary)'}}>Assigned to:</span> {task.assignee_name || 'Unassigned'}</div>
            <div><span style={{color:'var(--text-tertiary)'}}>Created by:</span> {task.creator_name}</div>
            <div><span style={{color:'var(--text-tertiary)'}}>Deadline:</span> {task.deadline || 'No deadline'}</div>
            <div><span style={{color:'var(--text-tertiary)'}}>Meeting:</span> {task.meeting_title || 'No meeting'}</div>
            <div><span style={{color:'var(--text-tertiary)'}}>Created:</span> {new Date(task.created_at).toLocaleDateString()}</div>
            {task.completed_at && <div><span style={{color:'var(--text-tertiary)'}}>Completed:</span> {new Date(task.completed_at).toLocaleDateString()}</div>}
          </div>
          {task.description && (
            <div style={{marginTop:'1rem',padding:'1rem',background:'var(--bg-glass)',borderRadius:'var(--radius-md)',fontSize:'0.875rem',color:'var(--text-secondary)'}}>
              {task.description}
            </div>
          )}
        </div>

        {task.source === 'AI_EXTRACTED' && (
          <div className="card">
            <h3 style={{marginBottom:'1rem'}}>AI Intelligence</h3>
            {task.ai_confidence !== null && (
              <div style={{marginBottom:'1rem'}}>
                <div style={{fontSize:'0.75rem',color:'var(--text-tertiary)',marginBottom:'0.25rem'}}>AI Confidence</div>
                <div style={{display:'flex',alignItems:'center',gap:'0.75rem'}}>
                  <div style={{flex:1,height:'8px',background:'var(--bg-input)',borderRadius:'var(--radius-full)',overflow:'hidden'}}>
                    <div style={{height:'100%',width:`${(task.ai_confidence || 0) * 100}%`,background:'var(--accent-gradient)',borderRadius:'var(--radius-full)'}} />
                  </div>
                  <span style={{fontWeight:700,fontSize:'0.875rem'}}>{Math.round((task.ai_confidence || 0) * 100)}%</span>
                </div>
              </div>
            )}
            {task.source_text && (
              <div>
                <div style={{fontSize:'0.75rem',color:'var(--text-tertiary)',marginBottom:'0.25rem'}}>Source from Transcript</div>
                <div className="action-item-source">"{task.source_text}"</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
