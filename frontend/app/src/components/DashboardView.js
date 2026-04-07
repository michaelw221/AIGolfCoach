import React, { useState, useEffect } from 'react';
import { getAuthHeader } from '../services/auth';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

// --- Reusable Graph Component ---
function MetricTrendChart({ title, history, metricKey }) {
  const chartData = {
    labels: history.map(s => new Date(s.created_at).toLocaleDateString()),
    datasets: [{
      label: title,
      data: history.map(s => s.analysis_results?.metrics?.[metricKey] || 0),
      fill: false,
      borderColor: 'var(--accent)',
      tension: 0.1,
    }],
  };
  return <div className="card" style={{ padding: '1rem' }}><Line data={chartData} options={{ responsive: true, plugins: { title: { display: true, text: title } } }} /></div>;
}


// --- Main Dashboard Component ---
export default function DashboardView({ isActive }) {
  const [activeTab, setActiveTab] = useState('details');
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passMsg, setPassMsg] = useState({ text: '', type: '' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userRes, historyRes] = await Promise.all([
          fetch('http://localhost:8000/api/users/me', { headers: getAuthHeader() }),
          fetch('http://localhost:8000/api/swings', { headers: getAuthHeader() }),
        ]);

        if (!userRes.ok || !historyRes.ok) throw new Error("Failed to fetch data");

        const userData = await userRes.json();
        const historyData = await historyRes.json();

        setUser(userData);
        
        // Filter for valid swings and take only the last 15
        const validSwings = historyData.filter(s => s.status === 'complete' && s.analysis_results?.metrics);
        const recentSwings = validSwings.slice(-15);
        setHistory(recentSwings);
        
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      } finally {
        setLoading(false);
      }
    };

    if (isActive) {
      fetchData();
    }
  }, [isActive]);

  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    setPassMsg({ text: 'Updating...', type: 'info' });

    try {
      const response = await fetch('http://localhost:8000/api/users/me/password', {
        method: 'PUT',
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setPassMsg({ text: '✅ Password updated successfully!', type: 'success' });
        setCurrentPassword(''); // Clear the input fields
        setNewPassword('');
      } else {
        setPassMsg({ text: `❌ ${data.detail || 'Failed to update'}`, type: 'error' });
      }
    } catch (err) {
      setPassMsg({ text: '❌ Network error', type: 'error' });
    }
  };

  if (loading) {
    return (
      <div className="dashboard-layout">
        <div className="sidebar">
          <button className="btn-accent">Details</button>
          <button className="btn-accent">Trends</button>
        </div>
        <div className="dashboard-content">
          <p>Loading Account Data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <button className="btn-dark" onClick={() => setActiveTab('details')}>Details</button>
        <button className="btn-dark" onClick={() => setActiveTab('trends')}>Trends</button>
      </div>
      
      {/* Main Content */}
      <div className="dashboard-content">
        {activeTab === 'details' ? (
          <div>
            <h3>Account Details</h3>
            <div style={{ marginTop: '2rem' }}>
              <p><strong>Username:</strong> {user?.username || 'N/A'}</p>
              <p><strong>Email:</strong> {user?.email || 'N/A'}</p>
            </div>
            <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--border)' }}/>
            <h4>Update Password</h4>
            <form onSubmit={handlePasswordUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '300px' }}>
              {passMsg.text && (
                <div style={{ color: passMsg.type === 'error' ? 'var(--error)' : 'var(--success)', fontSize: '0.9rem', fontWeight: 'bold' }}>
                  {passMsg.text}
                </div>
              )}
              <input 
                type="password" 
                className="auth-input" 
                placeholder="Current Password" 
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required 
              />
              <input 
                type="password" 
                className="auth-input" 
                placeholder="New Password" 
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required 
                minLength="6"
              />
              <button type="submit" className="btn-accent">Save Changes</button>
            </form>

          </div>
        ) : (
          <div>
            <h3>Improvement Trends</h3>
            <p style={{ color: 'var(--text-light)', marginBottom: '2rem' }}>
              Track how your key biomechanical metrics have changed over time.
            </p>
            <div className="placeholder-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <MetricTrendChart title="Head Sway (cm)" history={history} metricKey="max_head_sway_cm" />
              <MetricTrendChart title="Spine Angle Change (°)" history={history} metricKey="spine_angle_change" />
              <MetricTrendChart title="X-Factor Angle (°)" history={history} metricKey="x_factor_angle" />
              <MetricTrendChart title="Knee Flex Change (°)" history={history} metricKey="knee_flex_change" />
              <MetricTrendChart title="Hip Slide (cm)" history={history} metricKey="max_hip_slide_cm" />
              <MetricTrendChart title="Backswing Length (°)" history={history} metricKey="backswing_length_angle" />
              <MetricTrendChart title="Lead Arm Angle at Impact (°)" history={history} metricKey="lead_arm_angle_impact" />
              <MetricTrendChart title="Hand Path Angle (°)" history={history} metricKey="initial_hand_path_angle" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}