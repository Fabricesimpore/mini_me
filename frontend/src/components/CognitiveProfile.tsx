import React, { useEffect, useState } from 'react';
import { useAuth } from './AuthContext';

const CognitiveProfile: React.FC = () => {
  const { user, token } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!user || !token) return;
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/users/${user.id}/cognitive-profile`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (response.status === 404) {
          setProfile(null);
          setError('404');
          return;
        }
        if (!response.ok) throw new Error('Failed to fetch profile');
        const data = await response.json();
        setProfile(data);
      } catch (err: any) {
        setError(err.message || 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [user, token]);

  // New: Profile creation form state
  const [form, setForm] = useState({
    communication_style: '',
    decision_patterns: '',
    value_system: '',
  });
  const [creating, setCreating] = useState(false);
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !token) return;
    setCreating(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/cognitive-profile`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          communication_style: { value: form.communication_style },
          decision_patterns: { value: form.decision_patterns },
          value_system: { value: form.value_system },
        }),
      });
      if (!response.ok) throw new Error('Failed to create profile');
      const data = await response.json();
      setProfile(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div>Loading cognitive profile...</div>;
  if (error === '404') return (
    <div>
      <p>No profile found. Create your cognitive profile!</p>
      <form onSubmit={handleCreate}>
        <div>
          <label>Communication Style:</label>
          <input name="communication_style" value={form.communication_style} onChange={handleChange} required />
        </div>
        <div>
          <label>Decision Patterns:</label>
          <input name="decision_patterns" value={form.decision_patterns} onChange={handleChange} required />
        </div>
        <div>
          <label>Value System:</label>
          <input name="value_system" value={form.value_system} onChange={handleChange} required />
        </div>
        <button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create Profile'}</button>
      </form>
      {error && error !== '404' && <div style={{ color: 'red' }}>Error: {error}</div>}
    </div>
  );
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;
  if (!profile) return <div>No profile data available.</div>;

  return (
    <div className="cognitive-profile">
      <h2>Your Cognitive Profile</h2>
      <div className="profile-sections">
        <div className="communication-style">
          <h3>Communication Style</h3>
          <pre>{JSON.stringify(profile.communication_style, null, 2)}</pre>
        </div>
        <div className="decision-patterns">
          <h3>Decision Patterns</h3>
          <pre>{JSON.stringify(profile.decision_patterns, null, 2)}</pre>
        </div>
        <div className="value-system">
          <h3>Value System</h3>
          <pre>{JSON.stringify(profile.value_system, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
};

export default CognitiveProfile; 