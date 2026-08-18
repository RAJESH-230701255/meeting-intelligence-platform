import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const Modal = ({ title, onClose, error, children }) => (
  <div className="modal-overlay" onClick={onClose}>
    <div className="modal" onClick={e => e.stopPropagation()}>
      <div className="modal-header">
        <h2 className="modal-title">{title}</h2>
        <button type="button" className="modal-close" onClick={onClose}>×</button>
      </div>
      {error && <div style={{padding: '0.75rem', background: 'var(--danger)', color: 'white', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem'}}>⚠️ {error}</div>}
      {children}
    </div>
  </div>
);

export default function Meetings() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ title: '', description: '', meeting_type: 'INTERNAL', participant_ids: [] });
  const [uploadMeetingId, setUploadMeetingId] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadType, setUploadType] = useState('transcript');
  const [processing, setProcessing] = useState(false);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadMeetings();
    if (user?.role !== 'EMPLOYEE') api.get('/api/users').then(r => setUsers(r.data.users)).catch(() => {});
  }, []);

  const loadMeetings = () => {
    api.get('/api/meetings', { params: search ? { search } : {} })
      .then(r => setMeetings(r.data.meetings))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const createMeeting = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await api.post('/api/meetings', form);
      setShowCreate(false);
      setForm({ title: '', description: '', meeting_type: 'INTERNAL', participant_ids: [] });
      loadMeetings();
      if (res.data.meeting_type === 'INTERNAL') navigate(`/meetings/${res.data.id}`);
    } catch (err) { setError(err.response?.data?.detail || 'Failed to create meeting.'); }
  };

  const handleUpload = async (meetingId) => {
    if (!uploadFile) return;
    setProcessing(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      if (uploadType === 'audio') {
        await api.post(`/api/meetings/${meetingId}/process`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      } else {
        await api.post(`/api/meetings/${meetingId}/transcript/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        // Trigger AI analysis on existing transcript
        await api.post(`/api/meetings/${meetingId}/process`);
      }
      setShowUpload(false);
      setUploadFile(null);
      navigate(`/meetings/${meetingId}`);
    } catch (err) { setError(err.response?.data?.detail || 'Upload or analysis failed.'); }
    finally { setProcessing(false); }
  };

  const toggleParticipant = (id) => {
    setForm(prev => ({
      ...prev,
      participant_ids: prev.participant_ids.includes(id)
        ? prev.participant_ids.filter(p => p !== id)
        : [...prev.participant_ids, id],
    }));
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Meetings</h1><p className="page-subtitle">Manage and review your meetings</p></div>
        {user?.role !== 'EMPLOYEE' && (
          <div className="flex gap-sm">
            <button className="btn btn-secondary" onClick={() => { setShowUpload(true); setShowCreate(false); }}>📁 Upload External</button>
            <button className="btn btn-primary" onClick={() => { setShowCreate(true); setShowUpload(false); }}>➕ New Meeting</button>
          </div>
        )}
      </div>

      <div className="mb-lg">
        <input className="form-input" placeholder="Search meetings..." value={search}
          onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadMeetings()} style={{maxWidth:'400px'}} />
      </div>

      {meetings.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">📅</div><p className="empty-state-text">No meetings found</p>
          {user?.role !== 'EMPLOYEE' && <button className="btn btn-primary" onClick={() => setShowCreate(true)}>Create First Meeting</button>}
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead><tr><th>Meeting</th><th>Type</th><th>Status</th><th>Date</th><th>Tasks</th><th>Actions</th></tr></thead>
            <tbody>
              {meetings.map(m => (
                <tr key={m.id}>
                  <td style={{cursor:'pointer'}} onClick={() => navigate(`/meetings/${m.id}`)}><div style={{fontWeight:600}}>{m.title}</div><div style={{fontSize:'0.75rem',color:'var(--text-tertiary)'}}>{m.host_name}</div></td>
                  <td><span className="badge badge-progress">{m.meeting_type}</span></td>
                  <td><span className={`badge ${m.status === 'COMPLETED' ? 'badge-completed' : m.status === 'IN_PROGRESS' ? 'badge-progress' : 'badge-pending'}`}>{m.status}</span></td>
                  <td>{m.meeting_date || '—'}</td>
                  <td>{m.task_count}</td>
                  <td>
                    <div className="flex gap-sm">
                      <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/meetings/${m.id}`)}>View</button>
                      {m.meeting_type === 'INTERNAL' && m.status === 'SCHEDULED' && user?.role !== 'EMPLOYEE' && (
                        <button className="btn btn-primary btn-sm" onClick={() => navigate(`/meetings/${m.id}/room`)}>Join</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Meeting Modal */}
      {showCreate && (
        <Modal title="Create Meeting" onClose={() => { setShowCreate(false); setError(''); }} error={error}>
            <form onSubmit={createMeeting}>
              <div className="form-group"><label className="form-label">Title</label><input className="form-input" required value={form.title} onChange={e => setForm({...form, title: e.target.value})} /></div>
              <div className="form-group"><label className="form-label">Description</label><textarea className="form-textarea" value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
              <div className="form-group"><label className="form-label">Type</label>
                <select className="form-select" value={form.meeting_type} onChange={e => setForm({...form, meeting_type: e.target.value})}>
                  <option value="INTERNAL">Internal Meeting</option><option value="EXTERNAL">External Meeting</option>
                </select>
              </div>
              {users.length > 0 && (
                <div className="form-group"><label className="form-label">Participants</label>
                  <div style={{maxHeight:'150px',overflow:'auto',border:'1px solid var(--border-color)',borderRadius:'var(--radius-md)',padding:'0.5rem'}}>
                    {users.filter(u => u.id !== user.id).map(u => (
                      <label key={u.id} style={{display:'flex',alignItems:'center',gap:'0.5rem',padding:'0.25rem 0',cursor:'pointer',fontSize:'0.875rem'}}>
                        <input type="checkbox" checked={form.participant_ids.includes(u.id)} onChange={() => toggleParticipant(u.id)} />
                        {u.name} <span style={{color:'var(--text-tertiary)',fontSize:'0.75rem'}}>({u.role})</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              <button type="submit" className="btn btn-primary w-full">Create Meeting</button>
            </form>
        </Modal>
      )}

      {/* Upload External Modal */}
      {showUpload && (
        <Modal title="Upload External Meeting" onClose={() => { setShowUpload(false); setError(''); }} error={error}>
            <div className="form-group"><label className="form-label">Select Meeting</label>
              <select className="form-select" value={uploadMeetingId || ''} onChange={e => setUploadMeetingId(parseInt(e.target.value))}>
                <option value="">Create new external meeting...</option>
                {meetings.filter(m => m.meeting_type === 'EXTERNAL').map(m => <option key={m.id} value={m.id}>{m.title}</option>)}
              </select>
            </div>
            {!uploadMeetingId && (
              <div className="form-group"><label className="form-label">Meeting Title</label>
                <input className="form-input" id="ext-title" placeholder="External meeting title" />
              </div>
            )}
            <div className="form-group"><label className="form-label">Upload Type</label>
              <select className="form-select" value={uploadType} onChange={e => setUploadType(e.target.value)}>
                <option value="transcript">Transcript (TXT, DOCX, PDF)</option><option value="audio">Audio (WAV, MP3, M4A, MP4)</option>
              </select>
            </div>
            <div className="form-group"><label className="form-label">File</label>
              <input type="file" className="form-input" accept={uploadType === 'audio' ? '.wav,.mp3,.m4a,.mp4,.webm,.ogg' : '.txt,.docx,.pdf'}
                onChange={e => setUploadFile(e.target.files[0])} />
            </div>
            <button className="btn btn-primary w-full" disabled={processing || !uploadFile} onClick={async () => {
              let mid = uploadMeetingId;
              if (!mid) {
                const title = document.getElementById('ext-title')?.value || 'External Meeting';
                const res = await api.post('/api/meetings', { title, meeting_type: 'EXTERNAL' });
                mid = res.data.id;
              }
              handleUpload(mid);
            }}>{processing ? 'Processing...' : 'Upload & Analyze'}</button>
        </Modal>
      )}
    </div>
  );
}
