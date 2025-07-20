import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, Search, Plus, Calendar, Tag, Star, 
  Clock, Filter, Grid, List, Trash2, Edit 
} from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

interface Memory {
  id: string
  content: string
  category: string
  importance: number
  timestamp: Date
  tags: string[]
  source: string
  context?: string
}

const ModernMemory: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [categories, setCategories] = useState<Record<string, number>>({})
  const { token } = useAuthStore()

  useEffect(() => {
    loadMemories()
    loadCategories()
  }, [])

  const loadMemories = async () => {
    try {
      const response = await api.get('/api/memory/all', {
        headers: { Authorization: `Bearer ${token}` },
        params: { category: selectedCategory }
      })
      setMemories(response.data)
    } catch (error) {
      console.error('Failed to load memories:', error)
      toast.error('Failed to load memories')
    }
  }

  const loadCategories = async () => {
    try {
      const response = await api.get('/api/memory/categories', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setCategories(response.data.categories)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const searchMemories = async () => {
    if (!searchQuery.trim()) {
      loadMemories()
      return
    }

    try {
      const response = await api.get('/api/memory/search', {
        headers: { Authorization: `Bearer ${token}` },
        params: { query: searchQuery, category: selectedCategory }
      })
      setMemories(response.data)
    } catch (error) {
      console.error('Failed to search memories:', error)
      toast.error('Failed to search memories')
    }
  }

  const createMemory = async (memoryData: any) => {
    try {
      await api.post('/api/memory/create', memoryData, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Memory created successfully')
      setShowCreateModal(false)
      loadMemories()
    } catch (error) {
      console.error('Failed to create memory:', error)
      toast.error('Failed to create memory')
    }
  }

  const deleteMemory = async (id: string) => {
    try {
      await api.delete(`/api/memory/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('Memory deleted')
      loadMemories()
    } catch (error) {
      console.error('Failed to delete memory:', error)
      toast.error('Failed to delete memory')
    }
  }

  const categoryColors = {
    learning: 'from-blue-500 to-cyan-500',
    work: 'from-purple-500 to-pink-500',
    personal: 'from-green-500 to-emerald-500',
    ideas: 'from-orange-500 to-red-500'
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <div className="mb-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold gradient-text mb-2">Memory Bank</h1>
          <p className="text-gray-400 text-lg">Your digital consciousness archive</p>
        </motion.div>
      </div>

      {/* Controls Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-dark rounded-xl p-6 mb-8"
      >
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchMemories()}
              placeholder="Search memories..."
              className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Category Filter */}
          <div className="flex gap-2">
            {Object.entries(categories).map(([category, count]) => (
              <motion.button
                key={category}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setSelectedCategory(selectedCategory === category ? null : category)
                  loadMemories()
                }}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                  selectedCategory === category
                    ? 'bg-purple-500/20 border border-purple-500/50 text-purple-400'
                    : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white'
                }`}
              >
                {category}
                <span className="text-xs bg-white/10 px-2 py-1 rounded-full">{count}</span>
              </motion.button>
            ))}
          </div>

          {/* View Mode */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-3 rounded-lg transition-all ${
                viewMode === 'grid'
                  ? 'bg-purple-500/20 text-purple-400'
                  : 'bg-white/5 text-gray-400 hover:text-white'
              }`}
            >
              <Grid className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-3 rounded-lg transition-all ${
                viewMode === 'list'
                  ? 'bg-purple-500/20 text-purple-400'
                  : 'bg-white/5 text-gray-400 hover:text-white'
              }`}
            >
              <List className="w-5 h-5" />
            </button>
          </div>

          {/* Create Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg text-white font-medium flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Memory
          </motion.button>
        </div>
      </motion.div>

      {/* Memories Grid/List */}
      <AnimatePresence mode="wait">
        {viewMode === 'grid' ? (
          <motion.div
            key="grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {memories.map((memory, index) => {
              const categoryColor = categoryColors[memory.category as keyof typeof categoryColors] || 'from-gray-500 to-gray-600'
              return (
                <motion.div
                  key={memory.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="card glass-dark group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-2 rounded-lg bg-gradient-to-r ${categoryColor}`}>
                      <Brain className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                        <Edit className="w-4 h-4 text-gray-400" />
                      </button>
                      <button 
                        onClick={() => deleteMemory(memory.id)}
                        className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </button>
                    </div>
                  </div>

                  <h3 className="text-lg font-medium text-white mb-2 line-clamp-2">
                    {memory.content}
                  </h3>

                  <div className="flex items-center gap-4 text-sm text-gray-400 mb-4">
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {new Date(memory.timestamp).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <Star className="w-4 h-4" />
                      {Math.round(memory.importance * 100)}%
                    </span>
                  </div>

                  {memory.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {memory.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-xs px-2 py-1 bg-white/10 text-gray-300 rounded-full"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </motion.div>
              )
            })}
          </motion.div>
        ) : (
          <motion.div
            key="list"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {memories.map((memory, index) => (
              <motion.div
                key={memory.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="card glass-dark flex items-center justify-between"
              >
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-white mb-1">{memory.content}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>{memory.category}</span>
                    <span>{new Date(memory.timestamp).toLocaleDateString()}</span>
                    <div className="flex gap-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${
                            i < Math.round(memory.importance * 5)
                              ? 'text-yellow-400 fill-yellow-400'
                              : 'text-gray-600'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                    <Edit className="w-4 h-4 text-gray-400" />
                  </button>
                  <button 
                    onClick={() => deleteMemory(memory.id)}
                    className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Memory Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <CreateMemoryModal
            onClose={() => setShowCreateModal(false)}
            onCreate={createMemory}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// Create Memory Modal Component
const CreateMemoryModal: React.FC<{
  onClose: () => void
  onCreate: (data: any) => void
}> = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    content: '',
    category: 'personal',
    importance: 0.5,
    tags: '',
    context: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCreate({
      ...formData,
      tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg glass-dark rounded-2xl p-6"
      >
        <h2 className="text-2xl font-bold gradient-text mb-6">Create New Memory</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Memory Content
            </label>
            <textarea
              required
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none transition-colors h-32 resize-none"
              placeholder="What would you like to remember?"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-purple-500 focus:outline-none transition-colors"
              >
                <option value="personal">Personal</option>
                <option value="work">Work</option>
                <option value="learning">Learning</option>
                <option value="ideas">Ideas</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Importance ({Math.round(formData.importance * 100)}%)
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={formData.importance}
                onChange={(e) => setFormData({ ...formData, importance: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tags (comma separated)
            </label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none transition-colors"
              placeholder="work, important, project-x"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Context (optional)
            </label>
            <input
              type="text"
              value={formData.context}
              onChange={(e) => setFormData({ ...formData, context: e.target.value })}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none transition-colors"
              placeholder="During team meeting..."
            />
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-white/5 border border-white/10 rounded-lg text-white font-medium hover:bg-white/10 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg text-white font-medium hover:opacity-90 transition-opacity"
            >
              Create Memory
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  )
}

export default ModernMemory