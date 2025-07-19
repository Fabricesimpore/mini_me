import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Brain, TrendingUp, Users, Clock } from 'lucide-react'
import { api } from '../services/api'
import MemorySearch from '../components/MemorySearch'

interface MemoryInsights {
  total_memories: number
  memory_types: Record<string, number>
  common_activities: Record<string, number>
  frequent_people: Record<string, number>
  emotional_patterns: Record<string, number>
  active_times: Record<string, number>
}

const Memory = () => {
  const [showSearch, setShowSearch] = useState(false)

  const { data: insights, isLoading } = useQuery<MemoryInsights>({
    queryKey: ['memory-insights'],
    queryFn: async () => {
      const response = await api.get('/api/chat/insights')
      return response.data
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  const getTypeCount = (type: string) => {
    return insights?.memory_types[type] || 0
  }

  const getTopItems = (items: Record<string, number>, limit = 5) => {
    if (!items) return []
    return Object.entries(items)
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Memory System</h1>
        <button
          onClick={() => setShowSearch(!showSearch)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
        >
          <Search size={20} />
          Search Memories
        </button>
      </div>

      {showSearch && (
        <div className="mb-8">
          <MemorySearch onClose={() => setShowSearch(false)} />
        </div>
      )}
      
      {/* Memory Type Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Episodic</h3>
          <p className="text-2xl font-bold text-twin-primary">{getTypeCount('episodic')}</p>
          <p className="text-sm text-gray-500">Events & Experiences</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Semantic</h3>
          <p className="text-2xl font-bold text-twin-primary">{getTypeCount('semantic')}</p>
          <p className="text-sm text-gray-500">Facts & Knowledge</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Procedural</h3>
          <p className="text-2xl font-bold text-twin-primary">{getTypeCount('procedural')}</p>
          <p className="text-sm text-gray-500">Skills & Procedures</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Social</h3>
          <p className="text-2xl font-bold text-twin-primary">{getTypeCount('social')}</p>
          <p className="text-sm text-gray-500">Relationships</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Total</h3>
          <p className="text-2xl font-bold text-twin-primary">{insights?.total_memories || 0}</p>
          <p className="text-sm text-gray-500">All Memories</p>
        </div>
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Common Activities */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp size={20} />
              Common Activities
            </h2>
          </div>
          <div className="p-6">
            {getTopItems(insights?.common_activities || {}).length > 0 ? (
              <div className="space-y-3">
                {getTopItems(insights?.common_activities || {}).map(([activity, count]) => (
                  <div key={activity} className="flex items-center justify-between">
                    <span className="text-gray-700 capitalize">{activity}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full"
                          style={{
                            width: `${(count / insights.total_memories) * 100}%`
                          }}
                        />
                      </div>
                      <span className="text-sm text-gray-500 w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No activity patterns detected yet.</p>
            )}
          </div>
        </div>

        {/* Frequent People */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Users size={20} />
              Frequent People
            </h2>
          </div>
          <div className="p-6">
            {getTopItems(insights?.frequent_people || {}).length > 0 ? (
              <div className="space-y-3">
                {getTopItems(insights?.frequent_people || {}).map(([person, count]) => (
                  <div key={person} className="flex items-center justify-between">
                    <span className="text-gray-700">{person}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-pink-600 h-2 rounded-full"
                          style={{
                            width: `${(count / insights.total_memories) * 100}%`
                          }}
                        />
                      </div>
                      <span className="text-sm text-gray-500 w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No social patterns detected yet.</p>
            )}
          </div>
        </div>

        {/* Emotional Patterns */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Brain size={20} />
              Emotional Patterns
            </h2>
          </div>
          <div className="p-6">
            {getTopItems(insights?.emotional_patterns || {}).length > 0 ? (
              <div className="space-y-3">
                {getTopItems(insights?.emotional_patterns || {}).map(([emotion, count]) => (
                  <div key={emotion} className="flex items-center justify-between">
                    <span className="text-gray-700 capitalize">{emotion}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{
                            width: `${(count / Math.max(...Object.values(insights.emotional_patterns))) * 100}%`
                          }}
                        />
                      </div>
                      <span className="text-sm text-gray-500 w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No emotional patterns detected yet.</p>
            )}
          </div>
        </div>

        {/* Active Times */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Clock size={20} />
              Active Times
            </h2>
          </div>
          <div className="p-6">
            {Object.keys(insights?.active_times || {}).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(insights?.active_times || {})
                  .sort(([, a], [, b]) => b - a)
                  .map(([time, count]) => (
                    <div key={time} className="flex items-center justify-between">
                      <span className="text-gray-700 capitalize">{time}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-600 h-2 rounded-full"
                            style={{
                              width: `${(count / insights.total_memories) * 100}%`
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-500 w-8 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-gray-500">No time patterns detected yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Help Text */}
      {insights?.total_memories === 0 && (
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <Brain size={48} className="mx-auto mb-4 text-blue-600" />
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Start Building Your Memory
          </h3>
          <p className="text-blue-700">
            Your Digital Twin learns from your conversations. Start chatting to build your memory database!
          </p>
        </div>
      )}
    </div>
  )
}

export default Memory