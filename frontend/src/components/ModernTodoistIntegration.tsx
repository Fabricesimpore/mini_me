import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  CheckSquare, Link2, Plus, Calendar, Tag, 
  TrendingUp, Target, Clock, Flame, X
} from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

interface TodoistStatus {
  connected: boolean
  user_name: string | null
  total_tasks: number
  completed_today: number
  karma: number
}

interface TodoistInsights {
  productivity: {
    completion_rate: number
    streak: number
    avg_tasks_per_day: number
  }
  project_stats: Array<{
    name: string
    task_count: number
    completion_rate: number
  }>
  priority_distribution: {
    priority_1: number
    priority_2: number
    priority_3: number
    priority_4: number
  }
  insights: string[]
}

interface Task {
  id: string
  content: string
  priority: number
  project: string
  due_date: string | null
  completed: boolean
}

const ModernTodoistIntegration: React.FC = () => {
  const [status, setStatus] = useState<TodoistStatus | null>(null)
  const [insights, setInsights] = useState<TodoistInsights | null>(null)
  const [recentTasks, setRecentTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const { token } = useAuthStore()

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/todoist/status', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setStatus(response.data)
      
      if (response.data.connected) {
        loadInsights()
        loadRecentTasks()
      }
    } catch (error) {
      console.error('Failed to check Todoist status:', error)
    }
  }

  const loadInsights = async () => {
    try {
      const response = await api.get('/api/todoist/insights', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setInsights(response.data)
    } catch (error) {
      console.error('Failed to load Todoist insights:', error)
    }
  }

  const loadRecentTasks = async () => {
    try {
      const response = await api.get('/api/todoist/tasks/recent', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setRecentTasks(response.data.tasks)
    } catch (error) {
      console.error('Failed to load recent tasks:', error)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    try {
      await api.post('/api/todoist/connect', {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Todoist connected successfully!')
      checkStatus()
    } catch (error) {
      toast.error('Failed to connect Todoist')
    } finally {
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await api.post('/api/todoist/disconnect', {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Todoist disconnected')
      setStatus({ connected: false, user_name: null, total_tasks: 0, completed_today: 0, karma: 0 })
      setInsights(null)
      setRecentTasks([])
    } catch (error) {
      toast.error('Failed to disconnect Todoist')
    }
  }

  const getPriorityColor = (priority: number) => {
    const colors = {
      1: 'text-gray-400',
      2: 'text-blue-400',
      3: 'text-yellow-400',
      4: 'text-red-400'
    }
    return colors[priority as keyof typeof colors] || 'text-gray-400'
  }

  const getPriorityBg = (priority: number) => {
    const colors = {
      1: 'from-gray-500 to-gray-600',
      2: 'from-blue-500 to-blue-600',
      3: 'from-yellow-500 to-yellow-600',
      4: 'from-red-500 to-red-600'
    }
    return colors[priority as keyof typeof colors] || 'from-gray-500 to-gray-600'
  }

  if (!status) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-purple-400 border-t-transparent rounded-full" />
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
            <div className="p-3 rounded-xl bg-gradient-to-br from-red-500 to-orange-500">
              <CheckSquare className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Todoist Integration</h3>
              <p className="text-gray-400 text-sm">
                {status.connected 
                  ? `${status.user_name} • ${status.total_tasks} total tasks`
                  : 'Connect to analyze your task patterns'
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
                : 'bg-gradient-to-r from-red-500 to-orange-500 text-white'
            }`}
          >
            {loading ? (
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : status.connected ? (
              <>
                <X className="w-4 h-4" />
                Disconnect
              </>
            ) : (
              <>
                <Link2 className="w-4 h-4" />
                Connect Todoist
              </>
            )}
          </motion.button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      {status.connected && (
        <>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            <div className="glass-dark rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <CheckSquare className="w-5 h-5 text-green-400" />
                <span className="text-2xl font-bold text-white">
                  {status.completed_today}
                </span>
              </div>
              <p className="text-sm text-gray-400">Completed Today</p>
            </div>

            <div className="glass-dark rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <Target className="w-5 h-5 text-blue-400" />
                <span className="text-2xl font-bold text-white">
                  {status.total_tasks}
                </span>
              </div>
              <p className="text-sm text-gray-400">Total Tasks</p>
            </div>

            <div className="glass-dark rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <Flame className="w-5 h-5 text-orange-400" />
                <span className="text-2xl font-bold text-white">
                  {insights?.productivity.streak || 0}
                </span>
              </div>
              <p className="text-sm text-gray-400">Day Streak</p>
            </div>

            <div className="glass-dark rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-5 h-5 text-purple-400" />
                <span className="text-2xl font-bold text-white">
                  {status.karma}
                </span>
              </div>
              <p className="text-sm text-gray-400">Karma Points</p>
            </div>
          </motion.div>

          {/* Productivity Overview */}
          {insights && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-dark rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Productivity Overview</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-400 mb-1">
                    {Math.round(insights.productivity.completion_rate * 100)}%
                  </div>
                  <p className="text-sm text-gray-400">Completion Rate</p>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-400 mb-1">
                    {insights.productivity.avg_tasks_per_day}
                  </div>
                  <p className="text-sm text-gray-400">Tasks per Day</p>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-400 mb-1">
                    {insights.productivity.streak}
                  </div>
                  <p className="text-sm text-gray-400">Current Streak</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Priority Distribution */}
          {insights && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-dark rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Priority Distribution</h3>
              
              <div className="space-y-3">
                {Object.entries(insights.priority_distribution).map(([priority, count]) => {
                  const priorityNum = parseInt(priority.split('_')[1])
                  const total = Object.values(insights.priority_distribution).reduce((a, b) => a + b, 0)
                  const percentage = total > 0 ? (count / total) * 100 : 0
                  
                  return (
                    <div key={priority}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-300">
                          Priority {priorityNum}
                        </span>
                        <span className="text-sm text-gray-400">{count} tasks</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 1, ease: "easeOut" }}
                          className={`h-2 rounded-full bg-gradient-to-r ${getPriorityBg(priorityNum)}`}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </motion.div>
          )}

          {/* Recent Tasks */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-dark rounded-xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Recent Tasks</h3>
            
            <div className="space-y-3">
              {recentTasks.slice(0, 5).map((task, index) => (
                <motion.div
                  key={task.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                    task.completed 
                      ? 'bg-green-500/10 border border-green-500/30' 
                      : 'bg-white/5 border border-white/10'
                  }`}
                >
                  <div className={`w-4 h-4 rounded-full ${
                    task.completed 
                      ? 'bg-green-400' 
                      : `bg-gradient-to-r ${getPriorityBg(task.priority)}`
                  }`} />
                  
                  <div className="flex-1">
                    <p className={`text-sm ${
                      task.completed 
                        ? 'text-gray-400 line-through' 
                        : 'text-gray-300'
                    }`}>
                      {task.content}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-purple-400">{task.project}</span>
                      {task.due_date && (
                        <span className="text-xs text-orange-400 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className={`text-xs px-2 py-1 rounded ${getPriorityColor(task.priority)}`}>
                    P{task.priority}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* AI Insights */}
          {insights && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="glass-dark rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Task Insights</h3>
              
              <div className="space-y-3">
                {insights.insights.map((insight, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-2" />
                    <p className="text-sm text-gray-300">{insight}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* Empty State */}
      {!status.connected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <CheckSquare className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">
            Connect Your Todoist
          </h3>
          <p className="text-gray-400 mb-6">
            Analyze your task patterns and boost productivity
          </p>
        </motion.div>
      )}
    </div>
  )
}

export default ModernTodoistIntegration