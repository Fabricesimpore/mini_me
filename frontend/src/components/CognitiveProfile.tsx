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

  if (loading) return <div>Loading cognitive profile...</div>;
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