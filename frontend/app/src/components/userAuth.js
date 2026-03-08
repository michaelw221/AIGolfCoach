import React, { useState } from 'react';
import { saveToken } from '../services/auth';

function UserAuth({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const url = isLogin ? 'http://localhost:8000/api/auth/login' : 'http://localhost:8000/api/users';
    
    // Login uses x-www-form-urlencoded (OAuth2 requirement), Signup uses JSON
    const body = isLogin 
      ? new URLSearchParams({ username: formData.username, password: formData.password })
      : JSON.stringify(formData);

    const headers = isLogin 
      ? { 'Content-Type': 'application/x-www-form-urlencoded' }
      : { 'Content-Type': 'application/json' };

    try {
      const response = await fetch(url, { method: 'POST', headers, body });
      const data = await response.json();

      if (response.ok) {
        if (isLogin) {
          saveToken(data.access_token);
          onLoginSuccess();
        } else {
          alert("Account created! Please log in.");
          setIsLogin(true);
        }
      } else {
        alert(data.detail || "Authentication failed");
      }
    } catch (err) { console.error(err); }
  };

  return (
    <div className="card" style={{ maxWidth: '400px', margin: '2rem auto', padding: '1rem' }}>
      <h3>{isLogin ? 'Login' : 'Create Account'}</h3>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="Username" required 
          onChange={e => setFormData({...formData, username: e.target.value})} />
        
        {!isLogin && <input type="email" placeholder="Email" required 
          onChange={e => setFormData({...formData, email: e.target.value})} />}
        
        <input type="password" placeholder="Password" required 
          onChange={e => setFormData({...formData, password: e.target.value})} />
        
        <button type="submit">{isLogin ? 'Login' : 'Sign Up'}</button>
      </form>
      <button className="outline" onClick={() => setIsLogin(!isLogin)}>
        {isLogin ? 'Need an account? Sign Up' : 'Already have an account? Login'}
      </button>
    </div>
  );
}

export default UserAuth;