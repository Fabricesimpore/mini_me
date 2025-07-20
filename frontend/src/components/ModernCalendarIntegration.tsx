import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Calendar, Link2, Check, RefreshCw, Clock, 
  Users, Video, MapPin, TrendingUp, X
} from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

interface CalendarStatus {
  connected: boolean
  calendar_name: string | null
  total_events: number
  upcoming_events: number
}

interface CalendarInsights {
  summary: {
    meetings_this_week: number
    avg_meeting_duration: number
    meeting_hours_this_week: number
  }
  meeting_types: {
    one_on_one: number
    team_meeting: number
    external: number
    focus_time: number
  }
  busiest_days: Array<{
    day: string
    hours: number
  }>
  insights: string[]
}

const ModernCalendarIntegration: React.FC = () => {
  const [status, setStatus] = useState<CalendarStatus | null>(null)
  const [insights, setInsights] = useState<CalendarInsights | null>(null)
  const [loading, setLoading] = useState(false)
  const { token } = useAuthStore()

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/calendar/status', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setStatus(response.data)
      
      if (response.data.connected) {
        loadInsights()
      }
    } catch (error) {
      console.error('Failed to check Calendar status:', error)
    }
  }

  const loadInsights = async () => {
    try {
      const response = await api.get('/api/calendar/insights', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setInsights(response.data)
    } catch (error) {
      console.error('Failed to load calendar insights:', error)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    try {
      await api.post('/api/calendar/connect', {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Calendar connected successfully!')
      checkStatus()
    } catch (error) {
      toast.error('Failed to connect Calendar')
    } finally {
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await api.post('/api/calendar/disconnect', {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Calendar disconnected')
      setStatus({ connected: false, calendar_name: null, total_events: 0, upcoming_events: 0 })
      setInsights(null)
    } catch (error) {
      toast.error('Failed to disconnect Calendar')
    }
  }

  if (!status) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Connection Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-dark rounded-xl p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500">
              <Calendar className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Google Calendar</h3>
              <p className="text-gray-400 text-sm">
                {status.connected 
                  ? `${status.calendar_name} • ${status.upcoming_events} upcoming events`
                  : 'Connect to analyze your schedule patterns'
                }
              </p>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={status.connected ? handleDisconnect : handleConnect}
            disabled={loading}
            className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all ${
              status.connected
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white'
            }`}
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : status.connected ? (
              <>
                <X className="w-4 h-4" />
                Disconnect
              </>
            ) : (
              <>
                <Link2 className="w-4 h-4" />
                Connect Calendar
              </>
            )}
          </motion.button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      {status.connected && insights && (
        <>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-4"
          >
            <div className="glass-dark rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <Calendar className="w-5 h-5 text-blue-400" />
                <span className="text-2xl font-bold text-white">
                  {insights.summary.meetings_this_week}
                </span>
              </div>
              <p className="text-sm text-gray-400">Meetings This Week</p>
            </div>

            <div className="glass-dark rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <Clock className="w-5 h-5 text-purple-400" />
                <span className="text-2xl font-bold text-white">
                  {insights.summary.avg_meeting_duration}m
                </span>
              </div>
              <p className="text-sm text-gray-400">Avg Meeting Duration</p>
            </div>

            <div className="glass-dark rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-5 h-5 text-green-400" />
                <span className="text-2xl font-bold text-white">
                  {insights.summary.meeting_hours_this_week}h
                </span>
              </div>
              <p className="text-sm text-gray-400">Meeting Hours</p>
            </div>
          </motion.div>

          {/* Meeting Types */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-dark rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Meeting Breakdown</h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(insights.meeting_types).map(([type, count]) => {
                const icons = {
                  one_on_one: Users,
                  team_meeting: Users,
                  external: Video,
                  focus_time: Clock
                }
                const Icon = icons[type as keyof typeof icons]
                
                return (
                  <div key={type} className="bg-white/5 rounded-lg p-4">
                    <Icon className="w-5 h-5 text-purple-400 mb-2" />
                    <p className="text-2xl font-bold text-white">{count}</p>
                    <p className="text-sm text-gray-400 capitalize">
                      {type.replace('_', ' ')}
                    </p>
                  </div>
                )
              })}
            </div>
          </motion.div>

          {/* Busiest Days */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-dark rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Schedule Heatmap</h3>
            
            <div className="space-y-3">
              {insights.busiest_days.map((day, index) => {
                const maxHours = Math.max(...insights.busiest_days.map(d => d.hours))
                const percentage = (day.hours / maxHours) * 100
                
                return (
                  <div key={day.day}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-300">{day.day}</span>
                      <span className="text-sm text-gray-400">{day.hours}h</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 1, ease: "easeOut", delay: index * 0.1 }}
                        className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>

          {/* AI Insights */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-dark rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Schedule Insights</h3>
            
            <div className="space-y-3">
              {insights.insights.map((insight, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2" />
                  <p className="text-sm text-gray-300">{insight}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </>
      )}

      {/* Empty State */}
      {!status.connected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">
            Connect Your Calendar
          </h3>
          <p className="text-gray-400 mb-6">
            Optimize your schedule and meeting patterns
          </p>
        </motion.div>
      )}
    </div>
  )
}

export default ModernCalendarIntegration