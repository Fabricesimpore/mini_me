import React, { useState, useEffect } from 'react';
import { Brain, Sparkles, RefreshCw, User, Briefcase, MessageSquare, Heart, Target, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PersonalityTrait {
  score: number;
  level: string;
  description: string;
}

interface ProfileData {
  personality: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
  };
  communication: {
    formality: number;
    verbosity: number;
    preferred_channels: string[];
  };
  decision_making: {
    speed: number;
    risk_tolerance: number;
    style: string;
    analytical_score: number;
  };
  work_preferences: {
    style: { [key: string]: number };
    peak_hours: string[];
    task_types: string[];
  };
  interests: {
    categories: { [key: string]: number };
    expertise: string[];
  };
  emotional_patterns: {
    stability: number;
    stress_triggers: string[];
    coping_mechanisms: string[];
  };
  social_preferences: {
    energy: number;
    introvert_extrovert: string;
    relationship_depth: number;
  };
  metadata: {
    confidence: number;
    last_updated: string;
    data_points: number;
    analysis_count: number;
  };
}

interface Insight {
  type: string;
  insight: string;
  recommendations: string[];
}

const CognitiveProfile: React.FC = () => {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'personality' | 'work' | 'social' | 'insights'>('overview');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/profile/');
      if (response.data.status === 'success' && response.data.profile) {
        setProfile(response.data.profile);
        
        // Fetch insights
        const insightsResponse = await api.get('/api/profile/insights');
        if (insightsResponse.data.insights) {
          setInsights(insightsResponse.data.insights);
        }
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeProfile = async (forceFullAnalysis: boolean = false) => {
    setAnalyzing(true);
    try {
      const response = await api.post('/api/profile/analyze', null, {
        params: { force_full_analysis: forceFullAnalysis }
      });
      
      if (response.data.status === 'success') {
        setProfile(response.data.profile);
        await fetchProfile(); // Refresh with insights
      }
    } catch (error) {
      console.error('Error analyzing profile:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const getPersonalityData = () => {
    if (!profile) return [];
    
    return [
      { trait: 'Openness', value: profile.personality.openness * 100, fullMark: 100 },
      { trait: 'Conscientiousness', value: profile.personality.conscientiousness * 100, fullMark: 100 },
      { trait: 'Extraversion', value: profile.personality.extraversion * 100, fullMark: 100 },
      { trait: 'Agreeableness', value: profile.personality.agreeableness * 100, fullMark: 100 },
      { trait: 'Emotional Stability', value: (1 - profile.personality.neuroticism) * 100, fullMark: 100 }
    ];
  };

  const getInterestData = () => {
    if (!profile || !profile.interests.categories) return [];
    
    return Object.entries(profile.interests.categories)
      .slice(0, 5)
      .map(([category, score]) => ({
        category: category.charAt(0).toUpperCase() + category.slice(1),
        score: score * 100
      }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Brain className="h-12 w-12 text-purple-600 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600">Loading cognitive profile...</p>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <Brain className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4">No Cognitive Profile Yet</h2>
          <p className="text-gray-600 mb-6">
            Analyze your memories and interactions to build your cognitive profile.
          </p>
          <button
            onClick={() => analyzeProfile(true)}
            disabled={analyzing}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
          >
            {analyzing ? (
              <>
                <RefreshCw className="h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                Analyze My Profile
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
              <Brain className="h-8 w-8 text-purple-600" />
              Your Cognitive Profile
            </h1>
            <p className="text-gray-600">
              AI-powered analysis of your personality, preferences, and patterns
            </p>
          </div>
          <button
            onClick={() => analyzeProfile(false)}
            disabled={analyzing}
            className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
          >
            {analyzing ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Update Profile
              </>
            )}
          </button>
        </div>
        
        {/* Confidence Badge */}
        <div className="mt-4 flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-32 bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full"
                style={{ width: `${profile.metadata.confidence * 100}%` }}
              />
            </div>
            <span className="text-gray-600">
              {(profile.metadata.confidence * 100).toFixed(0)}% confidence
            </span>
          </div>
          <span className="text-gray-500">
            Based on {profile.metadata.data_points} memories
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b mb-6">
        <div className="flex gap-6">
          {(['overview', 'personality', 'work', 'social', 'insights'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 px-1 border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            {/* Quick Stats */}
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="flex items-center gap-3">
                  <User className="h-8 w-8 text-blue-600" />
                  <div>
                    <p className="text-sm text-gray-600">Personality Type</p>
                    <p className="font-semibold capitalize">
                      {profile.social_preferences.introvert_extrovert}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="flex items-center gap-3">
                  <Briefcase className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">Work Style</p>
                    <p className="font-semibold">
                      {profile.decision_making.style}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-8 w-8 text-purple-600" />
                  <div>
                    <p className="text-sm text-gray-600">Communication</p>
                    <p className="font-semibold">
                      {profile.communication.formality > 0.5 ? 'Formal' : 'Casual'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="flex items-center gap-3">
                  <Heart className="h-8 w-8 text-red-600" />
                  <div>
                    <p className="text-sm text-gray-600">Emotional</p>
                    <p className="font-semibold">
                      {profile.emotional_patterns.stability > 0.7 ? 'Stable' : 'Variable'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg p-6 shadow">
                <h3 className="text-lg font-semibold mb-4">Personality Traits</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={getPersonalityData()}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="trait" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Traits"
                      dataKey="value"
                      stroke="#8b5cf6"
                      fill="#8b5cf6"
                      fillOpacity={0.6}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg p-6 shadow">
                <h3 className="text-lg font-semibold mb-4">Top Interests</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getInterestData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="score" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}

        {activeTab === 'personality' && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg p-6 shadow">
              <h3 className="text-lg font-semibold mb-4">Big Five Personality Traits</h3>
              <div className="space-y-4">
                {Object.entries(profile.personality).map(([trait, score]) => (
                  <div key={trait}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium capitalize">
                        {trait === 'neuroticism' ? 'Emotional Stability' : trait}
                      </span>
                      <span className="text-sm text-gray-600">
                        {trait === 'neuroticism' 
                          ? ((1 - score) * 100).toFixed(0) 
                          : (score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-purple-600 h-2 rounded-full"
                        style={{
                          width: `${trait === 'neuroticism' ? (1 - score) * 100 : score * 100}%`
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow">
              <h3 className="text-lg font-semibold mb-4">Behavioral Patterns</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Decision Making</h4>
                  <p className="text-sm text-gray-600">
                    You tend to be <span className="font-semibold">{profile.decision_making.style}</span> in your approach,
                    with a <span className="font-semibold">{profile.decision_making.speed > 0.5 ? 'fast' : 'deliberate'}</span> decision-making speed.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Risk Profile</h4>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">Risk Averse</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-green-500 to-red-500 h-2 rounded-full"
                        style={{ width: `${profile.decision_making.risk_tolerance * 100}%` }}
                      />
                    </div>
                    <span className="text-sm">Risk Seeking</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'work' && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg p-6 shadow">
              <h3 className="text-lg font-semibold mb-4">Work Preferences</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Peak Productivity Hours</h4>
                  <div className="flex gap-2">
                    {profile.work_preferences.peak_hours.map((hour) => (
                      <span
                        key={hour}
                        className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
                      >
                        {hour}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Preferred Task Types</h4>
                  <div className="flex flex-wrap gap-2">
                    {profile.work_preferences.task_types.map((task) => (
                      <span
                        key={task}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                      >
                        {task}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Work Style</h4>
                  <div className="space-y-2">
                    {Object.entries(profile.work_preferences.style).map(([style, value]) => (
                      <div key={style}>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm capitalize">{style}</span>
                          <span className="text-sm text-gray-600">{(value * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${value * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow">
              <h3 className="text-lg font-semibold mb-4">Areas of Expertise</h3>
              <div className="space-y-2">
                {profile.interests.expertise.map((area, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                  >
                    <Target className="h-5 w-5 text-purple-600" />
                    <span className="capitalize">{area}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'social' && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg p-6 shadow">
              <h3 className="text-lg font-semibold mb-4">Social Preferences</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Social Energy</h4>
                  <p className="text-sm text-gray-600 mb-2">
                    You are primarily {profile.social_preferences.introvert_extrovert === 'extrovert' ? 'an' : 'an'} <span className="font-semibold">{profile.social_preferences.introvert_extrovert}</span>
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">Introvert</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-yellow-500 h-2 rounded-full"
                        style={{ width: `${profile.social_preferences.energy * 100}%` }}
                      />
                    </div>
                    <span className="text-sm">Extrovert</span>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Relationship Style</h4>
                  <p className="text-sm text-gray-600">
                    You prefer {profile.social_preferences.relationship_depth > 0.5 ? 'fewer, deeper relationships' : 'a broader network of connections'}
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Communication Preferences</h4>
                  <div className="flex gap-2">
                    {profile.communication.preferred_channels.map((channel) => (
                      <span
                        key={channel}
                        className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                      >
                        {channel}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow">
              <h3 className="text-lg font-semibold mb-4">Emotional Intelligence</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Emotional Stability</h4>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${profile.emotional_patterns.stability * 100}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600">
                    {profile.emotional_patterns.stability > 0.7 ? 'High' : profile.emotional_patterns.stability > 0.4 ? 'Moderate' : 'Variable'} emotional stability
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Stress Triggers</h4>
                  <div className="flex flex-wrap gap-2">
                    {profile.emotional_patterns.stress_triggers.map((trigger) => (
                      <span
                        key={trigger}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm"
                      >
                        {trigger}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Coping Mechanisms</h4>
                  <div className="flex flex-wrap gap-2">
                    {profile.emotional_patterns.coping_mechanisms.map((mechanism) => (
                      <span
                        key={mechanism}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                      >
                        {mechanism}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="space-y-4">
            {insights.length > 0 ? (
              insights.map((insight, index) => (
                <div key={index} className="bg-white rounded-lg p-6 shadow">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Sparkles className="h-6 w-6 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold mb-2 capitalize">{insight.type} Insight</h4>
                      <p className="text-gray-700 mb-3">{insight.insight}</p>
                      {insight.recommendations.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-gray-600 mb-1">Recommendations:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {insight.recommendations.map((rec, recIndex) => (
                              <li key={recIndex} className="text-sm text-gray-600">{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-gray-50 rounded-lg p-8 text-center">
                <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  No insights available yet. Continue using the platform to generate personalized insights.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CognitiveProfile;