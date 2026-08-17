import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import api from '../services/api';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    api.get('/api/notifications')
      .then(res => setUnreadCount(res.data.unread_count))
      .catch(() => {});
    const interval = setInterval(() => {
      api.get('/api/notifications')
        .then(res => setUnreadCount(res.data.unread_count))
        .catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user?.name?.split(' ').map(n => n[0]).join('').toUpperCase() || '?';

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">🧠</div>
          <div className="sidebar-brand-text">Meeting<br/>Intelligence</div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-title">Main</div>
          {user?.role === 'EMPLOYEE' && (
            <NavLink to="/employee" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <span className="sidebar-link-icon">📊</span> Dashboard
            </NavLink>
          )}
          {(user?.role === 'MANAGER' || user?.role === 'ADMIN') && (
            <NavLink to={user.role === 'ADMIN' ? '/admin' : '/manager'} className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <span className="sidebar-link-icon">📊</span> Dashboard
            </NavLink>
          )}

          <div className="sidebar-section-title">Workspace</div>
          <NavLink to="/meetings" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <span className="sidebar-link-icon">📅</span> Meetings
          </NavLink>
          <NavLink to="/tasks" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <span className="sidebar-link-icon">✅</span> Tasks
          </NavLink>

          {(user?.role === 'MANAGER' || user?.role === 'ADMIN') && (
            <>
              <div className="sidebar-section-title">Management</div>
              {user?.role === 'ADMIN' && (
                <NavLink to="/admin" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
                  <span className="sidebar-link-icon">⚙️</span> Admin Panel
                </NavLink>
              )}
            </>
          )}
        </nav>

        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user?.name}</div>
            <div className="sidebar-user-role">{user?.role?.toLowerCase()}</div>
          </div>
          <button className="btn btn-ghost btn-icon" onClick={handleLogout} title="Logout">🚪</button>
        </div>
      </aside>

      {/* Navbar */}
      <header className="navbar">
        <div className="navbar-title">Meeting Intelligence Platform</div>
        <div className="navbar-actions">
          <div className="notification-bell" onClick={() => navigate('/tasks')} title="Notifications">
            🔔
            {unreadCount > 0 && <span className="notification-count">{unreadCount}</span>}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/profile')}>
            {user?.name}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
