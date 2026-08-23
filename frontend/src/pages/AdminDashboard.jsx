import { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  Filler
} from 'chart.js';
import { Pie, Bar, Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  Filler
);

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/api/dashboard/admin')
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="empty-state">
        <p>Failed to load dashboard</p>
      </div>
    );
  }

  const roleChart = {
    labels: Object.keys(data.users_by_role || {}),
    datasets: [
      {
        data: Object.values(data.users_by_role || {}),
        backgroundColor: ['#6366f1', '#8b5cf6', '#a78bfa'],
        borderWidth: 0
      }
    ]
  };

  const statusColors = {
    PENDING: '#f59e0b',
    IN_PROGRESS: '#3b82f6',
    COMPLETED: '#10b981',
    PENDING_REVIEW: '#a855f7',
    REJECTED: '#ef4444',
    CONFIRMED: '#6366f1'
  };

  const statusChart = {
    labels: Object.keys(data.tasks_by_status || {}),
    datasets: [
      {
        data: Object.values(data.tasks_by_status || {}),
        backgroundColor: Object.keys(data.tasks_by_status || {}).map(
          k => statusColors[k] || '#6366f1'
        ),
        borderWidth: 0
      }
    ]
  };

  const aiColors = {
    AI_EXTRACTED: '#8b5cf6',
    MANUAL: '#64748b'
  };

  const aiManualChart = {
    labels: Object.keys(data.ai_vs_manual_tasks || {}),
    datasets: [
      {
        data: Object.values(data.ai_vs_manual_tasks || {}),
        backgroundColor: Object.keys(data.ai_vs_manual_tasks || {}).map(
          k => aiColors[k] || '#6366f1'
        ),
        borderWidth: 0
      }
    ]
  };

  const pieOpts = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#94a3b8',
          font: {
            family: 'Inter'
          }
        }
      }
    }
  };

  // --- Line Charts ---
  const lineChartOpts = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#94a3b8',
          font: {
            family: 'Inter'
          }
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: '#64748b',
          maxRotation: 45,
          autoSkip: true,
          maxTicksLimit: 10
        },
        grid: {
          color: 'rgba(255,255,255,0.05)'
        }
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: '#64748b',
          stepSize: 1
        },
        grid: {
          color: 'rgba(255,255,255,0.05)'
        }
      }
    }
  };

  const userGrowthChart = {
    labels: (data.user_growth_trend || []).map(d => {
      const dt = new Date(d.date);
      return `${dt.getMonth() + 1}/${dt.getDate()}`;
    }),
    datasets: [
      {
        label: 'New Users',
        data: (data.user_growth_trend || []).map(d => d.count),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 2,
        borderWidth: 2
      }
    ]
  };

  const activityLabels = (data.system_activity_trend || []).map(d => {
    const dt = new Date(d.date);
    return `${dt.getMonth() + 1}/${dt.getDate()}`;
  });

  const systemActivityChart = {
    labels: activityLabels,
    datasets: [
      {
        label: 'Meetings Created',
        data: (data.system_activity_trend || []).map(
          d => d.meetings_created
        ),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 2,
        borderWidth: 2
      },
      {
        label: 'Tasks Completed',
        data: (data.system_activity_trend || []).map(
          d => d.tasks_completed
        ),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 2,
        borderWidth: 2
      }
    ]
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Admin Dashboard</h1>
          <p className="page-subtitle">
            System-wide analytics and monitoring
          </p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div
            className="stat-card-icon"
            style={{
              background: 'rgba(99,102,241,0.15)',
              color: '#6366f1'
            }}
          >
            👥
          </div>
          <div className="stat-card-value">{data.total_users}</div>
          <div className="stat-card-label">Total Users</div>
        </div>

        <div className="stat-card">
          <div
            className="stat-card-icon"
            style={{
              background: 'rgba(139,92,246,0.15)',
              color: '#8b5cf6'
            }}
          >
            📅
          </div>
          <div className="stat-card-value">{data.total_meetings}</div>
          <div className="stat-card-label">Total Meetings</div>
        </div>

        <div className="stat-card">
          <div
            className="stat-card-icon"
            style={{
              background: 'rgba(245,158,11,0.15)',
              color: '#f59e0b'
            }}
          >
            📋
          </div>
          <div className="stat-card-value">{data.total_tasks}</div>
          <div className="stat-card-label">Total Tasks</div>
        </div>

        <div className="stat-card">
          <div
            className="stat-card-icon"
            style={{
              background: 'rgba(16,185,129,0.15)',
              color: '#10b981'
            }}
          >
            ✅
          </div>
          <div className="stat-card-value">{data.completed_tasks}</div>
          <div className="stat-card-label">Completed</div>
        </div>

        <div className="stat-card">
          <div
            className="stat-card-icon"
            style={{
              background: 'rgba(239,68,68,0.15)',
              color: '#ef4444'
            }}
          >
            ⚠️
          </div>
          <div className="stat-card-value">{data.overdue_tasks}</div>
          <div className="stat-card-label">Overdue Tasks</div>
        </div>

        <div className="stat-card">
          <div
            className="stat-card-icon"
            style={{
              background: 'rgba(168,85,247,0.15)',
              color: '#a855f7'
            }}
          >
            🤖
          </div>
          <div className="stat-card-value">{data.pending_reviews}</div>
          <div className="stat-card-label">Pending AI Reviews</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">User Growth</h2>
            <span
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-tertiary)'
              }}
            >
              Last 30 days
            </span>
          </div>

          <div style={{ padding: '1rem' }}>
            <Line data={userGrowthChart} options={lineChartOpts} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">System Activity</h2>
            <span
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-tertiary)'
              }}
            >
              Last 30 days
            </span>
          </div>

          <div style={{ padding: '1rem' }}>
            <Line data={systemActivityChart} options={lineChartOpts} />
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Users by Role</h2>
          </div>

          <Pie data={roleChart} options={pieOpts} />
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Tasks by Status</h2>
          </div>

          <Doughnut data={statusChart} options={pieOpts} />
        </div>
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">AI vs Manual Tasks</h2>
          </div>

          <Doughnut data={aiManualChart} options={pieOpts} />
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">System Stats</h2>
          </div>

          <div style={{ padding: '1rem' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.75rem 0',
                borderBottom: '1px solid var(--border-color)'
              }}
            >
              <span style={{ color: 'var(--text-secondary)' }}>
                Completion Rate
              </span>
              <strong style={{ color: 'var(--success)' }}>
                {data.completion_rate}%
              </strong>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.75rem 0',
                borderBottom: '1px solid var(--border-color)'
              }}
            >
              <span style={{ color: 'var(--text-secondary)' }}>
                Internal Meetings
              </span>
              <strong>
                {data.meetings_by_type?.INTERNAL || 0}
              </strong>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.75rem 0',
                borderBottom: '1px solid var(--border-color)'
              }}
            >
              <span style={{ color: 'var(--text-secondary)' }}>
                External Meetings
              </span>
              <strong>
                {data.meetings_by_type?.EXTERNAL || 0}
              </strong>
            </div>
          </div>
        </div>
      </div>

      {data.recent_activity &&
        data.recent_activity.length > 0 && (
          <div className="card mt-lg">
            <div className="card-header">
              <h2 className="card-title">
                Recent Activity (Audit Log)
              </h2>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Entity</th>
                    <th>Time</th>
                  </tr>
                </thead>

                <tbody>
                  {data.recent_activity.map(a => (
                    <tr key={a.id}>
                      <td>
                        <span className="badge badge-progress">
                          {a.action}
                        </span>
                      </td>

                      <td>{a.entity_type || '—'}</td>

                      <td
                        style={{
                          fontSize: '0.75rem',
                          color: 'var(--text-tertiary)'
                        }}
                      >
                        {a.timestamp}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
    </div>
  );
}