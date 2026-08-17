import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import EmployeeDashboard from './pages/EmployeeDashboard';
import ManagerDashboard from './pages/ManagerDashboard';
import AdminDashboard from './pages/AdminDashboard';
import Meetings from './pages/Meetings';
import MeetingDetails from './pages/MeetingDetails';
import MeetingRoom from './pages/MeetingRoom';
import Tasks from './pages/Tasks';
import TaskDetails from './pages/TaskDetails';
import TaskReview from './pages/TaskReview';
import Profile from './pages/Profile';
import Layout from './components/Layout';

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" />;
  return children;
}

function DashboardRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (user.role === 'ADMIN') return <Navigate to="/admin" />;
  if (user.role === 'MANAGER') return <Navigate to="/manager" />;
  return <Navigate to="/employee" />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<DashboardRedirect />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/employee" element={<ProtectedRoute><EmployeeDashboard /></ProtectedRoute>} />
        <Route path="/manager" element={<ProtectedRoute roles={['MANAGER', 'ADMIN']}><ManagerDashboard /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute roles={['ADMIN']}><AdminDashboard /></ProtectedRoute>} />
        <Route path="/meetings" element={<ProtectedRoute><Meetings /></ProtectedRoute>} />
        <Route path="/meetings/:id" element={<ProtectedRoute><MeetingDetails /></ProtectedRoute>} />
        <Route path="/meetings/:id/room" element={<ProtectedRoute><MeetingRoom /></ProtectedRoute>} />
        <Route path="/meetings/:id/review" element={<ProtectedRoute roles={['MANAGER', 'ADMIN']}><TaskReview /></ProtectedRoute>} />
        <Route path="/tasks" element={<ProtectedRoute><Tasks /></ProtectedRoute>} />
        <Route path="/tasks/:id" element={<ProtectedRoute><TaskDetails /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
