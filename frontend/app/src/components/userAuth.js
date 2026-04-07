import React, { useState } from 'react';
import { saveToken } from '../services/auth';

export default function UserAuth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(false);
  const[formData, setFormData] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const url = isLogin ? 'http://localhost:8000/api/auth/login' : 'http://localhost:8000/api/users';
    
    const body = isLogin 
      ? new URLSearchParams({ username: formData.username, password: formData.password })
      : JSON.stringify(formData);

    const headers = isLogin ? { 'Content-Type': 'application/x-www-form-urlencoded' } : { 'Content-Type': 'application/json' };

    try {
      const response = await fetch(url, { method: 'POST', headers, body });
      const data = await response.json();

      if (response.ok) {
        if (isLogin) {
          saveToken(data.access_token);
          onLogin();
        } else {
          alert("Account created! Please log in.");
          setIsLogin(true);
        }
      } else {
        setError(data.detail || "Authentication failed");
      }
    } catch (err) { setError("Network error"); }
  };

  return (
    <div className="card" style={{ maxWidth: '400px', margin: '10vh auto' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>{isLogin ? 'Login' : 'Create Account'}</h2>
      {error && <p style={{ color: 'var(--error)', fontSize: '0.9rem', textAlign: 'center' }}>{error}</p>}
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <input type="text" className="auth-input" placeholder="Username" required onChange={e => setFormData({...formData, username: e.target.value})} />
        {!isLogin && <input type="email" className="auth-input" placeholder="Email" required onChange={e => setFormData({...formData, email: e.target.value})} />}
        <input type="password" className="auth-input" placeholder="Password" required onChange={e => setFormData({...formData, password: e.target.value})} />
        
        <button type="submit" className="btn-dark" style={{ marginTop: '1rem' }}>
          {isLogin ? 'Sign In' : 'Sign Up'}
        </button>
      </form>
      
      <div style={{ marginTop: '2rem', textAlign: 'center', cursor: 'pointer', color: 'var(--accent)', fontWeight: '600' }} onClick={() => setIsLogin(!isLogin)}>
        {isLogin ? 'Need an account? Sign Up' : 'Already have an account? Login'}
      </div>
    </div>
  );
}