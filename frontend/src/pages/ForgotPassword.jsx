import { useState } from 'react';
import { Link } from 'react-router-dom';
import { auth } from '../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState({ type: '', message: '', mockUrl: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: '', message: '', mockUrl: '' });
    setLoading(true);
    try {
      const res = await auth.forgotPassword(email);
      setStatus({ 
        type: 'success', 
        message: res.data.message,
        mockUrl: res.data.token ? `${window.location.origin}/reset-password?token=${res.data.token}` : ''
      });
      setEmail('');
    } catch (err) {
      setStatus({ 
        type: 'error', 
        message: err.response?.data?.detail || 'Failed to request password reset' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">🧠</div>
          <h1>Reset Password</h1>
          <p>Enter your email to receive a reset link</p>
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
            <p>{status.message}</p>
            {status.mockUrl && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                <strong>Demo mode:</strong> <br/>
                <a href={status.mockUrl} style={{ color: 'var(--primary)', textDecoration: 'underline', wordBreak: 'break-all' }}>Click here to reset password</a>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <input id="email" type="email" className="form-input" placeholder="you@company.com"
              value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary w-full btn-lg" disabled={loading}>
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <div className="auth-footer">
          Remember your password? <Link to="/login">Sign In</Link>
        </div>
      </div>
    </div>
  );
}
