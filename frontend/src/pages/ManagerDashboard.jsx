import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend, LineElement, PointElement, Filler } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend, LineElement, PointElement, Filler);

export default function ManagerDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/api/dashboard/manager').then(res => setData(res.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!data) return <div className="empty-state"><p>Failed to load dashboard</p></div>;

  const statusColors = { PENDING: '#f59e0b', IN_PROGRESS: '#3b82f6', COMPLETED: '#10b981', PENDING_REVIEW: '#a855f7', REJECTED: '#ef4444', CONFIRMED: '#6366f1' };
  const priorityColors = { LOW: '#10b981', MEDIUM: '#f59e0b', HIGH: '#f97316', URGENT: '#ef4444' };

  const statusChart = {
    labels: Object.keys(data.tasks_by_status),
    datasets: [{ data: Object.values(data.tasks_by_status), backgroundColor: Object.keys(data.tasks_by_status).map(k => statusColors[k] || '#6366f1'), borderWidth: 0 }],
  };

  const priorityChart = {
    labels: Object.keys(data.tasks_by_priority),
    datasets: [{ label: 'Tasks', data: Object.values(data.tasks_by_priority), backgroundColor: Object.keys(data.tasks_by_priority).map(k => priorityColors[k] || '#6366f1'), borderWidth: 0, borderRadius: 6 }],
  };

  const chartOpts = { responsive: true, plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } } }, scales: { x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }, y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } } } };
  const pieOpts = { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' }, padding: 16 } } } };

  // --- Completion Trend Line Chart ---
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

  // --- Meeting Activity Line Chart ---
  const activityLabels = (data.meeting_activity || []).map(d => {
    const dt = new Date(d.date);
    return `${dt.getMonth() + 1}/${dt.getDate()}`;
  });
  const activityValues = (data.meeting_activity || []).map(d => d.count);

  const meetingActivityChart = {
    labels: activityLabels,
    datasets: [{
      label: 'Meetings Created',
      data: activityValues,
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 2,
      pointHoverRadius: 5,
      pointBackgroundColor: '#6366f1',
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
        <div><h1 className="page-title">Manager Dashboard</h1><p className="page-subtitle">Team overview and meeting intelligence</p></div>
        <button className="btn btn-primary" onClick={() => navigate('/meetings')}>📅 Meetings</button>
      </div>

      <div className="stats-grid">
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(99,102,241,0.15)',color:'#6366f1'}}>📅</div><div className="stat-card-value">{data.total_meetings}</div><div className="stat-card-label">Total Meetings</div></div>
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(59,130,246,0.15)',color:'#3b82f6'}}>📊</div><div className="stat-card-value">{data.meetings_this_week}</div><div className="stat-card-label">This Week</div></div>
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(245,158,11,0.15)',color:'#f59e0b'}}>⚡</div><div className="stat-card-value">{data.active_tasks}</div><div className="stat-card-label">Active Tasks</div></div>
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(16,185,129,0.15)',color:'#10b981'}}>✅</div><div className="stat-card-value">{data.completed_tasks}</div><div className="stat-card-label">Completed</div></div>
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(239,68,68,0.15)',color:'#ef4444'}}>⚠️</div><div className="stat-card-value">{data.overdue_tasks}</div><div className="stat-card-label">Overdue</div></div>
        <div className="stat-card" style={{borderColor: data.pending_reviews > 0 ? '#a855f7' : undefined}}>
          <div className="stat-card-icon" style={{background:'rgba(168,85,247,0.15)',color:'#a855f7'}}>🤖</div>
          <div className="stat-card-value">{data.pending_reviews}</div><div className="stat-card-label">Pending AI Reviews</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="card"><div className="card-header"><h2 className="card-title">Tasks by Status</h2></div>
          {Object.keys(data.tasks_by_status).length > 0 ? <Pie data={statusChart} options={pieOpts} /> : <div className="empty-state"><p>No data</p></div>}
        </div>
        <div className="card"><div className="card-header"><h2 className="card-title">Tasks by Priority</h2></div>
          {Object.keys(data.tasks_by_priority).length > 0 ? <Bar data={priorityChart} options={chartOpts} /> : <div className="empty-state"><p>No data</p></div>}
        </div>
      </div>

      <div className="charts-grid">
        <div className="card"><div className="card-header"><h2 className="card-title">Task Completion Trend</h2><span style={{fontSize:'0.75rem',color:'var(--text-tertiary)'}}>Last 30 days</span></div>
          <div style={{padding:'1rem'}}>
            <Line data={completionTrendChart} options={lineChartOpts} />
          </div>
        </div>
        <div className="card"><div className="card-header"><h2 className="card-title">Meeting Activity</h2><span style={{fontSize:'0.75rem',color:'var(--text-tertiary)'}}>Last 30 days</span></div>
          <div style={{padding:'1rem'}}>
            <Line data={meetingActivityChart} options={lineChartOpts} />
          </div>
        </div>
      </div>

      {data.team_workload.length > 0 && (
        <div className="card mt-lg"><div className="card-header"><h2 className="card-title">Team Workload</h2></div>
          <div className="table-container"><table><thead><tr><th>Team Member</th><th>Active Tasks</th></tr></thead>
            <tbody>{data.team_workload.map((m, i) => (
              <tr key={i}><td>{m.name}</td><td><span className="badge badge-progress">{m.tasks} tasks</span></td></tr>
            ))}</tbody></table></div>
        </div>
      )}

      <div className="card mt-lg"><div className="card-header"><h2 className="card-title">Recent Meetings</h2><button className="btn btn-ghost btn-sm" onClick={() => navigate('/meetings')}>View All</button></div>
        {data.recent_meetings.length === 0 ? <div className="empty-state"><p className="empty-state-text">No meetings yet</p></div> : (
          <div className="table-container"><table><thead><tr><th>Meeting</th><th>Type</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>{data.recent_meetings.map(m => (
              <tr key={m.id} style={{cursor:'pointer'}} onClick={() => navigate(`/meetings/${m.id}`)}>
                <td>{m.title}</td><td><span className="badge badge-progress">{m.type}</span></td>
                <td><span className={`badge ${m.status === 'COMPLETED' ? 'badge-completed' : 'badge-pending'}`}>{m.status}</span></td>
                <td>{m.date || '—'}</td>
              </tr>
            ))}</tbody></table></div>
        )}
      </div>

      <div style={{textAlign:'center', padding:'1rem', marginTop:'1rem'}}>
        <span style={{fontSize:'0.875rem', color:'var(--text-tertiary)'}}>Completion Rate: <strong style={{color:'var(--success)'}}>{data.completion_rate}%</strong></span>
      </div>
    </div>
  );
}
