import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect, useRef } from 'react';
import { notifications as notificationsApi } from '../services/api';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef(null);

  const fetchNotifications = async () => {
    try {
      const res = await notificationsApi.getNotifications();
      setNotifications(res.data.notifications);
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error('Failed to fetch notifications', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await notificationsApi.markRead(notif.id);
        setNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
        setUnreadCount(prev => Math.max(0, prev - 1));
      } catch (err) {
        console.error('Failed to mark notification as read', err);
      }
    }
    if (notif.task_id) {
      setShowNotifications(false);
      navigate(`/tasks/${notif.task_id}`); // Navigate to specific task detail page
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read', err);
    }
  };

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
          <div className="notification-wrapper" ref={dropdownRef} style={{ position: 'relative' }}>
            <div 
              className="notification-bell" 
              onClick={() => setShowNotifications(!showNotifications)} 
              title="Notifications"
              style={{ cursor: 'pointer', position: 'relative' }}
            >
              🔔
              {unreadCount > 0 && <span className="notification-count">{unreadCount}</span>}
            </div>

            {showNotifications && (
              <div className="notification-dropdown" style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                width: '320px',
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                zIndex: 1000,
                marginTop: '10px',
                maxHeight: '400px',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
              }}>
                <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0, fontSize: '1rem' }}>Notifications</h3>
                  {unreadCount > 0 && (
                    <button onClick={handleMarkAllRead} className="btn btn-ghost btn-sm" style={{ fontSize: '0.8rem' }}>
                      Mark all read
                    </button>
                  )}
                </div>
                <div style={{ overflowY: 'auto', flex: 1 }}>
                  {notifications.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No notifications
                    </div>
                  ) : (
                    notifications.map(notif => (
                      <div 
                        key={notif.id} 
                        onClick={() => handleNotificationClick(notif)}
                        style={{
                          padding: '12px 16px',
                          borderBottom: '1px solid var(--border)',
                          cursor: 'pointer',
                          backgroundColor: notif.is_read ? 'transparent' : 'rgba(99, 102, 241, 0.1)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '4px'
                        }}
                      >
                        <div style={{ fontSize: '0.9rem', color: notif.is_read ? 'var(--text)' : 'var(--text-bright)' }}>
                          {notif.message}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {new Date(notif.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
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
