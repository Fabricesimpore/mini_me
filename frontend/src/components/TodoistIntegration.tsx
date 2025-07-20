import React, { useState, useEffect } from 'react';
import { CheckSquare, Check, AlertCircle, RefreshCw, Link2, TrendingUp, Target, Clock } from 'lucide-react';
import { api } from '../services/api';

interface TodoistStatus {
  connected: boolean;
  email?: string;
  active_tasks?: number;
  projects?: number;
  connected_at?: string;
}

interface TaskAnalysis {
  tasks_analyzed: number;
  task_patterns: {
    tasks_with_due_dates_percentage: number;
    overdue_tasks: number;
    upcoming_week_tasks: number;
    peak_productivity_hours: Array<{ hour: number; completions: number }>;
    average_daily_completions: number;
  };
  project_distribution: {
    inbox_tasks: number;
    project_count: number;
    top_projects: Array<{ name: string; tasks: number }>;
    uses_projects: boolean;
  };
  productivity_insights: {
    daily_average: number;
    weekly_pattern: Record<string, number>;
    completion_streak: number;
    most_productive_day: string;
  };
  priority_usage: {
    high_priority: number;
    medium_priority: number;
    low_priority: number;
    uses_priorities: boolean;
  };
}

interface Task {
  id: string;
  content: string;
  priority: number;
  due?: { date: string };
  project_id?: string;
  labels: string[];
}

const TodoistIntegration: React.FC = () => {
  const [status, setStatus] = useState<TodoistStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<TaskAnalysis | null>(null);
  const [tasksSummary, setTasksSummary] = useState<{
    today: Task[];
    overdue: Task[];
    counts: { today: number; overdue: number };
  } | null>(null);
  const [showTasks, setShowTasks] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/todoist/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Error checking Todoist status:', error);
      setStatus({ connected: false });
    }
  };

  const handleConnect = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/todoist/auth');
      // Open auth URL in new window
      window.open(response.data.auth_url, '_blank', 'width=600,height=600');
      
      // Poll for connection status
      const pollInterval = setInterval(async () => {
        const statusResponse = await api.get('/api/todoist/status');
        if (statusResponse.data.connected) {
          clearInterval(pollInterval);
          setStatus(statusResponse.data);
          setLoading(false);
        }
      }, 2000);
      
      // Stop polling after 2 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setLoading(false);
      }, 120000);
    } catch (error) {
      console.error('Error connecting Todoist:', error);
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const response = await api.post('/api/todoist/analyze');
      if (response.data.status === 'success') {
        setAnalysis(response.data.insights);
      }
    } catch (error) {
      console.error('Error analyzing tasks:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const loadTasksSummary = async () => {
    try {
      const response = await api.get('/api/todoist/tasks/summary');
      setTasksSummary(response.data);
      setShowTasks(true);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 4: return 'text-red-600';
      case 3: return 'text-orange-600';
      case 2: return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 4: return 'P1';
      case 3: return 'P2';
      case 2: return 'P3';
      default: return 'P4';
    }
  };

  if (!status) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <CheckSquare className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Todoist</h3>
              <p className="text-sm text-gray-600">
                {status.connected
                  ? `Connected as ${status.email}`
                  : 'Analyze your task management patterns'}
              </p>
            </div>
          </div>
          
          {status.connected ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 text-sm text-green-600">
                <Check className="h-4 w-4" />
                Connected
              </span>
            </div>
          ) : (
            <button
              onClick={handleConnect}
              disabled={loading}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Link2 className="h-4 w-4" />
                  Connect
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {status.connected && (
        <>
          {/* Stats */}
          <div className="p-6 border-b">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Active Tasks</p>
                <p className="text-2xl font-bold text-gray-900">
                  {status.active_tasks || '-'}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Projects</p>
                <p className="text-2xl font-bold text-gray-900">
                  {status.projects || '-'}
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="p-6 border-b">
            <div className="flex gap-3">
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {analyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-4 w-4" />
                    Analyze Tasks
                  </>
                )}
              </button>
              
              <button
                onClick={loadTasksSummary}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
              >
                <Target className="h-4 w-4" />
                Today's Tasks
              </button>
            </div>
          </div>

          {/* Analysis Results */}
          {analysis && (
            <div className="p-6 border-b space-y-4">
              <h4 className="font-semibold mb-4">Task Management Analysis</h4>
              
              {/* Task Patterns */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h5 className="font-medium text-blue-900 mb-2">Task Patterns</h5>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-blue-700">Tasks with Due Dates:</span>{' '}
                    <span className="font-medium">{analysis.task_patterns.tasks_with_due_dates_percentage.toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-blue-700">Daily Completions:</span>{' '}
                    <span className="font-medium">{analysis.task_patterns.average_daily_completions.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-blue-700">Overdue Tasks:</span>{' '}
                    <span className="font-medium text-red-600">{analysis.task_patterns.overdue_tasks}</span>
                  </div>
                  <div>
                    <span className="text-blue-700">This Week:</span>{' '}
                    <span className="font-medium">{analysis.task_patterns.upcoming_week_tasks}</span>
                  </div>
                </div>
                {analysis.task_patterns.peak_productivity_hours.length > 0 && (
                  <div className="mt-2">
                    <p className="text-blue-700 text-xs mb-1">Peak Productivity Hours:</p>
                    <div className="flex gap-2">
                      {analysis.task_patterns.peak_productivity_hours.map((hour, idx) => (
                        <span key={idx} className="text-xs bg-blue-100 px-2 py-0.5 rounded">
                          {hour.hour}:00 ({hour.completions})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Productivity Insights */}
              <div className="bg-green-50 rounded-lg p-4">
                <h5 className="font-medium text-green-900 mb-2">Productivity Insights</h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-green-700">Current Streak:</span>
                    <span className="font-medium">{analysis.productivity_insights.completion_streak} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-700">Most Productive Day:</span>
                    <span className="font-medium">{analysis.productivity_insights.most_productive_day || 'N/A'}</span>
                  </div>
                  {Object.keys(analysis.productivity_insights.weekly_pattern).length > 0 && (
                    <div>
                      <p className="text-green-700 text-xs mb-1">Weekly Pattern:</p>
                      <div className="grid grid-cols-7 gap-1">
                        {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(day => {
                          const avg = analysis.productivity_insights.weekly_pattern[day] || 0;
                          return (
                            <div key={day} className="text-center">
                              <div className="text-xs text-gray-600">{day.slice(0, 3)}</div>
                              <div className="text-xs font-medium">{avg.toFixed(1)}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Project Distribution */}
              <div className="bg-purple-50 rounded-lg p-4">
                <h5 className="font-medium text-purple-900 mb-2">Project Organization</h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-purple-700">Total Projects:</span>
                    <span className="font-medium">{analysis.project_distribution.project_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-700">Inbox Tasks:</span>
                    <span className="font-medium">{analysis.project_distribution.inbox_tasks}</span>
                  </div>
                  {analysis.project_distribution.top_projects.length > 0 && (
                    <div>
                      <p className="text-purple-700 text-xs mb-1">Top Projects:</p>
                      {analysis.project_distribution.top_projects.map((project, idx) => (
                        <div key={idx} className="flex justify-between text-xs">
                          <span className="text-purple-600">{project.name}</span>
                          <span>{project.tasks} tasks</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Priority Usage */}
              <div className="bg-orange-50 rounded-lg p-4">
                <h5 className="font-medium text-orange-900 mb-2">Priority Usage</h5>
                <div className="grid grid-cols-3 gap-2 text-sm text-center">
                  <div>
                    <div className="text-red-600 font-bold text-lg">{analysis.priority_usage.high_priority}</div>
                    <div className="text-xs text-gray-600">High Priority</div>
                  </div>
                  <div>
                    <div className="text-orange-600 font-bold text-lg">{analysis.priority_usage.medium_priority}</div>
                    <div className="text-xs text-gray-600">Medium Priority</div>
                  </div>
                  <div>
                    <div className="text-gray-600 font-bold text-lg">{analysis.priority_usage.low_priority}</div>
                    <div className="text-xs text-gray-600">Low Priority</div>
                  </div>
                </div>
                <p className="text-xs text-center text-gray-600 mt-2">
                  {analysis.priority_usage.uses_priorities ? 'Actively using priority system' : 'Not using priorities'}
                </p>
              </div>

              <p className="text-sm text-gray-600">
                Analyzed {analysis.tasks_analyzed} tasks to understand your productivity patterns
              </p>
            </div>
          )}

          {/* Tasks Summary */}
          {showTasks && tasksSummary && (
            <div className="p-6">
              <h4 className="font-semibold mb-4">Current Tasks</h4>
              
              {/* Today's Tasks */}
              {tasksSummary.today.length > 0 && (
                <div className="mb-6">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">
                    Today ({tasksSummary.counts.today} total)
                  </h5>
                  <div className="space-y-2">
                    {tasksSummary.today.map((task) => (
                      <div key={task.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                        <span className={`text-xs font-medium ${getPriorityColor(task.priority)}`}>
                          {getPriorityLabel(task.priority)}
                        </span>
                        <span className="flex-1 text-sm">{task.content}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Overdue Tasks */}
              {tasksSummary.overdue.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-red-700 mb-2">
                    Overdue ({tasksSummary.counts.overdue} total)
                  </h5>
                  <div className="space-y-2">
                    {tasksSummary.overdue.map((task) => (
                      <div key={task.id} className="flex items-center gap-2 p-2 bg-red-50 rounded">
                        <span className={`text-xs font-medium ${getPriorityColor(task.priority)}`}>
                          {getPriorityLabel(task.priority)}
                        </span>
                        <span className="flex-1 text-sm">{task.content}</span>
                        {task.due && (
                          <span className="text-xs text-red-600">
                            {new Date(task.due.date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default TodoistIntegration;