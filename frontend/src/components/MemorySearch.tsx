import React, { useState, useCallback } from 'react';
import { Search, Brain, Clock, Tag, Link, Sparkles, Calendar, Filter, X } from 'lucide-react';
import { api } from '../services/api';
import { format } from 'date-fns';

interface Memory {
  id: string;
  content: string;
  type: string;
  metadata: any;
  created_at: string;
  similarity?: number;
  combined_score?: number;
  search_type?: string;
}

interface RelatedMemory extends Memory {
  relationship?: {
    type: string;
    strength: number;
  };
}

interface MemorySearchProps {
  onClose?: () => void
}

const MemorySearch: React.FC<MemorySearchProps> = ({ onClose }) => {
  const [query, setQuery] = useState('');
  const [memories, setMemories] = useState<Memory[]>([]);
  const [relatedMemories, setRelatedMemories] = useState<RelatedMemory[]>([]);
  const [selectedMemoryId, setSelectedMemoryId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchType, setSearchType] = useState<'semantic' | 'hybrid'>('hybrid');
  const [memoryType, setMemoryType] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!query.trim() && memoryType === 'all' && !startDate && !endDate) {
      return;
    }

    setLoading(true);
    setHasSearched(true);
    try {
      if (searchType === 'semantic') {
        const params = new URLSearchParams({
          query: query.trim(),
          ...(memoryType !== 'all' && { memory_type: memoryType }),
          limit: '20',
          similarity_threshold: '0.5'
        });
        
        const response = await api.get(`/api/memory/recall?${params}`);
        setMemories(response.data.memories);
      } else {
        // Use the original search endpoint for backward compatibility
        const params = new URLSearchParams({
          query: query.trim(),
          ...(memoryType !== 'all' && { memory_type: memoryType }),
          ...(startDate && { start_date: new Date(startDate).toISOString() }),
          ...(endDate && { end_date: new Date(endDate).toISOString() }),
          limit: '20'
        });

        const response = await api.get(`/api/chat/search?${params}`);
        setMemories(response.data.results || []);
      }
      setRelatedMemories([]);
      setSelectedMemoryId(null);
    } catch (error) {
      console.error('Search error:', error);
      // Try the new hybrid search endpoint if the old one fails
      if (searchType === 'hybrid') {
        try {
          const response = await api.post('/api/memory/search', {
            query: query.trim(),
            memory_type: memoryType,
            keyword_weight: 0.3,
            semantic_weight: 0.7,
            limit: 20
          });
          setMemories(response.data.results);
        } catch (hybridError) {
          console.error('Hybrid search error:', hybridError);
          setMemories([]);
        }
      }
    } finally {
      setLoading(false);
    }
  }, [query, searchType, memoryType, startDate, endDate]);

  const handleGetRelated = useCallback(async (memoryId: string) => {
    setLoading(true);
    try {
      const response = await api.get(`/api/memory/related/${memoryId}`);
      setRelatedMemories(response.data.related_memories);
      setSelectedMemoryId(memoryId);
    } catch (error) {
      console.error('Error getting related memories:', error);
      setRelatedMemories([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearFilters = () => {
    setQuery('');
    setMemoryType('all');
    setStartDate('');
    setEndDate('');
    setMemories([]);
    setRelatedMemories([]);
    setSelectedMemoryId(null);
    setHasSearched(false);
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch {
      return dateString;
    }
  };

  const getMemoryTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      episodic: 'bg-blue-100 text-blue-800',
      semantic: 'bg-green-100 text-green-800',
      procedural: 'bg-purple-100 text-purple-800',
      social: 'bg-pink-100 text-pink-800',
      conversation: 'bg-gray-100 text-gray-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="h-6 w-6 text-purple-600" />
          Enhanced Memory Search
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

      {/* Search Controls */}
      <div className="space-y-4 mb-6">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search your memories with AI understanding..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <Search className="absolute left-3 top-3.5 text-gray-400" size={20} />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-yellow-500" />
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as 'semantic' | 'hybrid')}
              className="border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="hybrid">Hybrid Search (AI + Keywords)</option>
              <option value="semantic">Semantic Search (AI Only)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-500" />
            <select
              value={memoryType}
              onChange={(e) => setMemoryType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Types</option>
              <option value="episodic">Events</option>
              <option value="semantic">Knowledge</option>
              <option value="procedural">Tasks</option>
              <option value="social">Social</option>
              <option value="conversation">Conversations</option>
            </select>
          </div>

          {searchType === 'hybrid' && (
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-gray-500" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Start date"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="End date"
              />
            </div>
          )}

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
          disabled={loading}
          className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>Loading...</>
          ) : (
            <>
              <Search size={20} />
              Search Memories
            </>
          )}
        </button>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {hasSearched && memories.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Brain size={48} className="mx-auto mb-4 text-gray-300" />
            <p>No memories found matching your search criteria.</p>
            <p className="text-sm mt-2">Try adjusting your filters or search terms.</p>
          </div>
        ) : memories.length > 0 && (
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-yellow-500" />
                Search Results
              </h3>
              <div className="space-y-4">
                {memories.map((memory) => (
                  <div
                    key={memory.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedMemoryId === memory.id
                        ? 'ring-2 ring-purple-500 border-purple-300'
                        : 'border-gray-200 hover:shadow-md'
                    }`}
                    onClick={() => handleGetRelated(memory.id)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getMemoryTypeColor(
                          memory.type
                        )}`}
                      >
                        {memory.type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatDate(memory.created_at)}
                      </span>
                    </div>

                    <p className="text-gray-800 mb-2">{memory.content}</p>

                    {/* Score indicators */}
                    {(memory.similarity || memory.search_type) && (
                      <div className="flex gap-4 text-xs mb-2">
                        {memory.similarity && (
                          <div className="flex items-center gap-1">
                            <div className="w-16 bg-gray-200 rounded-full h-1.5">
                              <div
                                className="bg-green-500 h-1.5 rounded-full"
                                style={{
                                  width: `${memory.similarity * 100}%`
                                }}
                              />
                            </div>
                            <span className="text-gray-600">
                              {(memory.similarity * 100).toFixed(0)}%
                            </span>
                          </div>
                        )}
                        {memory.search_type && (
                          <span
                            className={`px-2 py-0.5 rounded text-xs ${
                              memory.search_type === 'both'
                                ? 'bg-purple-100 text-purple-700'
                                : memory.search_type === 'semantic'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-orange-100 text-orange-700'
                            }`}
                          >
                            {memory.search_type}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Metadata tags */}
                    {memory.metadata && Object.keys(memory.metadata).length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {memory.metadata.person && (
                          <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                            👤 {Array.isArray(memory.metadata.person) ? memory.metadata.person.join(', ') : memory.metadata.person}
                          </span>
                        )}
                        {memory.metadata.place && (
                          <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded">
                            📍 {Array.isArray(memory.metadata.place) ? memory.metadata.place.join(', ') : memory.metadata.place}
                          </span>
                        )}
                        {memory.metadata.activity && (
                          <span className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                            🎯 {Array.isArray(memory.metadata.activity) ? memory.metadata.activity.join(', ') : memory.metadata.activity}
                          </span>
                        )}
                        {memory.metadata.emotions && memory.metadata.emotions.length > 0 && (
                          <span className="text-xs bg-pink-50 text-pink-700 px-2 py-1 rounded">
                            💭 {memory.metadata.emotions.join(', ')}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Related Memories */}
            {selectedMemoryId && (
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Link className="h-5 w-5 text-purple-600" />
                  Related Memories
                </h3>
                {relatedMemories.length > 0 ? (
                  <div className="space-y-4">
                    {relatedMemories.map((memory) => (
                      <div
                        key={memory.id}
                        className="border border-gray-200 rounded-lg p-4"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getMemoryTypeColor(
                              memory.type
                            )}`}
                          >
                            {memory.type}
                          </span>
                          {memory.relationship && (
                            <div className="text-xs text-gray-600">
                              <span className="font-medium">
                                {memory.relationship.type}
                              </span>
                              <span className="ml-2">
                                ({(memory.relationship.strength * 100).toFixed(0)}%)
                              </span>
                            </div>
                          )}
                        </div>

                        <p className="text-gray-800 mb-2">{memory.content}</p>

                        <div className="text-xs text-gray-500 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(memory.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
                    {loading ? (
                      <p>Loading related memories...</p>
                    ) : (
                      <p>Click on a memory to see related ones</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {memories.length > 0 && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Showing {memories.length} memories
        </div>
      )}
    </div>
  );
};

export default MemorySearch;