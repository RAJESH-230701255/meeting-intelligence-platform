import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function TaskReview() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [actionItems, setActionItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    Promise.all([
      api.get(`/api/meetings/${id}/action-items`).then(r => setActionItems(r.data)),
      api.get(`/api/meetings/${id}`).then(r => setMeeting(r.data)),
      api.get('/api/users').then(r => setUsers(r.data.users)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [id]);

  const confirm = async (taskId) => {
    try {
      await api.post(`/api/action-items/${taskId}/confirm`);
      setActionItems(prev => prev.map(a => a.id === taskId ? { ...a, status: 'PENDING' } : a));
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const reject = async (taskId) => {
    try {
      await api.post(`/api/action-items/${taskId}/reject`);
      setActionItems(prev => prev.map(a => a.id === taskId ? { ...a, status: 'REJECTED' } : a));
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setEditForm({
      title: item.title,
      description: item.description || '',
      assigned_to: item.assignee_id || '',
      deadline: item.deadline || '',
      priority: item.priority,
    });
  };

  const saveEdit = async (taskId) => {
    try {
      const payload = { ...editForm };
      if (payload.assigned_to === '') delete payload.assigned_to;
      else payload.assigned_to = parseInt(payload.assigned_to);
      if (!payload.deadline) delete payload.deadline;

      await api.put(`/api/action-items/${taskId}`, payload);
      setActionItems(prev => prev.map(a => a.id === taskId ? { ...a, ...payload, assignee_name: users.find(u => u.id === payload.assigned_to)?.name || a.assignee_name } : a));
      setEditingId(null);
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const confirmEdited = async (taskId) => {
    await saveEdit(taskId);
    await confirm(taskId);
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  const pending = actionItems.filter(a => a.status === 'PENDING_REVIEW');
  const processed = actionItems.filter(a => a.status !== 'PENDING_REVIEW');

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Review AI Action Items</h1>
          <p className="page-subtitle">{meeting?.title} — {pending.length} items pending review</p>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate(`/meetings/${id}`)}>← Back to Meeting</button>
      </div>

      {pending.length === 0 && processed.length === 0 && (
        <div className="empty-state"><div className="empty-state-icon">🤖</div><p className="empty-state-text">No AI-extracted action items for this meeting</p></div>
      )}

      {pending.map(item => (
        <div key={item.id} className="action-item-card">
          {editingId === item.id ? (
            <div>
              <div className="form-group"><label className="form-label">Title</label>
                <input className="form-input" value={editForm.title} onChange={e => setEditForm({...editForm, title: e.target.value})} />
              </div>
              <div className="form-group"><label className="form-label">Description</label>
                <textarea className="form-textarea" value={editForm.description} onChange={e => setEditForm({...editForm, description: e.target.value})} />
              </div>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:'1rem'}}>
                <div className="form-group"><label className="form-label">Assign To</label>
                  <select className="form-select" value={editForm.assigned_to} onChange={e => setEditForm({...editForm, assigned_to: e.target.value})}>
                    <option value="">Unassigned</option>
                    {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                  </select>
                </div>
                <div className="form-group"><label className="form-label">Deadline</label>
                  <input type="date" className="form-input" value={editForm.deadline} onChange={e => setEditForm({...editForm, deadline: e.target.value})} />
                </div>
                <div className="form-group"><label className="form-label">Priority</label>
                  <select className="form-select" value={editForm.priority} onChange={e => setEditForm({...editForm, priority: e.target.value})}>
                    <option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="URGENT">Urgent</option>
                  </select>
                </div>
              </div>
              <div className="action-item-actions">
                <button className="btn btn-success btn-sm" onClick={() => confirmEdited(item.id)}>✓ Save & Confirm</button>
                <button className="btn btn-ghost btn-sm" onClick={() => setEditingId(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <>
              <div className="action-item-header">
                <span className="action-item-title">{item.title}</span>
                <div className="action-item-confidence">
                  <span>{Math.round((item.confidence || 0) * 100)}%</span>
                  <div className="confidence-bar"><div className="confidence-fill" style={{width: `${(item.confidence || 0) * 100}%`}} /></div>
                </div>
              </div>
              {item.description && <p style={{fontSize:'0.875rem',color:'var(--text-secondary)',marginBottom:'0.75rem'}}>{item.description}</p>}
              <div className="action-item-meta">
                <span>👤 {item.assignee_name || 'Unassigned'}</span>
                <span>📅 {item.deadline || 'No deadline'}</span>
                <span>🏷️ <span className={`badge badge-${item.priority?.toLowerCase()}`}>{item.priority}</span></span>
              </div>
              {item.source_text && (
                <div className="action-item-source">💬 "{item.source_text}"</div>
              )}
              <div className="action-item-actions">
                <button className="btn btn-success btn-sm" onClick={() => confirm(item.id)}>✓ Confirm</button>
                <button className="btn btn-secondary btn-sm" onClick={() => startEdit(item)}>✏️ Edit</button>
                <button className="btn btn-danger btn-sm" onClick={() => reject(item.id)}>✗ Reject</button>
              </div>
            </>
          )}
        </div>
      ))}

      {processed.length > 0 && (
        <div className="mt-lg">
          <h3 style={{marginBottom:'1rem',color:'var(--text-tertiary)'}}>Processed Items</h3>
          {processed.map(item => (
            <div key={item.id} className="action-item-card" style={{opacity: item.status === 'REJECTED' ? 0.5 : 1}}>
              <div className="action-item-header">
                <span className="action-item-title">{item.title}</span>
                <span className={`badge ${item.status === 'REJECTED' ? 'badge-rejected' : 'badge-completed'}`}>{item.status?.replace('_', ' ')}</span>
              </div>
              <div className="action-item-meta">
                <span>👤 {item.assignee_name || 'Unassigned'}</span>
                <span>📅 {item.deadline || 'No deadline'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
