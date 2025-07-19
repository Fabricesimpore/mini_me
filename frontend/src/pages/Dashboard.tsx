import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { Line, Doughnut } from 'react-chartjs-2'
import { useNavigate } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

const Dashboard = () => {
  const navigate = useNavigate()
  const { data: patterns } = useQuery({
    queryKey: ['behavioral-patterns'],
    queryFn: async () => {
      const response = await api.get('/api/behavioral/patterns')
      return response.data
    },
  })

  const { data: integrationStatus } = useQuery({
    queryKey: ['integration-status'],
    queryFn: async () => {
      const response = await api.get('/api/integrations/status')
      return response.data
    },
  })

  const activityData = {
    labels: ['6AM', '9AM', '12PM', '3PM', '6PM', '9PM'],
    datasets: [
      {
        label: 'Activity Level',
        data: [20, 85, 70, 90, 75, 30],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const behaviorDistribution = {
    labels: ['Communication', 'Browsing', 'Decision Making', 'Learning'],
    datasets: [
      {
        data: [30, 25, 20, 25],
        backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'],
      },
    ],
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Digital Twin Dashboard
      </h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Patterns Learned</p>
              <p className="text-2xl font-bold text-gray-900">247</p>
            </div>
            <div className="text-3xl">🧠</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Integrations</p>
              <p className="text-2xl font-bold text-gray-900">
                {integrationStatus ? Object.values(integrationStatus.integrations).filter((i: any) => i.connected).length : 0}
              </p>
            </div>
            <div className="text-3xl">🔗</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Memories Stored</p>
              <p className="text-2xl font-bold text-gray-900">1,843</p>
            </div>
            <div className="text-3xl">💾</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Accuracy</p>
              <p className="text-2xl font-bold text-gray-900">92%</p>
            </div>
            <div className="text-3xl">🎯</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Daily Activity Pattern
          </h2>
          <Line data={activityData} options={{ responsive: true }} />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Behavior Distribution
          </h2>
          <div className="max-w-xs mx-auto">
            <Doughnut data={behaviorDistribution} options={{ responsive: true }} />
          </div>
        </div>
      </div>

      {/* Chat Widget */}
      <div className="mt-8 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Chat with Your Digital Twin</h2>
            <p className="text-indigo-100 mb-4">
              Start a conversation with yourself. Share memories, ask questions, or reflect on your day.
            </p>
            <button
              onClick={() => navigate('/chat')}
              className="bg-white text-indigo-600 px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors flex items-center gap-2"
            >
              <MessageCircle size={20} />
              Open Chat
            </button>
          </div>
          <div className="text-6xl opacity-20">
            💬
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Learning</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-2 h-2 mt-2 bg-green-400 rounded-full"></div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">
                  Email Response Pattern Learned
                </p>
                <p className="text-sm text-gray-500">
                  Learned your typical response time and style for work emails
                </p>
                <p className="text-xs text-gray-400 mt-1">2 hours ago</p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-2 h-2 mt-2 bg-blue-400 rounded-full"></div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">
                  Shopping Behavior Updated
                </p>
                <p className="text-sm text-gray-500">
                  Identified preference for comparing at least 3 options before purchase
                </p>
                <p className="text-xs text-gray-400 mt-1">5 hours ago</p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-2 h-2 mt-2 bg-purple-400 rounded-full"></div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">
                  New Relationship Mapped
                </p>
                <p className="text-sm text-gray-500">
                  Added communication patterns with new contact "Alex Chen"
                </p>
                <p className="text-xs text-gray-400 mt-1">1 day ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard