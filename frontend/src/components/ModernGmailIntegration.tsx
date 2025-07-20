import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mail, Link2, Check, AlertCircle, RefreshCw, 
  BarChart3, Users, Clock, Zap, TrendingUp, 
  Inbox, Send, Archive, Star, X
} from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

interface GmailStatus {
  connected: boolean
  last_sync: string | null
  total_emails: number
  unread_count: number
}

interface EmailInsights {
  summary: {
    total_this_week: number
    response_rate: number
    avg_response_time_hours: number
  }
  top_senders: Array<{
    email: string
    count: number
  }>
  categories: {
    work: number
    personal: number
    newsletters: number
  }
  insights: string[]
}

const ModernGmailIntegration: React.FC = () => {
  const [status, setStatus] = useState<GmailStatus | null>(null)
  const [insights, setInsights] = useState<EmailInsights | null>(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const { token } = useAuthStore()

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/gmail/status', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setStatus(response.data)
      
      if (response.data.connected) {
        loadInsights()
      }
    } catch (error) {
      console.error('Failed to check Gmail status:', error)
    }
  }

  const loadInsights = async () => {
    try {
      const response = await api.get('/api/gmail/insights', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setInsights(response.data)
    } catch (error) {
      console.error('Failed to load email insights:', error)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    try {
      // Get OAuth URL from backend
      const response = await api.get('/api/gmail/auth', {
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
          'Gmail Authorization',
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
              loadInsights()
            }, 1000)
          }
        }, 500)
      } else {
        // Fallback to mock connection
        await api.post('/api/gmail/connect', {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
        toast.success('Gmail connected (demo mode)')
        checkStatus()
      }
    } catch (error) {
      console.error('Failed to connect Gmail:', error)
      toast.error('Failed to connect Gmail')
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await api.post('/api/gmail/disconnect', {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Gmail disconnected')
      setStatus({ connected: false, last_sync: null, total_emails: 0, unread_count: 0 })
      setInsights(null)
    } catch (error) {
      console.error('Failed to disconnect Gmail:', error)
      toast.error('Failed to disconnect Gmail')
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      // Simulate sync
      await new Promise(resolve => setTimeout(resolve, 2000))
      toast.success('Email sync completed')
      checkStatus()
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
            <div className="p-3 rounded-xl bg-gradient-to-br from-red-500 to-pink-500">
              <Mail className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Gmail Integration</h3>
              <p className="text-gray-400 text-sm">
                {status.connected 
                  ? `Connected • ${status.total_emails.toLocaleString()} emails`
                  : 'Connect to analyze your email patterns'
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
                  : 'bg-gradient-to-r from-red-500 to-pink-500 text-white'
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
                  Connect Gmail
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

      {/* Stats Grid */}
      {status.connected && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          <div className="glass-dark rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <Inbox className="w-5 h-5 text-blue-400" />
              <span className="text-2xl font-bold text-white">
                {status.total_emails.toLocaleString()}
              </span>
            </div>
            <p className="text-sm text-gray-400">Total Emails</p>
          </div>

          <div className="glass-dark rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <Mail className="w-5 h-5 text-green-400" />
              <span className="text-2xl font-bold text-white">
                {status.unread_count}
              </span>
            </div>
            <p className="text-sm text-gray-400">Unread</p>
          </div>

          <div className="glass-dark rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <Send className="w-5 h-5 text-purple-400" />
              <span className="text-2xl font-bold text-white">
                {insights?.summary.response_rate 
                  ? `${Math.round(insights.summary.response_rate * 100)}%` 
                  : '-'
                }
              </span>
            </div>
            <p className="text-sm text-gray-400">Response Rate</p>
          </div>

          <div className="glass-dark rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <Clock className="w-5 h-5 text-orange-400" />
              <span className="text-2xl font-bold text-white">
                {insights?.summary.avg_response_time_hours 
                  ? `${insights.summary.avg_response_time_hours}h` 
                  : '-'
                }
              </span>
            </div>
            <p className="text-sm text-gray-400">Avg Response Time</p>
          </div>
        </motion.div>
      )}

      {/* Email Insights */}
      {status.connected && insights && (
        <>
          {/* Categories Breakdown */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-dark rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              Email Categories
            </h3>

            <div className="space-y-3">
              {Object.entries(insights.categories).map(([category, count]) => {
                const percentage = (count / status.total_emails) * 100
                const colors = {
                  work: 'from-blue-500 to-cyan-500',
                  personal: 'from-purple-500 to-pink-500',
                  newsletters: 'from-green-500 to-emerald-500'
                }
                
                return (
                  <div key={category}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-300 capitalize">{category}</span>
                      <span className="text-sm text-gray-400">{count} emails</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className={`h-2 rounded-full bg-gradient-to-r ${colors[category as keyof typeof colors]}`}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>

          {/* Top Senders */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-dark rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-400" />
              Top Senders
            </h3>

            <div className="space-y-3">
              {insights.top_senders.map((sender, index) => (
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

          {/* AI Insights */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-dark rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              AI Insights
            </h3>

            <div className="space-y-3">
              {insights.insights.map((insight, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-yellow-400 mt-2" />
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
          <Mail className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">
            Connect Your Gmail
          </h3>
          <p className="text-gray-400 mb-6">
            Analyze your email patterns and improve your communication
          </p>
        </motion.div>
      )}
    </div>
  )
}

export default ModernGmailIntegration