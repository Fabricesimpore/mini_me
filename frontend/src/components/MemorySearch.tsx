import React, { useState } from 'react'
import { Search, Calendar, Filter, X } from 'lucide-react'
import { api } from '../services/api'
import { format } from 'date-fns'

interface MemorySearchProps {
  onClose?: () => void
}

interface SearchResult {
  id: string
  content: string
  type: string
  metadata: any
  created_at: string
}

const MemorySearch: React.FC<MemorySearchProps> = ({ onClose }) => {
  const [query, setQuery] = useState('')
  const [memoryType, setMemoryType] = useState('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async () => {
    if (!query.trim() && memoryType === 'all' && !startDate && !endDate) {
      return
    }

    setIsLoading(true)
    setHasSearched(true)

    try {
      const params = new URLSearchParams({
        query: query.trim(),
        ...(memoryType !== 'all' && { memory_type: memoryType }),
        ...(startDate && { start_date: new Date(startDate).toISOString() }),
        ...(endDate && { end_date: new Date(endDate).toISOString() }),
        limit: '50'
      })

      const response = await api.get(`/api/chat/search?${params}`)
      setResults(response.data.results || [])
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const clearFilters = () => {
    setQuery('')
    setMemoryType('all')
    setStartDate('')
    setEndDate('')
    setResults([])
    setHasSearched(false)
  }

  const getMemoryTypeColor = (type: string) => {
    const colors = {
      episodic: 'bg-blue-100 text-blue-800',
      semantic: 'bg-green-100 text-green-800',
      procedural: 'bg-purple-100 text-purple-800',
      social: 'bg-pink-100 text-pink-800',
      conversation: 'bg-gray-100 text-gray-800'
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a')
    } catch {
      return dateString
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Search size={24} />
          Memory Search
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={24} />
          </button>
        )}
      </div>

      {/* Search Bar */}
      <div className="space-y-4 mb-6">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search your memories..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <Search className="absolute left-3 top-3.5 text-gray-400" size={20} />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-500" />
            <select
              value={memoryType}
              onChange={(e) => setMemoryType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Types</option>
              <option value="episodic">Events</option>
              <option value="semantic">Knowledge</option>
              <option value="procedural">Tasks</option>
              <option value="social">Social</option>
              <option value="conversation">Conversations</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-gray-500" />
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Start date"
            />
            <span className="text-gray-500">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="End date"
            />
          </div>

          <button
            onClick={clearFilters}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear filters
          </button>
        </div>

        {/* Search Button */}
        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Searching...' : 'Search Memories'}
        </button>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {hasSearched && results.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Search size={48} className="mx-auto mb-4 text-gray-300" />
            <p>No memories found matching your search criteria.</p>
            <p className="text-sm mt-2">Try adjusting your filters or search terms.</p>
          </div>
        ) : (
          results.map((result) => (
            <div
              key={result.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <span
                  className={`text-xs px-2 py-1 rounded-full ${getMemoryTypeColor(
                    result.type
                  )}`}
                >
                  {result.type}
                </span>
                <span className="text-xs text-gray-500">
                  {formatDate(result.created_at)}
                </span>
              </div>
              <p className="text-gray-800 mb-2">{result.content}</p>
              {result.metadata && Object.keys(result.metadata).length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <div className="flex flex-wrap gap-2">
                    {result.metadata.person && (
                      <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                        👤 {Array.isArray(result.metadata.person) ? result.metadata.person.join(', ') : result.metadata.person}
                      </span>
                    )}
                    {result.metadata.place && (
                      <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded">
                        📍 {Array.isArray(result.metadata.place) ? result.metadata.place.join(', ') : result.metadata.place}
                      </span>
                    )}
                    {result.metadata.activity && (
                      <span className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                        🎯 {Array.isArray(result.metadata.activity) ? result.metadata.activity.join(', ') : result.metadata.activity}
                      </span>
                    )}
                    {result.metadata.emotions && result.metadata.emotions.length > 0 && (
                      <span className="text-xs bg-pink-50 text-pink-700 px-2 py-1 rounded">
                        💭 {result.metadata.emotions.join(', ')}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {results.length > 0 && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Showing {results.length} memories
        </div>
      )}
    </div>
  )
}

export default MemorySearch