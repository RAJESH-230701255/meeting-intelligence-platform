import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { auth } from '../services/api';

export default function ResetPassword() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [status, setStatus] = useState({ type: '', message: '' });
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();
  const token = new URLSearchParams(location.search).get('token');

  useEffect(() => {
    if (!token) {
      setStatus({ type: 'error', message: 'Invalid or missing reset token.' });
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) return;

    if (password !== confirmPassword) {
      setStatus({ type: 'error', message: 'Passwords do not match.' });
      return;
    }
    
    if (password.length < 6) {
      setStatus({ type: 'error', message: 'Password must be at least 6 characters long.' });
      return;
    }

    setStatus({ type: '', message: '' });
    setLoading(true);
    try {
      const res = await auth.resetPassword(token, password);
      setStatus({ type: 'success', message: res.data.message || 'Password reset successfully.' });
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setStatus({ 
        type: 'error', 
        message: err.response?.data?.detail || 'Failed to reset password.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">🔒</div>
          <h1>Set New Password</h1>
          <p>Please enter your new password</p>
        </div>

        {status.message && (
          <div className={status.type === 'error' ? 'auth-error' : 'auth-success'} style={{ 
            padding: '1rem', 
            borderRadius: '0.5rem', 
            marginBottom: '1.5rem', 
            backgroundColor: status.type === 'error' ? '#fee2e2' : '#dcfce7',
            color: status.type === 'error' ? '#991b1b' : '#166534',
            border: `1px solid ${status.type === 'error' ? '#f87171' : '#86efac'}`
          }}>
            {status.message}
            {status.type === 'success' && <p style={{marginTop: '0.5rem', fontSize: '0.875rem'}}>Redirecting to login...</p>}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="password">New Password</label>
            <input id="password" type="password" className="form-input" placeholder="Enter new password"
              value={password} onChange={e => setPassword(e.target.value)} required disabled={!token || status.type === 'success'} />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
            <input id="confirmPassword" type="password" className="form-input" placeholder="Confirm new password"
              value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required disabled={!token || status.type === 'success'} />
          </div>
          <button type="submit" className="btn btn-primary w-full btn-lg" disabled={loading || !token || status.type === 'success'}>
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        <div className="auth-footer">
          Back to <Link to="/login">Sign In</Link>
        </div>
      </div>
    </div>
  );
}
