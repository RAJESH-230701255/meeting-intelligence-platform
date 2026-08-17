import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function MeetingRoom() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [meeting, setMeeting] = useState(null);
  const [recording, setRecording] = useState(false);
  const [muted, setMuted] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [micError, setMicError] = useState(null);
  const [ending, setEnding] = useState(false);
  const [processing, setProcessing] = useState(false);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    api.get(`/api/meetings/${id}`).then(r => {
      setMeeting(r.data);
      startMeeting(r.data);
    }).catch(() => navigate('/meetings'));
    return () => cleanup();
  }, [id]);

  const startMeeting = async (meetingData) => {
    // Mark meeting as started
    try {
      await api.post(`/api/meetings/${id}/start`);
    } catch (e) { /* may already be started */ }

    // Request microphone + start recording automatically
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.start(1000); // Collect data every second
      setRecording(true);

      // Start timer
      timerRef.current = setInterval(() => setElapsed(prev => prev + 1), 1000);
    } catch (err) {
      console.error('Microphone error:', err);
      setMicError(err.name === 'NotAllowedError'
        ? 'Microphone permission denied. Please allow microphone access and refresh.'
        : `Microphone error: ${err.message}`);
    }
  };

  const toggleMute = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach(track => { track.enabled = !track.enabled; });
      setMuted(prev => !prev);
    }
  }, []);

  const endMeeting = async () => {
    setEnding(true);

    // Stop recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (timerRef.current) clearInterval(timerRef.current);
    setRecording(false);

    // Wait for final data
    await new Promise(resolve => setTimeout(resolve, 500));

    // End meeting on server
    try {
      await api.post(`/api/meetings/${id}/end`);
    } catch (e) { /* continue */ }

    // Upload recording automatically
    if (chunksRef.current.length > 0) {
      setProcessing(true);
      try {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', blob, `meeting_${id}.webm`);

        await api.post(`/api/meetings/${id}/audio`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        // Trigger AI analysis
        await api.post(`/api/meetings/${id}/analyze`);
      } catch (err) {
        console.error('Processing error:', err);
      }
    }

    cleanup();
    navigate(`/meetings/${id}`);
  };

  const retryMic = async () => {
    setMicError(null);
    if (meeting) startMeeting(meeting);
  };

  const cleanup = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
  };

  const formatTime = (secs) => {
    const h = Math.floor(secs / 3600).toString().padStart(2, '0');
    const m = Math.floor((secs % 3600) / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  if (!meeting) return <div className="loading-spinner"><div className="spinner" /></div>;

  if (processing) {
    return (
      <div className="meeting-room" style={{alignItems:'center',justifyContent:'center'}}>
        <div style={{textAlign:'center'}}>
          <div className="spinner" style={{margin:'0 auto 1.5rem'}} />
          <h2 style={{marginBottom:'0.5rem'}}>Processing Meeting</h2>
          <p style={{color:'var(--text-secondary)',fontSize:'0.875rem'}}>
            Transcribing audio and running AI analysis...<br/>
            This may take a moment.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="meeting-room">
      {/* Header */}
      <div className="meeting-room-header">
        <div className="meeting-room-info">
          <h2>{meeting.title}</h2>
          <div className="meeting-room-id">Room ID: {meeting.room_id || id}</div>
        </div>
        <div className="flex gap-md items-center">
          {recording && (
            <div className="recording-indicator">
              <div className="recording-dot" />
              Recording
            </div>
          )}
          {micError && <span style={{color:'var(--danger)',fontSize:'0.75rem'}}>⚠️ No mic</span>}
        </div>
      </div>

      {/* Main Area */}
      <div className="meeting-room-body">
        <div className="meeting-room-main">
          {micError ? (
            <div style={{textAlign:'center',maxWidth:'400px'}}>
              <div style={{fontSize:'3rem',marginBottom:'1rem'}}>🎤</div>
              <h3 style={{marginBottom:'0.5rem',color:'var(--danger)'}}>Microphone Access Required</h3>
              <p style={{color:'var(--text-secondary)',fontSize:'0.875rem',marginBottom:'1rem'}}>{micError}</p>
              <button className="btn btn-primary" onClick={retryMic}>Retry Permission</button>
            </div>
          ) : (
            <div className="meeting-room-visual">
              <div className="timer">{formatTime(elapsed)}</div>
              <div className="status-text">
                {recording ? 'Meeting in progress — All audio is being recorded' : 'Initializing...'}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar — Participants */}
        <div className="meeting-room-sidebar">
          <h3>Participants ({meeting.participants?.length || 0})</h3>
          {meeting.participants?.map(p => (
            <div key={p.id} className="participant-item">
              <div className="participant-avatar">
                {p.user_name.split(' ').map(n => n[0]).join('').toUpperCase()}
              </div>
              <div>
                <div className="participant-name">{p.user_name}</div>
                <div className="participant-role">{p.role_in_meeting}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div className="meeting-room-controls">
        <button className={`control-btn control-btn-mic ${muted ? 'muted' : ''}`} onClick={toggleMute} title={muted ? 'Unmute' : 'Mute'}>
          {muted ? '🔇' : '🎤'}
        </button>
        <button className="control-btn control-btn-end" onClick={endMeeting} disabled={ending} title="End Meeting">
          📞
        </button>
      </div>
    </div>
  );
}
