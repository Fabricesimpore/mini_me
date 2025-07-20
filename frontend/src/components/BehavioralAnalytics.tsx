import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, TrendingUp, Activity, Zap, Calendar, Target,
  BarChart3, Clock, Sparkles, ChevronRight, Flame
} from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

interface BehavioralPattern {
  pattern_type: string
  description: string
  frequency: number
  confidence: number
  last_observed: Date
}

interface ActivitySummary {
  activity_type: string
  duration_minutes: number
  count: number
  productivity_score: number
}

interface Habit {
  name: string
  streak: number
  completion_rate: number
  impact_score: number
}

const BehavioralAnalytics: React.FC = () => {
  const [patterns, setPatterns] = useState<BehavioralPattern[]>([])
  const [activities, setActivities] = useState<ActivitySummary[]>([])
  const [productivityData, setProductivityData] = useState<any>(null)
  const [habits, setHabits] = useState<any>(null)
  const [selectedTimeframe, setSelectedTimeframe] = useState(7)
  const { token } = useAuthStore()

  useEffect(() => {
    loadBehavioralData()
  }, [selectedTimeframe])

  const loadBehavioralData = async () => {
    try {
      const [patternsRes, activitiesRes, productivityRes, habitsRes] = await Promise.all([
        api.get('/api/behavioral/patterns', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get(`/api/behavioral/activity-summary?days=${selectedTimeframe}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/behavioral/productivity-score', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/behavioral/habits', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ])

      setPatterns(patternsRes.data)
      setActivities(activitiesRes.data)
      setProductivityData(productivityRes.data)
      setHabits(habitsRes.data)
    } catch (error) {
      console.error('Failed to load behavioral data:', error)
      toast.error('Failed to load behavioral analytics')
    }
  }

  const getPatternIcon = (type: string) => {
    switch (type) {
      case 'work_schedule': return Clock
      case 'break_pattern': return Activity
      case 'communication': return Brain
      default: return Sparkles
    }
  }

  const getActivityColor = (score: number) => {
    if (score >= 0.8) return 'from-green-500 to-emerald-500'
    if (score >= 0.6) return 'from-blue-500 to-cyan-500'
    if (score >= 0.4) return 'from-yellow-500 to-orange-500'
    return 'from-red-500 to-pink-500'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h2 className="text-2xl font-bold gradient-text">Behavioral Analytics</h2>
          <p className="text-gray-400 mt-1">Understanding your patterns and productivity</p>
        </div>
        
        {/* Timeframe Selector */}
        <div className="flex gap-2">
          {[7, 14, 30].map((days) => (
            <motion.button
              key={days}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSelectedTimeframe(days)}
              className={`px-4 py-2 rounded-lg transition-all ${
                selectedTimeframe === days
                  ? 'bg-purple-500/20 border border-purple-500/50 text-purple-400'
                  : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white'
              }`}
            >
              {days}d
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Productivity Score Card */}
      {productivityData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-dark rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              Productivity Score
            </h3>
            <motion.div
              className="text-3xl font-bold gradient-text"
              animate={{ 
                scale: [1, 1.1, 1],
                opacity: [1, 0.8, 1]
              }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {Math.round(productivityData.current_score * 100)}%
            </motion.div>
          </div>

          {/* Productivity Factors */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {Object.entries(productivityData.factors).map(([factor, score]) => (
              <motion.div
                key={factor}
                whileHover={{ scale: 1.05 }}
                className="bg-white/5 rounded-lg p-3"
              >
                <div className="text-sm text-gray-400 mb-1">
                  {factor.replace('_', ' ').charAt(0).toUpperCase() + factor.slice(1).replace('_', ' ')}
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-white/10 rounded-full h-2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(score as number) * 100}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      className={`h-2 rounded-full bg-gradient-to-r ${getActivityColor(score as number)}`}
                    />
                  </div>
                  <span className="text-xs text-gray-300">{Math.round((score as number) * 100)}%</span>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Recommendations */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-300 mb-2">AI Recommendations</h4>
            {productivityData.recommendations.map((rec: string, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-2 text-sm text-gray-400"
              >
                <ChevronRight className="w-4 h-4 text-purple-400 mt-0.5" />
                <span>{rec}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Activity Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-dark rounded-xl p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          Activity Breakdown
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {activities.map((activity, index) => (
            <motion.div
              key={activity.activity_type}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.02 }}
              className="bg-white/5 rounded-lg p-4 border border-white/10"
            >
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-white">{activity.activity_type}</h4>
                <div className={`px-2 py-1 rounded-full text-xs bg-gradient-to-r ${getActivityColor(activity.productivity_score)} text-white`}>
                  {Math.round(activity.productivity_score * 100)}% productive
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Total Time</p>
                  <p className="text-white font-medium">{Math.round(activity.duration_minutes / 60)}h {activity.duration_minutes % 60}m</p>
                </div>
                <div>
                  <p className="text-gray-400">Sessions</p>
                  <p className="text-white font-medium">{activity.count}</p>
                </div>
              </div>
              
              <div className="mt-3">
                <div className="w-full bg-white/10 rounded-full h-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(activity.duration_minutes / 480) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className={`h-2 rounded-full bg-gradient-to-r ${getActivityColor(activity.productivity_score)}`}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Behavioral Patterns */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-dark rounded-xl p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          Identified Patterns
        </h3>

        <div className="space-y-3">
          {patterns.map((pattern, index) => {
            const Icon = getPatternIcon(pattern.pattern_type)
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-4 p-4 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="p-2 rounded-lg bg-purple-500/20">
                  <Icon className="w-5 h-5 text-purple-400" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium">{pattern.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                    <span>Frequency: {Math.round(pattern.frequency * 100)}%</span>
                    <span>Confidence: {Math.round(pattern.confidence * 100)}%</span>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </motion.div>

      {/* Habits Tracker */}
      {habits && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-dark rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-green-400" />
            Habit Tracker
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {habits.habits.map((habit: Habit, index: number) => (
              <motion.div
                key={habit.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.05 }}
                className="bg-white/5 rounded-lg p-4 border border-white/10"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-white">{habit.name}</h4>
                  <div className="flex items-center gap-1 text-orange-400">
                    <Flame className="w-4 h-4" />
                    <span className="text-sm font-bold">{habit.streak}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-400">Completion</span>
                      <span className="text-white">{Math.round(habit.completion_rate * 100)}%</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${habit.completion_rate * 100}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="h-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-500"
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-400">Impact</span>
                      <span className="text-white">{Math.round(habit.impact_score * 100)}%</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${habit.impact_score * 100}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500"
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {habits.insights && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg"
            >
              <p className="text-green-400 text-sm flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                {habits.insights}
              </p>
            </motion.div>
          )}
        </motion.div>
      )}
    </div>
  )
}

export default BehavioralAnalytics