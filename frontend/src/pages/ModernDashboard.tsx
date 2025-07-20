import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Brain, Activity, TrendingUp, Calendar, Mail, CheckCircle, 
  AlertCircle, Zap, Target, Heart, Coffee, Moon
} from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import ModernChat from '../components/ModernChat'
import toast from 'react-hot-toast'

const ModernDashboard: React.FC = () => {
  const { user, token } = useAuthStore()
  const [stats, setStats] = useState({
    productivity: 0,
    insights: 0,
    memories: 0,
    integrations: 0
  })
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [mlInsights, setMlInsights] = useState<any[]>([])

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      // Load multiple data points in parallel
      const [behavioralRes, mlRes, recommendationsRes, integrationsRes] = await Promise.all([
        api.get('/api/behavioral/productivity-score', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/ml/insights', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/recommendations/daily', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/integrations/status', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ])

      setStats({
        productivity: Math.round(behavioralRes.data.current_score * 100),
        insights: mlRes.data.length,
        memories: 42, // Mock value
        integrations: integrationsRes.data.filter((i: any) => i.status === 'connected').length
      })

      setMlInsights(mlRes.data.slice(0, 3))
      setRecommendations(recommendationsRes.data.slice(0, 3))
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  }

  const statCards = [
    {
      title: 'Productivity Score',
      value: `${stats.productivity}%`,
      icon: TrendingUp,
      color: 'from-blue-500 to-cyan-500',
      change: '+5%'
    },
    {
      title: 'AI Insights',
      value: stats.insights,
      icon: Brain,
      color: 'from-purple-500 to-pink-500',
      change: 'New'
    },
    {
      title: 'Memories Stored',
      value: stats.memories,
      icon: Activity,
      color: 'from-green-500 to-emerald-500',
      change: '+3'
    },
    {
      title: 'Active Integrations',
      value: `${stats.integrations}/4`,
      icon: Zap,
      color: 'from-orange-500 to-red-500',
      change: 'Connect'
    }
  ]

  const moodIcons = {
    work: Coffee,
    health: Heart,
    rest: Moon
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Welcome Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold mb-2">
            Welcome back, <span className="gradient-text">{user?.username || 'User'}</span>
          </h1>
          <p className="text-gray-400 text-lg">Your digital twin is ready to assist you today</p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative group"
            >
              <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl blur-xl"
                style={{ background: `linear-gradient(135deg, ${stat.color.split(' ')[1]} 0%, ${stat.color.split(' ')[3]} 100%)` }}
              />
              <div className="relative card glass-dark">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-lg bg-gradient-to-r ${stat.color}`}>
                    <stat.icon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-sm text-green-400">{stat.change}</span>
                </div>
                <h3 className="text-gray-400 text-sm mb-1">{stat.title}</h3>
                <p className="text-3xl font-bold text-white">{stat.value}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Insights & Recommendations */}
          <div className="lg:col-span-2 space-y-6">
            {/* AI Insights */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="card glass-dark"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-400" />
                  AI Insights
                </h2>
                <button className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                  View all →
                </button>
              </div>
              <div className="space-y-4">
                {mlInsights.map((insight, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-white mb-1">{insight.title}</h3>
                        <p className="text-sm text-gray-400">{insight.description}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        insight.importance === 'high' 
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {insight.importance}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Daily Recommendations */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="card glass-dark"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Target className="w-5 h-5 text-green-400" />
                  Today's Recommendations
                </h2>
                <button className="text-sm text-green-400 hover:text-green-300 transition-colors">
                  Customize →
                </button>
              </div>
              <div className="space-y-4">
                {recommendations.map((rec, index) => {
                  const Icon = moodIcons[rec.category as keyof typeof moodIcons] || Coffee
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-start gap-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/15 transition-colors cursor-pointer"
                    >
                      <div className="p-2 bg-green-500/20 rounded-lg">
                        <Icon className="w-5 h-5 text-green-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-white mb-1">{rec.title}</h3>
                        <p className="text-sm text-gray-400 mb-2">{rec.description}</p>
                        <div className="flex flex-wrap gap-2">
                          {rec.action_items.slice(0, 2).map((action: string, i: number) => (
                            <span key={i} className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full">
                              {action}
                            </span>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          </div>

          {/* Right Column - Chat */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="h-[600px]"
          >
            <ModernChat />
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8"
        >
          {[
            { icon: Calendar, label: 'Schedule', color: 'from-blue-500 to-blue-600' },
            { icon: Mail, label: 'Email Insights', color: 'from-purple-500 to-purple-600' },
            { icon: CheckCircle, label: 'Tasks', color: 'from-green-500 to-green-600' },
            { icon: AlertCircle, label: 'Focus Mode', color: 'from-orange-500 to-orange-600' }
          ].map((action, index) => (
            <motion.button
              key={action.label}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`p-4 rounded-xl bg-gradient-to-r ${action.color} text-white font-medium flex items-center justify-center gap-2 transition-all`}
            >
              <action.icon className="w-5 h-5" />
              {action.label}
            </motion.button>
          ))}
        </motion.div>
      </div>
    </div>
  )
}

export default ModernDashboard