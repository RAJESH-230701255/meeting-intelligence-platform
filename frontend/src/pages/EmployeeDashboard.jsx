import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend, LineElement, PointElement, Filler } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend, LineElement, PointElement, Filler);
export default function EmployeeDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/api/dashboard/employee')
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!data) return <div className="empty-state"><p>Failed to load dashboard</p></div>;

  const statusBadge = (status) => {
    const map = { PENDING: 'badge-pending', IN_PROGRESS: 'badge-progress', COMPLETED: 'badge-completed', CONFIRMED: 'badge-pending' };
    return map[status] || 'badge-pending';
  };

  const priorityBadge = (priority) => {
    const map = { LOW: 'badge-low', MEDIUM: 'badge-medium', HIGH: 'badge-high', URGENT: 'badge-urgent' };
    return map[priority] || 'badge-medium';
  };

  const statusColors = { PENDING: '#f59e0b', IN_PROGRESS: '#3b82f6', COMPLETED: '#10b981', PENDING_REVIEW: '#a855f7', REJECTED: '#ef4444', CONFIRMED: '#6366f1' };
  const priorityColors = { LOW: '#10b981', MEDIUM: '#f59e0b', HIGH: '#f97316', URGENT: '#ef4444' };

  const statusChart = {
    labels: Object.keys(data.tasks_by_status || {}),
    datasets: [{ data: Object.values(data.tasks_by_status || {}), backgroundColor: Object.keys(data.tasks_by_status || {}).map(k => statusColors[k] || '#6366f1'), borderWidth: 0 }],
  };

  const priorityChart = {
    labels: Object.keys(data.tasks_by_priority || {}),
    datasets: [{ label: 'Tasks', data: Object.values(data.tasks_by_priority || {}), backgroundColor: Object.keys(data.tasks_by_priority || {}).map(k => priorityColors[k] || '#6366f1'), borderWidth: 0, borderRadius: 6 }],
  };

  const chartOpts = { responsive: true, plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } } }, scales: { x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }, y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } } } };
  const pieOpts = { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' }, padding: 16 } } } };

  const trendLabels = (data.completion_trend || []).map(d => {
    const dt = new Date(d.date);
    return `${dt.getMonth() + 1}/${dt.getDate()}`;
  });
  const trendValues = (data.completion_trend || []).map(d => d.count);

  const completionTrendChart = {
    labels: trendLabels,
    datasets: [{
      label: 'Tasks Completed',
      data: trendValues,
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 2,
      pointHoverRadius: 5,
      pointBackgroundColor: '#10b981',
      borderWidth: 2,
    }],
  };

  const lineChartOpts = {
    responsive: true,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } },
    },
    scales: {
      x: {
        ticks: { color: '#64748b', maxRotation: 45, autoSkip: true, maxTicksLimit: 10 },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        beginAtZero: true,
        ticks: { color: '#64748b', stepSize: 1 },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
    },
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">My Dashboard</h1>
          <p className="page-subtitle">Your tasks and meetings at a glance</p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-icon" style={{background: 'rgba(99,102,241,0.15)', color: '#6366f1'}}>📋</div>
          <div className="stat-card-value">{data.total_tasks}</div>
          <div className="stat-card-label">Total Tasks</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon" style={{background: 'rgba(245,158,11,0.15)', color: '#f59e0b'}}>⏳</div>
          <div className="stat-card-value">{data.pending_tasks}</div>
          <div className="stat-card-label">Pending</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon" style={{background: 'rgba(59,130,246,0.15)', color: '#3b82f6'}}>🔄</div>
          <div className="stat-card-value">{data.in_progress_tasks}</div>
          <div className="stat-card-label">In Progress</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon" style={{background: 'rgba(16,185,129,0.15)', color: '#10b981'}}>✅</div>
          <div className="stat-card-value">{data.completed_tasks}</div>
          <div className="stat-card-label">Completed</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon" style={{background: 'rgba(239,68,68,0.15)', color: '#ef4444'}}>⚠️</div>
          <div className="stat-card-value">{data.overdue_tasks}</div>
          <div className="stat-card-label">Overdue</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-header"><h2 className="card-title">Tasks by Status</h2></div>
          {Object.keys(data.tasks_by_status || {}).length > 0 ? <Pie data={statusChart} options={pieOpts} /> : <div className="empty-state"><p>No data</p></div>}
        </div>
        <div className="card">
          <div className="card-header"><h2 className="card-title">Tasks by Priority</h2></div>
          {Object.keys(data.tasks_by_priority || {}).length > 0 ? <Bar data={priorityChart} options={chartOpts} /> : <div className="empty-state"><p>No data</p></div>}
        </div>
      </div>

      <div className="charts-grid">
        <div className="card" style={{gridColumn: '1 / -1'}}>
          <div className="card-header">
            <h2 className="card-title">Task Completion Trend</h2>
            <span style={{fontSize:'0.75rem',color:'var(--text-tertiary)'}}>Last 30 days</span>
          </div>
          <div style={{padding:'1rem'}}>
            <Line data={completionTrendChart} options={lineChartOpts} />
          </div>
        </div>
      </div>

      <div className="charts-grid">
        {/* Recent Tasks */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Recent Tasks</h2>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/tasks')}>View All</button>
          </div>
          {data.recent_tasks.length === 0 ? (
            <div className="empty-state"><p className="empty-state-text">No tasks yet</p></div>
          ) : (
            <div className="table-container">
              <table>
                <thead><tr><th>Task</th><th>Status</th><th>Priority</th><th>Deadline</th></tr></thead>
                <tbody>
                  {data.recent_tasks.map(t => (
                    <tr key={t.id} style={{cursor:'pointer'}} onClick={() => navigate(`/tasks/${t.id}`)}>
                      <td>{t.title}</td>
                      <td><span className={`badge ${statusBadge(t.status)}`}>{t.status.replace('_',' ')}</span></td>
                      <td><span className={`badge ${priorityBadge(t.priority)}`}>{t.priority}</span></td>
                      <td>{t.deadline || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Upcoming Deadlines */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Upcoming Deadlines</h2>
          </div>
          {data.upcoming_deadlines.length === 0 ? (
            <div className="empty-state"><p className="empty-state-text">No upcoming deadlines</p></div>
          ) : (
            <div>
              {data.upcoming_deadlines.map((t, i) => (
                <div key={i} style={{display:'flex', justifyContent:'space-between', alignItems:'center', padding:'0.5rem 0', borderBottom:'1px solid var(--border-color)'}}>
                  <div>
                    <div style={{fontWeight:500, fontSize:'0.875rem'}}>{t.title}</div>
                  </div>
                  <div style={{display:'flex', gap:'0.5rem', alignItems:'center'}}>
                    <span className={`badge ${priorityBadge(t.priority)}`}>{t.priority}</span>
                    <span style={{fontSize:'0.75rem', color:'var(--text-tertiary)'}}>{t.deadline}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Notifications */}
      {data.notifications.length > 0 && (
        <div className="card mt-lg">
          <div className="card-header">
            <h2 className="card-title">🔔 Notifications</h2>
          </div>
          {data.notifications.map(n => (
            <div key={n.id} style={{padding:'0.5rem 0', borderBottom:'1px solid var(--border-color)', fontSize:'0.875rem', color:'var(--text-secondary)'}}>
              {n.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
