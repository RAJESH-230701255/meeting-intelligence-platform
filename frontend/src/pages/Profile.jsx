import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user, logout } = useAuth();

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Profile</h1>
      </div>
      <div className="card" style={{maxWidth:'500px'}}>
        <div style={{display:'flex',alignItems:'center',gap:'1.5rem',marginBottom:'1.5rem'}}>
          <div style={{width:64,height:64,borderRadius:'var(--radius-full)',background:'var(--accent-gradient)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'1.5rem',fontWeight:700,color:'white'}}>
            {user?.name?.split(' ').map(n => n[0]).join('').toUpperCase()}
          </div>
          <div>
            <h2 style={{fontSize:'1.25rem',fontWeight:600}}>{user?.name}</h2>
            <p style={{color:'var(--text-secondary)',fontSize:'0.875rem'}}>{user?.email}</p>
          </div>
        </div>
        <div style={{display:'grid',gap:'0.75rem',fontSize:'0.875rem'}}>
          <div style={{display:'flex',justifyContent:'space-between',padding:'0.75rem 0',borderBottom:'1px solid var(--border-color)'}}>
            <span style={{color:'var(--text-tertiary)'}}>Role</span>
            <span className="badge badge-progress">{user?.role}</span>
          </div>
          <div style={{display:'flex',justifyContent:'space-between',padding:'0.75rem 0',borderBottom:'1px solid var(--border-color)'}}>
            <span style={{color:'var(--text-tertiary)'}}>Status</span>
            <span className="badge badge-completed">{user?.is_active ? 'Active' : 'Inactive'}</span>
          </div>
          <div style={{display:'flex',justifyContent:'space-between',padding:'0.75rem 0',borderBottom:'1px solid var(--border-color)'}}>
            <span style={{color:'var(--text-tertiary)'}}>User ID</span>
            <span>{user?.id}</span>
          </div>
        </div>
        <button className="btn btn-danger mt-lg" onClick={logout}>🚪 Sign Out</button>
      </div>
    </div>
  );
}
