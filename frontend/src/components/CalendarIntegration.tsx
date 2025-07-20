import React, { useState, useEffect } from 'react';
import { Calendar, Check, AlertCircle, RefreshCw, Link2, Clock, Users, BarChart3 } from 'lucide-react';
import { api } from '../services/api';

interface CalendarStatus {
  connected: boolean;
  email?: string;
  calendars_count?: number;
  connected_at?: string;
}

interface CalendarAnalysis {
  events_analyzed: number;
  time_patterns: {
    peak_hours: Array<{ hour: number; count: number }>;
    busiest_days: Array<{ day: string; count: number }>;
    average_duration_minutes: number;
    typical_start_time: string;
  };
  meeting_patterns: {
    meeting_types: {
      one_on_one: number;
      small_group: number;
      large_meeting: number;
      recurring: number;
      external: number;
    };
    top_collaborators: Array<{ email: string; meetings: number }>;
  };
  work_life_balance: {
    work_hours_percentage: number;
    personal_hours_percentage: number;
    work_life_balance_score: number;
    weekend_events: number;
    evening_events: number;
  };
  scheduling_habits: {
    average_buffer_minutes: number;
    average_advance_scheduling_days: number;
    prefers_buffer_time: boolean;
  };
}

interface UpcomingEvent {
  id: string;
  summary: string;
  start: { dateTime?: string; date?: string };
  end: { dateTime?: string; date?: string };
  location?: string;
  attendees_count: number;
  is_recurring: boolean;
}

const CalendarIntegration: React.FC = () => {
  const [status, setStatus] = useState<CalendarStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<CalendarAnalysis | null>(null);
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
  const [showUpcoming, setShowUpcoming] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/calendar/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Error checking calendar status:', error);
      setStatus({ connected: false });
    }
  };

  const handleConnect = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/calendar/auth');
      // Open auth URL in new window
      window.open(response.data.auth_url, '_blank', 'width=600,height=600');
      
      // Poll for connection status
      const pollInterval = setInterval(async () => {
        const statusResponse = await api.get('/api/calendar/status');
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
      console.error('Error connecting calendar:', error);
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const response = await api.post('/api/calendar/analyze', { max_events: 500 });
      if (response.data.status === 'success') {
        setAnalysis(response.data.insights);
      }
    } catch (error) {
      console.error('Error analyzing calendar:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const loadUpcomingEvents = async () => {
    try {
      const response = await api.get('/api/calendar/upcoming?days=7');
      setUpcomingEvents(response.data.events);
      setShowUpcoming(true);
    } catch (error) {
      console.error('Error loading upcoming events:', error);
    }
  };

  const formatEventTime = (event: UpcomingEvent) => {
    if (event.start.dateTime) {
      const date = new Date(event.start.dateTime);
      return date.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      });
    } else if (event.start.date) {
      return new Date(event.start.date).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      }) + ' (All day)';
    }
    return 'Unknown time';
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
            <div className="p-2 bg-blue-100 rounded-lg">
              <Calendar className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Google Calendar</h3>
              <p className="text-sm text-gray-600">
                {status.connected
                  ? `Connected as ${status.email}`
                  : 'Analyze your scheduling patterns and habits'}
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
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Connected Calendars</p>
              <p className="text-2xl font-bold text-gray-900">
                {status.calendars_count || '-'}
              </p>
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
                    <BarChart3 className="h-4 w-4" />
                    Analyze Calendar
                  </>
                )}
              </button>
              
              <button
                onClick={loadUpcomingEvents}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
              >
                <Clock className="h-4 w-4" />
                Upcoming Events
              </button>
            </div>
          </div>

          {/* Analysis Results */}
          {analysis && (
            <div className="p-6 border-b space-y-4">
              <h4 className="font-semibold mb-4">Calendar Analysis</h4>
              
              {/* Time Patterns */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h5 className="font-medium text-blue-900 mb-2">Time Patterns</h5>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="text-blue-700">Typical Start Time:</span>{' '}
                    <span className="font-medium">{analysis.time_patterns.typical_start_time}</span>
                  </p>
                  <p>
                    <span className="text-blue-700">Average Meeting Duration:</span>{' '}
                    <span className="font-medium">
                      {Math.round(analysis.time_patterns.average_duration_minutes)} minutes
                    </span>
                  </p>
                  <div>
                    <span className="text-blue-700">Peak Hours:</span>
                    <div className="mt-1 space-y-1">
                      {analysis.time_patterns.peak_hours.map((hour, idx) => (
                        <div key={idx} className="text-xs">
                          {hour.hour}:00 - {hour.count} events
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Meeting Patterns */}
              <div className="bg-purple-50 rounded-lg p-4">
                <h5 className="font-medium text-purple-900 mb-2">Meeting Patterns</h5>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-purple-700">1:1s:</span>{' '}
                    <span className="font-medium">{analysis.meeting_patterns.meeting_types.one_on_one}</span>
                  </div>
                  <div>
                    <span className="text-purple-700">Group:</span>{' '}
                    <span className="font-medium">
                      {analysis.meeting_patterns.meeting_types.small_group + 
                       analysis.meeting_patterns.meeting_types.large_meeting}
                    </span>
                  </div>
                  <div>
                    <span className="text-purple-700">Recurring:</span>{' '}
                    <span className="font-medium">{analysis.meeting_patterns.meeting_types.recurring}</span>
                  </div>
                  <div>
                    <span className="text-purple-700">External:</span>{' '}
                    <span className="font-medium">{analysis.meeting_patterns.meeting_types.external}</span>
                  </div>
                </div>
                {analysis.meeting_patterns.top_collaborators.length > 0 && (
                  <div className="mt-3">
                    <p className="text-purple-700 text-xs mb-1">Top Collaborators:</p>
                    {analysis.meeting_patterns.top_collaborators.slice(0, 3).map((collab, idx) => (
                      <div key={idx} className="text-xs">
                        {collab.email} ({collab.meetings} meetings)
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Work-Life Balance */}
              <div className="bg-green-50 rounded-lg p-4">
                <h5 className="font-medium text-green-900 mb-2">Work-Life Balance</h5>
                <div className="mb-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-green-700">Balance Score</span>
                    <span className="font-medium">{analysis.work_life_balance.work_life_balance_score.toFixed(0)}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${analysis.work_life_balance.work_life_balance_score}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-green-700">Work Hours:</span>{' '}
                    <span className="font-medium">{analysis.work_life_balance.work_hours_percentage.toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-green-700">Personal:</span>{' '}
                    <span className="font-medium">{analysis.work_life_balance.personal_hours_percentage.toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-green-700">Weekend Events:</span>{' '}
                    <span className="font-medium">{analysis.work_life_balance.weekend_events}</span>
                  </div>
                  <div>
                    <span className="text-green-700">Evening Events:</span>{' '}
                    <span className="font-medium">{analysis.work_life_balance.evening_events}</span>
                  </div>
                </div>
              </div>

              {/* Scheduling Habits */}
              <div className="bg-orange-50 rounded-lg p-4">
                <h5 className="font-medium text-orange-900 mb-2">Scheduling Habits</h5>
                <div className="space-y-1 text-sm">
                  <p>
                    <span className="text-orange-700">Average Buffer Time:</span>{' '}
                    <span className="font-medium">{Math.round(analysis.scheduling_habits.average_buffer_minutes)} minutes</span>
                  </p>
                  <p>
                    <span className="text-orange-700">Plans Ahead:</span>{' '}
                    <span className="font-medium">{Math.round(analysis.scheduling_habits.average_advance_scheduling_days)} days</span>
                  </p>
                  <p>
                    <span className="text-orange-700">Prefers Buffer Time:</span>{' '}
                    <span className="font-medium">{analysis.scheduling_habits.prefers_buffer_time ? 'Yes' : 'No'}</span>
                  </p>
                </div>
              </div>

              <p className="text-sm text-gray-600">
                Analyzed {analysis.events_analyzed} events to understand your scheduling patterns
              </p>
            </div>
          )}

          {/* Upcoming Events */}
          {showUpcoming && upcomingEvents.length > 0 && (
            <div className="p-6">
              <h4 className="font-semibold mb-4">Upcoming Events (Next 7 Days)</h4>
              <div className="space-y-2">
                {upcomingEvents.map((event) => (
                  <div key={event.id} className="border rounded-lg p-3 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h5 className="font-medium text-sm">{event.summary}</h5>
                        <p className="text-xs text-gray-600 mt-1">
                          {formatEventTime(event)}
                        </p>
                        {event.location && (
                          <p className="text-xs text-gray-500 mt-1">
                            📍 {event.location}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        {event.attendees_count > 0 && (
                          <span className="flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            {event.attendees_count}
                          </span>
                        )}
                        {event.is_recurring && (
                          <span className="bg-gray-100 px-1.5 py-0.5 rounded">
                            Recurring
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default CalendarIntegration;