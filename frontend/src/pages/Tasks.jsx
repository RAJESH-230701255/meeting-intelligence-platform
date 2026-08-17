import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function Tasks() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => { loadTasks(); }, [statusFilter, priorityFilter]);

  const loadTasks = () => {
    const params = {};
    if (statusFilter) params.status_filter = statusFilter;
    if (priorityFilter) params.priority = priorityFilter;
    if (search) params.search = search;
    api.get('/api/tasks', { params }).then(r => setTasks(r.data.tasks)).catch(console.error).finally(() => setLoading(false));
  };

  const statusBadge = (s) => ({ PENDING: 'badge-pending', IN_PROGRESS: 'badge-progress', COMPLETED: 'badge-completed', CONFIRMED: 'badge-pending', PENDING_REVIEW: 'badge-review', REJECTED: 'badge-rejected' }[s] || 'badge-pending');
  const priorityBadge = (p) => ({ LOW: 'badge-low', MEDIUM: 'badge-medium', HIGH: 'badge-high', URGENT: 'badge-urgent' }[p] || 'badge-medium');

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Tasks</h1><p className="page-subtitle">{tasks.length} task{tasks.length !== 1 ? 's' : ''}</p></div>
      </div>

      <div className="flex gap-md mb-lg" style={{flexWrap:'wrap'}}>
        <input className="form-input" placeholder="Search tasks..." value={search} style={{maxWidth:'250px'}}
          onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadTasks()} />
        <select className="form-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{maxWidth:'180px'}}>
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option><option value="IN_PROGRESS">In Progress</option>
          <option value="COMPLETED">Completed</option>
          {user?.role !== 'EMPLOYEE' && <option value="PENDING_REVIEW">Pending Review</option>}
        </select>
        <select className="form-select" value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)} style={{maxWidth:'150px'}}>
          <option value="">All Priorities</option>
          <option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="URGENT">Urgent</option>
        </select>
      </div>

      {tasks.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">✅</div><p className="empty-state-text">No tasks found</p></div>
      ) : (
        <div className="table-container">
          <table>
            <thead><tr><th>Task</th><th>Assignee</th><th>Status</th><th>Priority</th><th>Deadline</th><th>Source</th></tr></thead>
            <tbody>
              {tasks.map(t => (
                <tr key={t.id} style={{cursor:'pointer'}} onClick={() => navigate(`/tasks/${t.id}`)}>
                  <td><div style={{fontWeight:600}}>{t.title}</div>{t.meeting_title && <div style={{fontSize:'0.75rem',color:'var(--text-tertiary)'}}>📅 {t.meeting_title}</div>}</td>
                  <td>{t.assignee_name || <span style={{color:'var(--text-tertiary)'}}>Unassigned</span>}</td>
                  <td><span className={`badge ${statusBadge(t.status)}`}>{t.status.replace('_', ' ')}</span></td>
                  <td><span className={`badge ${priorityBadge(t.priority)}`}>{t.priority}</span></td>
                  <td>{t.deadline || '—'}</td>
                  <td><span className={`badge ${t.source === 'AI_EXTRACTED' ? 'badge-review' : 'badge-progress'}`}>{t.source === 'AI_EXTRACTED' ? '🤖 AI' : '✍️ Manual'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
