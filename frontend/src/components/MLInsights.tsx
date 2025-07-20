import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, MessageSquare, Zap, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface ModelStatus {
  behavioral_pattern: {
    trained: boolean;
    last_training?: {
      timestamp: string;
      result: any;
    };
  };
  communication_style: {
    trained: boolean;
    last_training?: {
      timestamp: string;
      result: any;
    };
  };
}

interface BehavioralInsights {
  behavioral_patterns: Array<{ pattern: string; frequency: number }>;
  communication_style?: any;
  recommendations: string[];
}

interface CurrentBehavior {
  primary_pattern: string;
  confidence: number;
  all_predictions: Array<{ pattern: string; confidence: number }>;
}

const MLInsights: React.FC = () => {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [insights, setInsights] = useState<BehavioralInsights | null>(null);
  const [currentBehavior, setCurrentBehavior] = useState<CurrentBehavior | null>(null);
  const [training, setTraining] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadModelStatus();
    loadInsights();
  }, []);

  const loadModelStatus = async () => {
    try {
      const response = await api.get('/api/ml/models/status');
      setModelStatus(response.data.models);
    } catch (error) {
      console.error('Error loading model status:', error);
    }
  };

  const loadInsights = async () => {
    try {
      const response = await api.get('/api/ml/insights');
      setInsights(response.data.insights);
    } catch (error) {
      console.error('Error loading insights:', error);
    }
  };

  const analyzeCurrentBehavior = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/ml/analyze/current-behavior');
      if (response.data.status === 'success') {
        setCurrentBehavior(response.data.analysis);
      }
    } catch (error) {
      console.error('Error analyzing current behavior:', error);
    } finally {
      setLoading(false);
    }
  };

  const trainModel = async (modelType: string) => {
    setTraining(modelType);
    try {
      const endpoint = modelType === 'behavioral' 
        ? '/api/ml/train/behavioral' 
        : '/api/ml/train/communication';
      
      const response = await api.post(endpoint);
      if (response.data.status === 'success') {
        await loadModelStatus();
        await loadInsights();
      }
    } catch (error) {
      console.error(`Error training ${modelType} model:`, error);
    } finally {
      setTraining(null);
    }
  };

  const trainAllModels = async () => {
    setTraining('all');
    try {
      const response = await api.post('/api/ml/train/all');
      if (response.data.status === 'success' || response.data.status === 'partial_success') {
        await loadModelStatus();
        await loadInsights();
      }
    } catch (error) {
      console.error('Error training all models:', error);
    } finally {
      setTraining(null);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getPatternIcon = (pattern: string) => {
    const icons: Record<string, string> = {
      productive_flow: '🚀',
      deep_focus: '🎯',
      multitasking: '🔄',
      communication_heavy: '💬',
      creative_work: '🎨',
      distracted_browsing: '🌐',
      learning_research: '📚',
      administrative_tasks: '📋',
      break_leisure: '☕',
      meeting_collaboration: '👥'
    };
    return icons[pattern] || '📊';
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">ML Insights</h3>
              <p className="text-sm text-gray-600">
                AI-powered analysis of your behavior patterns
              </p>
            </div>
          </div>
          
          <button
            onClick={trainAllModels}
            disabled={training === 'all'}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
          >
            {training === 'all' ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Training...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                Train All Models
              </>
            )}
          </button>
        </div>
      </div>

      {/* Model Status */}
      {modelStatus && (
        <div className="p-6 border-b">
          <h4 className="font-semibold mb-4">Model Status</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Behavioral Pattern Model */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-indigo-600" />
                  <span className="font-medium">Behavioral Pattern Model</span>
                </div>
                {modelStatus.behavioral_pattern.trained ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-amber-600" />
                )}
              </div>
              
              {modelStatus.behavioral_pattern.last_training ? (
                <div className="text-sm text-gray-600">
                  <p>Last trained: {formatTimestamp(modelStatus.behavioral_pattern.last_training.timestamp)}</p>
                  <p>Accuracy: {(modelStatus.behavioral_pattern.last_training.result.final_accuracy * 100).toFixed(1)}%</p>
                </div>
              ) : (
                <p className="text-sm text-gray-500">Not trained yet</p>
              )}
              
              <button
                onClick={() => trainModel('behavioral')}
                disabled={training === 'behavioral'}
                className="mt-3 w-full px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 disabled:opacity-50 text-sm"
              >
                {training === 'behavioral' ? 'Training...' : 'Train Model'}
              </button>
            </div>

            {/* Communication Style Model */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-blue-600" />
                  <span className="font-medium">Communication Style Model</span>
                </div>
                {modelStatus.communication_style.trained ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-amber-600" />
                )}
              </div>
              
              {modelStatus.communication_style.last_training ? (
                <div className="text-sm text-gray-600">
                  <p>Last trained: {formatTimestamp(modelStatus.communication_style.last_training.timestamp)}</p>
                  <p>Messages analyzed: {modelStatus.communication_style.last_training.result.samples_analyzed}</p>
                </div>
              ) : (
                <p className="text-sm text-gray-500">Not trained yet</p>
              )}
              
              <button
                onClick={() => trainModel('communication')}
                disabled={training === 'communication'}
                className="mt-3 w-full px-3 py-1.5 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50 text-sm"
              >
                {training === 'communication' ? 'Training...' : 'Train Model'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Current Behavior Analysis */}
      <div className="p-6 border-b">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold">Current Activity Analysis</h4>
          <button
            onClick={analyzeCurrentBehavior}
            disabled={loading}
            className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 text-sm flex items-center gap-2"
          >
            {loading ? (
              <>
                <RefreshCw className="h-3 w-3 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <RefreshCw className="h-3 w-3" />
                Analyze Now
              </>
            )}
          </button>
        </div>
        
        {currentBehavior ? (
          <div className="space-y-3">
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-700">Current Pattern</p>
                  <p className="text-lg font-semibold text-purple-900 flex items-center gap-2">
                    <span>{getPatternIcon(currentBehavior.primary_pattern)}</span>
                    {currentBehavior.primary_pattern.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-purple-700">Confidence</p>
                  <p className="text-lg font-semibold text-purple-900">
                    {(currentBehavior.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            </div>
            
            {currentBehavior.all_predictions.length > 1 && (
              <div className="text-sm text-gray-600">
                <p className="mb-1">Other possibilities:</p>
                {currentBehavior.all_predictions.slice(1).map((pred, idx) => (
                  <div key={idx} className="flex justify-between text-xs">
                    <span>{pred.pattern.replace(/_/g, ' ')}</span>
                    <span>{(pred.confidence * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Click "Analyze Now" to see your current activity pattern</p>
        )}
      </div>

      {/* Behavioral Insights */}
      {insights && (
        <div className="p-6 space-y-4">
          <h4 className="font-semibold">Behavioral Insights</h4>
          
          {/* Pattern Distribution */}
          {insights.behavioral_patterns.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700 mb-3">Common Patterns</p>
              <div className="space-y-2">
                {insights.behavioral_patterns.map((pattern, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm">
                      <span>{getPatternIcon(pattern.pattern)}</span>
                      {pattern.pattern.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className="text-sm text-gray-600">{pattern.frequency} times</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Communication Style */}
          {insights.communication_style && (
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-700 mb-2">Communication Style</p>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="text-blue-600">Primary Style:</span>{' '}
                  {insights.communication_style.primary_style.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
                <p>
                  <span className="text-blue-600">Formality:</span>{' '}
                  {insights.communication_style.formality_level}
                </p>
                <p>
                  <span className="text-blue-600">Directness:</span>{' '}
                  {insights.communication_style.directness_level}
                </p>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {insights.recommendations.length > 0 && (
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm font-medium text-green-700 mb-2">Personalized Recommendations</p>
              <ul className="space-y-1">
                {insights.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-green-800">
                    • {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MLInsights;