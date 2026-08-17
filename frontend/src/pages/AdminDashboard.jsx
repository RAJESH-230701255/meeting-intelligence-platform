import { useState, useEffect } from 'react';
import api from '../services/api';
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/dashboard/admin').then(res => setData(res.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!data) return <div className="empty-state"><p>Failed to load dashboard</p></div>;

  const roleChart = {
    labels: Object.keys(data.users_by_role),
    datasets: [{ data: Object.values(data.users_by_role), backgroundColor: ['#6366f1', '#8b5cf6', '#a78bfa'], borderWidth: 0 }],
  };

  const pieOpts = { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' } } } } };

  return (
    <div>
      <div className="page-header"><div><h1 className="page-title">Admin Dashboard</h1><p className="page-subtitle">System-wide analytics and monitoring</p></div></div>

      <div className="stats-grid">
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(99,102,241,0.15)',color:'#6366f1'}}>👥</div><div className="stat-card-value">{data.total_users}</div><div className="stat-card-label">Total Users</div></div>
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(139,92,246,0.15)',color:'#8b5cf6'}}>📅</div><div className="stat-card-value">{data.total_meetings}</div><div className="stat-card-label">Total Meetings</div></div>
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(245,158,11,0.15)',color:'#f59e0b'}}>📋</div><div className="stat-card-value">{data.total_tasks}</div><div className="stat-card-label">Total Tasks</div></div>
        <div className="stat-card"><div className="stat-card-icon" style={{background:'rgba(16,185,129,0.15)',color:'#10b981'}}>✅</div><div className="stat-card-value">{data.completed_tasks}</div><div className="stat-card-label">Completed</div></div>
      </div>

      <div className="charts-grid">
        <div className="card"><div className="card-header"><h2 className="card-title">Users by Role</h2></div>
          <Pie data={roleChart} options={pieOpts} />
        </div>
        <div className="card"><div className="card-header"><h2 className="card-title">System Stats</h2></div>
          <div style={{padding:'1rem'}}>
            <div style={{display:'flex',justifyContent:'space-between',padding:'0.75rem 0',borderBottom:'1px solid var(--border-color)'}}><span style={{color:'var(--text-secondary)'}}>Completion Rate</span><strong style={{color:'var(--success)'}}>{data.completion_rate}%</strong></div>
            <div style={{display:'flex',justifyContent:'space-between',padding:'0.75rem 0',borderBottom:'1px solid var(--border-color)'}}><span style={{color:'var(--text-secondary)'}}>Internal Meetings</span><strong>{data.meetings_by_type?.INTERNAL || 0}</strong></div>
            <div style={{display:'flex',justifyContent:'space-between',padding:'0.75rem 0',borderBottom:'1px solid var(--border-color)'}}><span style={{color:'var(--text-secondary)'}}>External Meetings</span><strong>{data.meetings_by_type?.EXTERNAL || 0}</strong></div>
          </div>
        </div>
      </div>

      {data.recent_activity.length > 0 && (
        <div className="card mt-lg"><div className="card-header"><h2 className="card-title">Recent Activity (Audit Log)</h2></div>
          <div className="table-container"><table><thead><tr><th>Action</th><th>Entity</th><th>Time</th></tr></thead>
            <tbody>{data.recent_activity.map(a => (
              <tr key={a.id}><td><span className="badge badge-progress">{a.action}</span></td><td>{a.entity_type || '—'}</td><td style={{fontSize:'0.75rem',color:'var(--text-tertiary)'}}>{a.timestamp}</td></tr>
            ))}</tbody></table></div>
        </div>
      )}
    </div>
  );
}
