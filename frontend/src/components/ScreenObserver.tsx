import React, { useState, useEffect } from 'react';
import { Monitor, Play, Square, TrendingUp, Clock, Target, AlertCircle, Settings } from 'lucide-react';
import { api } from '../services/api';

interface CaptureStatus {
  active: boolean;
  capture_interval?: number;
}

interface ActivitySummary {
  analysis_summary?: {
    date: string;
    average_productivity?: number;
    average_focus?: number;
    activity_breakdown: Record<string, number>;
    recommendations: string[];
  };
  time_range?: {
    start: string;
    end: string;
  };
}

interface CaptureSettings {
  capture_interval: number;
  analysis_interval: number;
}

const ScreenObserver: React.FC = () => {
  const [status, setStatus] = useState<CaptureStatus>({ active: false });
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<ActivitySummary | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<CaptureSettings>({
    capture_interval: 30,
    analysis_interval: 300
  });

  useEffect(() => {
    checkStatus();
    loadSummary();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/screen-observer/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };

  const loadSummary = async () => {
    try {
      const response = await api.get('/api/screen-observer/activity-summary?hours=24');
      setSummary(response.data);
    } catch (error) {
      console.error('Error loading summary:', error);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      await api.post('/api/screen-observer/start');
      await checkStatus();
    } catch (error) {
      console.error('Error starting capture:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await api.post('/api/screen-observer/stop');
      await checkStatus();
    } catch (error) {
      console.error('Error stopping capture:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCaptureOnce = async () => {
    setLoading(true);
    try {
      const response = await api.post('/api/screen-observer/capture-once');
      if (response.data.status === 'success') {
        // Refresh summary after capture
        await loadSummary();
      }
    } catch (error) {
      console.error('Error capturing screenshot:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSettings = async () => {
    try {
      await api.post('/api/screen-observer/settings', settings);
      setShowSettings(false);
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const getActivityColor = (activity: string) => {
    const colors: Record<string, string> = {
      coding: 'bg-purple-500',
      browsing: 'bg-blue-500',
      reading: 'bg-green-500',
      communication: 'bg-yellow-500',
      document_work: 'bg-indigo-500',
      other: 'bg-gray-500'
    };
    return colors[activity] || 'bg-gray-500';
  };

  const formatPercentage = (value?: number) => {
    if (value === undefined) return '0%';
    return `${Math.round(value * 100)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Monitor className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Screen Activity Observer</h3>
              <p className="text-sm text-gray-600">
                {status.active
                  ? `Capturing every ${status.capture_interval} seconds`
                  : 'Monitor your screen activity patterns'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {status.active ? (
              <button
                onClick={handleStop}
                disabled={loading}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Square className="h-4 w-4" />
                Stop
              </button>
            ) : (
              <button
                onClick={handleStart}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Play className="h-4 w-4" />
                Start
              </button>
            )}
            
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              <Settings className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-6 bg-gray-50 border-b">
          <h4 className="font-semibold mb-4">Capture Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Capture Interval (seconds)
              </label>
              <input
                type="number"
                min="10"
                max="300"
                value={settings.capture_interval}
                onChange={(e) => setSettings({
                  ...settings,
                  capture_interval: parseInt(e.target.value)
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Analysis Interval (seconds)
              </label>
              <input
                type="number"
                min="60"
                max="1800"
                value={settings.analysis_interval}
                onChange={(e) => setSettings({
                  ...settings,
                  analysis_interval: parseInt(e.target.value)
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={() => setShowSettings(false)}
              className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdateSettings}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Save Settings
            </button>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="p-6 border-b">
        <div className="flex gap-3">
          <button
            onClick={handleCaptureOnce}
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
          >
            <Monitor className="h-4 w-4" />
            Capture Once
          </button>
          
          <button
            onClick={loadSummary}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
          >
            <TrendingUp className="h-4 w-4" />
            Refresh Summary
          </button>
        </div>
      </div>

      {/* Activity Summary */}
      {summary?.analysis_summary && (
        <div className="p-6 space-y-6">
          <h4 className="font-semibold">Activity Analysis</h4>
          
          {/* Productivity Scores */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-green-700">Productivity Score</span>
                <Target className="h-4 w-4 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-green-900">
                {formatPercentage(summary.analysis_summary.average_productivity)}
              </div>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-700">Focus Score</span>
                <Clock className="h-4 w-4 text-blue-600" />
              </div>
              <div className="text-2xl font-bold text-blue-900">
                {formatPercentage(summary.analysis_summary.average_focus)}
              </div>
            </div>
          </div>

          {/* Activity Breakdown */}
          {Object.keys(summary.analysis_summary.activity_breakdown).length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-3">Activity Breakdown</h5>
              <div className="space-y-2">
                {Object.entries(summary.analysis_summary.activity_breakdown).map(([activity, count]) => {
                  const total = Object.values(summary.analysis_summary!.activity_breakdown).reduce((a, b) => a + b, 0);
                  const percentage = total > 0 ? (count / total) * 100 : 0;
                  
                  return (
                    <div key={activity} className="flex items-center gap-3">
                      <span className="text-sm text-gray-600 w-24">{activity}</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-4 relative">
                        <div
                          className={`h-full rounded-full ${getActivityColor(activity)}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600 w-12 text-right">
                        {percentage.toFixed(0)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {summary.analysis_summary.recommendations.length > 0 && (
            <div className="bg-amber-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <h5 className="font-medium text-amber-900">Recommendations</h5>
              </div>
              <ul className="space-y-1">
                {summary.analysis_summary.recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-amber-800">
                    • {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Privacy Notice */}
      <div className="p-4 bg-gray-50 text-xs text-gray-600 border-t">
        <p>
          🔒 Your screen captures are processed locally and stored securely. 
          Only activity patterns are analyzed, not specific content.
        </p>
      </div>
    </div>
  );
};

export default ScreenObserver;