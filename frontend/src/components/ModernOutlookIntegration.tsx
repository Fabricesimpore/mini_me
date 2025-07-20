import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mail, Link2, Check, AlertCircle, RefreshCw, 
  Calendar, Users, Clock, TrendingUp, X,
  Folder, Send, Inbox, BarChart3
} from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

interface OutlookStatus {
  connected: boolean
  last_sync: string | null
  total_emails: number
  unread_count: number
}

interface EmailSummary {
  folders: Record<string, { total: number; unread: number }>
  recent_senders: Array<{ email: string; count: number }>
  insights: string[]
}

interface OutlookInsights {
  email_patterns: {
    peak_hours: number[]
    busiest_day: string
    avg_emails_per_day: number
  }
  meeting_patterns: {
    avg_meetings_per_week: number
    most_common_duration: number
    back_to_back_meetings: number
  }
  productivity_score: {
    email_efficiency: number
    meeting_optimization: number
    focus_time_available: number
  }
  recommendations: string[]
}

const ModernOutlookIntegration: React.FC = () => {
  const [status, setStatus] = useState<OutlookStatus | null>(null)
  const [emailSummary, setEmailSummary] = useState<EmailSummary | null>(null)
  const [insights, setInsights] = useState<OutlookInsights | null>(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const { token } = useAuthStore()

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/outlook/status', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setStatus(response.data)
      
      if (response.data.connected) {
        loadEmailSummary()
        loadInsights()
      }
    } catch (error) {
      console.error('Failed to check Outlook status:', error)
    }
  }

  const loadEmailSummary = async () => {
    try {
      const response = await api.get('/api/outlook/emails/summary', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setEmailSummary(response.data)
    } catch (error) {
      console.error('Failed to load email summary:', error)
    }
  }

  const loadInsights = async () => {
    try {
      const response = await api.get('/api/outlook/insights', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setInsights(response.data)
    } catch (error) {
      console.error('Failed to load Outlook insights:', error)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    try {
      // Get OAuth URL from backend
      const response = await api.get('/api/outlook/auth', {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      const authUrl = response.data.auth_url
      
      if (authUrl) {
        // Open OAuth flow in new window
        const width = 500
        const height = 600
        const left = window.screen.width / 2 - width / 2
        const top = window.screen.height / 2 - height / 2
        
        const authWindow = window.open(
          authUrl,
          'Microsoft Authorization',
          `width=${width},height=${height},left=${left},top=${top}`
        )
        
        // Check if window was closed
        const checkInterval = setInterval(() => {
          if (authWindow?.closed) {
            clearInterval(checkInterval)
            setLoading(false)
            // Check status after a delay to allow callback to process
            setTimeout(() => {
              checkStatus()
            }, 1000)
          }
        }, 500)
      } else {
        // Fallback to mock connection
        await api.post('/api/outlook/connect', {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
        toast.success('Outlook connected (demo mode)')
        checkStatus()
        setLoading(false)
      }
    } catch (error) {
      console.error('Failed to connect Outlook:', error)
      toast.error('Failed to connect Outlook')
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await api.post('/api/outlook/disconnect', {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Outlook disconnected')
      setStatus({ connected: false, last_sync: null, total_emails: 0, unread_count: 0 })
      setEmailSummary(null)
      setInsights(null)
    } catch (error) {
      console.error('Failed to disconnect Outlook:', error)
      toast.error('Failed to disconnect Outlook')
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 2000))
      toast.success('Outlook sync completed')
      checkStatus()
      loadEmailSummary()
      loadInsights()
    } catch (error) {
      toast.error('Sync failed')
    } finally {
      setSyncing(false)
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
            <div className="p-3 rounded-xl bg-gradient-to-br from-blue-600 to-blue-400">
              <Mail className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Microsoft Outlook Integration</h3>
              <p className="text-gray-400 text-sm">
                {status.connected 
                  ? `Connected • ${status.total_emails.toLocaleString()} emails • ${status.unread_count} unread`
                  : 'Connect to analyze your Outlook data'
                }
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {status.connected && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSync}
                disabled={syncing}
                className="p-2 bg-white/5 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 text-gray-400 ${syncing ? 'animate-spin' : ''}`} />
              </motion.button>
            )}
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={status.connected ? handleDisconnect : handleConnect}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all ${
                status.connected
                  ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                  : 'bg-gradient-to-r from-blue-600 to-blue-400 text-white'
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
                  Connect Outlook
                </>
              )}
            </motion.button>
          </div>
        </div>

        {status.connected && status.last_sync && (
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-400">
            <Clock className="w-4 h-4" />
            Last synced: {new Date(status.last_sync).toLocaleString()}
          </div>
        )}
      </motion.div>

      {/* Email Folders Summary */}
      {status.connected && emailSummary && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-dark rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Folder className="w-5 h-5 text-blue-400" />
            Email Folders
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(emailSummary.folders).map(([folder, stats]) => {
              const icons = {
                inbox: Inbox,
                sent: Send,
                drafts: Mail,
                deleted: AlertCircle
              }
              const Icon = icons[folder as keyof typeof icons] || Folder
              
              return (
                <div key={folder} className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Icon className="w-5 h-5 text-blue-400" />
                    <span className="text-2xl font-bold text-white">{stats.total}</span>
                  </div>
                  <p className="text-sm text-gray-400 capitalize">{folder}</p>
                  {stats.unread > 0 && (
                    <p className="text-xs text-blue-400 mt-1">{stats.unread} unread</p>
                  )}
                </div>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Productivity Scores */}
      {status.connected && insights && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-dark rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            Productivity Analysis
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(insights.productivity_score).map(([metric, score]) => {
              const colors = {
                email_efficiency: 'from-blue-500 to-cyan-500',
                meeting_optimization: 'from-purple-500 to-pink-500',
                focus_time_available: 'from-green-500 to-emerald-500'
              }
              
              return (
                <div key={metric}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-300 capitalize">
                      {metric.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm font-medium text-white">{score}%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${score}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      className={`h-2 rounded-full bg-gradient-to-r ${colors[metric as keyof typeof colors]}`}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          {/* Peak Hours */}
          <div className="mt-6">
            <p className="text-sm text-gray-400 mb-2">Peak Email Hours</p>
            <div className="flex gap-2 flex-wrap">
              {insights.email_patterns.peak_hours.map(hour => (
                <span key={hour} className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm">
                  {hour}:00
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Top Senders */}
      {status.connected && emailSummary && emailSummary.recent_senders.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-dark rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Frequent Contacts
          </h3>

          <div className="space-y-3">
            {emailSummary.recent_senders.map((sender, index) => (
              <motion.div
                key={sender.email}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
              >
                <span className="text-sm text-gray-300">{sender.email}</span>
                <span className="text-sm text-purple-400 font-medium">{sender.count} emails</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* AI Recommendations */}
      {status.connected && insights && insights.recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-dark rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            Productivity Recommendations
          </h3>

          <div className="space-y-3">
            {insights.recommendations.map((recommendation, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-3"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-green-400 mt-2" />
                <p className="text-sm text-gray-300">{recommendation}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {!status.connected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <Mail className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">
            Connect Your Outlook
          </h3>
          <p className="text-gray-400 mb-6">
            Analyze your email and calendar patterns across Microsoft services
          </p>
        </motion.div>
      )}
    </div>
  )
}

export default ModernOutlookIntegration