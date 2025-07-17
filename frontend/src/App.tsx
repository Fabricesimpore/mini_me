import React, { useState } from 'react';
import Login from './components/Login';
import Register from './components/Register';
import { useAuth } from './components/AuthContext';
import CognitiveProfile from './components/CognitiveProfile';
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

const App: React.FC = () => {
  const [showLogin, setShowLogin] = useState(true);
  const { user, login, logout } = useAuth();

  const handleLoginSuccess = (token: string, user: any) => {
    login(token, user);
  };

  const handleRegisterSuccess = () => {
    setShowLogin(true);
  };

  if (user) {
    return (
      <div>
        <h2>Welcome, {user.name || user.email}!</h2>
        <p>You are logged in.</p>
        <button onClick={logout}>Logout</button>
        <CognitiveProfile />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto' }}>
      <div style={{ marginBottom: 16 }}>
        <button onClick={() => setShowLogin(true)} disabled={showLogin}>
          Login
        </button>
        <button onClick={() => setShowLogin(false)} disabled={!showLogin}>
          Register
        </button>
      </div>
      {showLogin ? (
        <Login onLoginSuccess={handleLoginSuccess} />
      ) : (
        <Register onRegisterSuccess={handleRegisterSuccess} />
      )}
    </div>
  );
};

export default App;
