import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import BehavioralData from './pages/BehavioralData'
import Memory from './pages/Memory'
import Integrations from './pages/Integrations'
import Settings from './pages/Settings'
import Chat from './pages/Chat'
import { useAuthStore } from './store/authStore'
import { initializeWebSocket } from './services/websocket'

function App() {
  const { isAuthenticated, user } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated && user) {
      // Initialize WebSocket connection when user logs in
      // Disabled for now during initial setup
      // initializeWebSocket(user.id)
    }
  }, [isAuthenticated, user])

  return (
    <Routes>
      <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
      <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/" />} />
      
      <Route
        path="/"
        element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}
      >
        <Route index element={<Dashboard />} />
        <Route path="chat" element={<Chat />} />
        <Route path="behavioral" element={<BehavioralData />} />
        <Route path="memory" element={<Memory />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App