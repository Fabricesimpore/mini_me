import React, { useState, useEffect } from 'react';
import { Lightbulb, Target, MessageSquare, Heart, GraduationCap, Users, Clock, ChevronRight, Star, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

interface Recommendation {
  type: string;
  title: string;
  description: string;
  action_items: string[];
  priority: 'high' | 'medium' | 'low';
  expected_impact: string;
  category?: string;
}

interface DecisionSupport {
  decision_framework: {
    steps: string[];
    time_allocation: Record<string, string>;
    key_considerations: string[];
  };
  confidence_factors: {
    strengths: string[];
    watch_points: string[];
    confidence_boosters: string[];
  };
  recommendations: Recommendation[];
}

const Recommendations: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('daily');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [decisionSupport, setDecisionSupport] = useState<DecisionSupport | null>(null);
  const [loading, setLoading] = useState(false);
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [decisionType, setDecisionType] = useState('');
  const [decisionDescription, setDecisionDescription] = useState('');

  useEffect(() => {
    loadRecommendations('daily');
  }, []);

  const loadRecommendations = async (type: string) => {
    setLoading(true);
    try {
      let response;
      switch (type) {
        case 'daily':
          response = await api.get('/api/recommendations/daily');
          setRecommendations(response.data.daily_recommendations || []);
          break;
        case 'productivity':
          response = await api.get('/api/recommendations/productivity');
          setRecommendations(response.data.recommendations || []);
          break;
        case 'communication':
          response = await api.get('/api/recommendations/communication');
          setRecommendations(response.data.recommendations || []);
          break;
        case 'wellness':
          response = await api.get('/api/recommendations/wellness');
          setRecommendations(response.data.recommendations || []);
          break;
        default:
          response = await api.get('/api/recommendations/general');
          const allRecs = response.data.recommendations || {};
          const flatRecs: Recommendation[] = [];
          Object.entries(allRecs).forEach(([category, recs]) => {
            if (Array.isArray(recs)) {
              recs.forEach(rec => {
                flatRecs.push({ ...rec, category });
              });
            }
          });
          setRecommendations(flatRecs);
      }
      setActiveTab(type);
    } catch (error) {
      console.error('Error loading recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const requestDecisionSupport = async () => {
    if (!decisionType) return;
    
    setLoading(true);
    try {
      const response = await api.post('/api/recommendations/decision-support', {
        decision_type: decisionType,
        description: decisionDescription,
        time_pressure: false
      });
      
      setDecisionSupport(response.data.decision_support);
      setShowDecisionModal(false);
      setDecisionType('');
      setDecisionDescription('');
    } catch (error) {
      console.error('Error getting decision support:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async (recommendationId: string, rating: number) => {
    try {
      await api.post('/api/recommendations/feedback', {
        recommendation_id: recommendationId,
        rating: rating,
        applied: rating >= 4
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, JSX.Element> = {
      productivity: <Target className="h-5 w-5" />,
      communication: <MessageSquare className="h-5 w-5" />,
      wellness: <Heart className="h-5 w-5" />,
      learning: <GraduationCap className="h-5 w-5" />,
      social: <Users className="h-5 w-5" />,
      daily: <Clock className="h-5 w-5" />
    };
    return icons[category] || <Lightbulb className="h-5 w-5" />;
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      high: 'border-red-500 bg-red-50',
      medium: 'border-yellow-500 bg-yellow-50',
      low: 'border-green-500 bg-green-50'
    };
    return colors[priority] || 'border-gray-500 bg-gray-50';
  };

  const getPriorityBadgeColor = (priority: string) => {
    const colors: Record<string, string> = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Personalized Recommendations</h1>
        <p className="text-gray-600">
          AI-powered suggestions based on your behavioral patterns and goals
        </p>
      </div>

      {/* Category Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'daily', label: 'Daily', icon: <Clock className="h-4 w-4" /> },
          { id: 'productivity', label: 'Productivity', icon: <Target className="h-4 w-4" /> },
          { id: 'communication', label: 'Communication', icon: <MessageSquare className="h-4 w-4" /> },
          { id: 'wellness', label: 'Wellness', icon: <Heart className="h-4 w-4" /> },
          { id: 'all', label: 'All Categories', icon: <Lightbulb className="h-4 w-4" /> }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => loadRecommendations(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.icon}
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Decision Support Button */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={() => setShowDecisionModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
        >
          <Lightbulb className="h-4 w-4" />
          Get Decision Support
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      )}

      {/* Recommendations List */}
      {!loading && recommendations.length > 0 && (
        <div className="space-y-4">
          {recommendations.map((rec, index) => (
            <div
              key={index}
              className={`border-l-4 rounded-lg p-6 shadow-sm ${getPriorityColor(rec.priority)}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3">
                  <div className="mt-1">
                    {getCategoryIcon(rec.category || activeTab)}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{rec.title}</h3>
                    <p className="text-gray-600 mt-1">{rec.description}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityBadgeColor(rec.priority)}`}>
                  {rec.priority} priority
                </span>
              </div>

              {/* Action Items */}
              <div className="ml-8 mb-3">
                <p className="text-sm font-medium text-gray-700 mb-2">Action Items:</p>
                <ul className="space-y-1">
                  {rec.action_items.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                      <ChevronRight className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Expected Impact */}
              <div className="ml-8 flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  <span className="font-medium">Expected Impact:</span> {rec.expected_impact}
                </p>
                
                {/* Feedback Stars */}
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-500 mr-2">Rate this:</span>
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => submitFeedback(`${activeTab}_${index}`, rating)}
                      className="text-gray-300 hover:text-yellow-400 transition-colors"
                    >
                      <Star className="h-4 w-4 fill-current" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Decision Support Display */}
      {decisionSupport && (
        <div className="mt-8 bg-indigo-50 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-indigo-900 mb-4">Decision Support Framework</h2>
          
          {/* Decision Steps */}
          <div className="mb-6">
            <h3 className="font-medium text-indigo-800 mb-2">Recommended Steps:</h3>
            <ol className="list-decimal list-inside space-y-1">
              {decisionSupport.decision_framework.steps.map((step, idx) => (
                <li key={idx} className="text-sm text-indigo-700">{step}</li>
              ))}
            </ol>
          </div>

          {/* Time Allocation */}
          {Object.keys(decisionSupport.decision_framework.time_allocation).length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium text-indigo-800 mb-2">Time Allocation:</h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(decisionSupport.decision_framework.time_allocation).map(([phase, time]) => (
                  <div key={phase} className="text-sm">
                    <span className="text-indigo-600 capitalize">{phase}:</span>
                    <span className="ml-2 font-medium text-indigo-900">{time}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence Factors */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-100 rounded-lg p-3">
              <h4 className="font-medium text-green-800 mb-1">Your Strengths</h4>
              <ul className="text-sm text-green-700 space-y-0.5">
                {decisionSupport.confidence_factors.strengths.map((strength, idx) => (
                  <li key={idx}>• {strength}</li>
                ))}
              </ul>
            </div>
            
            <div className="bg-yellow-100 rounded-lg p-3">
              <h4 className="font-medium text-yellow-800 mb-1">Watch Points</h4>
              <ul className="text-sm text-yellow-700 space-y-0.5">
                {decisionSupport.confidence_factors.watch_points.map((point, idx) => (
                  <li key={idx}>• {point}</li>
                ))}
              </ul>
            </div>
            
            <div className="bg-blue-100 rounded-lg p-3">
              <h4 className="font-medium text-blue-800 mb-1">Confidence Boosters</h4>
              <ul className="text-sm text-blue-700 space-y-0.5">
                {decisionSupport.confidence_factors.confidence_boosters.map((booster, idx) => (
                  <li key={idx}>• {booster}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Decision Support Modal */}
      {showDecisionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-semibold mb-4">Request Decision Support</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Decision Type
              </label>
              <select
                value={decisionType}
                onChange={(e) => setDecisionType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select type...</option>
                <option value="career">Career</option>
                <option value="financial">Financial</option>
                <option value="purchase">Purchase</option>
                <option value="personal">Personal</option>
                <option value="relationship">Relationship</option>
              </select>
            </div>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Decision Description
              </label>
              <textarea
                value={decisionDescription}
                onChange={(e) => setDecisionDescription(e.target.value)}
                placeholder="Briefly describe your decision..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                rows={3}
              />
            </div>
            
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDecisionModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={requestDecisionSupport}
                disabled={!decisionType || loading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Get Support
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Recommendations;