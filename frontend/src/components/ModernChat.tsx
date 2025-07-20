import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, Brain, Mic, Paperclip, MoreVertical } from 'lucide-react'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

interface Message {
  id: string
  content: string
  timestamp: Date
  user_id: string
  is_twin: boolean
  parent_id?: string
}

const ModernChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const { token } = useAuthStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Load chat history
    loadChatHistory()
  }, [])

  const loadChatHistory = async () => {
    try {
      const response = await api.get('/api/chat/history', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        // For now, just show a message that recording is complete
        toast.success('Voice recording complete (feature in development)')
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      toast.success('Recording started...')
    } catch (error) {
      toast.error('Failed to access microphone')
      console.error('Recording error:', error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = input
    setInput('')
    setIsLoading(true)
    setIsTyping(true)

    // Add user message immediately
    const tempUserMsg: Message = {
      id: Date.now().toString(),
      content: userMessage,
      timestamp: new Date(),
      user_id: 'current-user',
      is_twin: false
    }
    setMessages(prev => [...prev, tempUserMsg])

    try {
      const response = await api.post('/api/chat/message', 
        { content: userMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Simulate typing delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setIsTyping(false)
      setMessages(prev => [...prev, response.data])
    } catch (error) {
      toast.error('Failed to send message')
      setIsTyping(false)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-black/50 rounded-2xl overflow-hidden glass-dark">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Brain className="w-10 h-10 text-purple-400" />
            <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          </div>
          <div>
            <h2 className="text-xl font-semibold gradient-text">Your Digital Twin</h2>
            <p className="text-sm text-gray-400">Always learning from you</p>
          </div>
        </div>
        <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
          <MoreVertical className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.is_twin ? 'justify-start' : 'justify-end'}`}
            >
              <div className={`max-w-[70%] ${message.is_twin ? 'order-2' : 'order-1'}`}>
                <div
                  className={`p-4 rounded-2xl ${
                    message.is_twin
                      ? 'bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-purple-500/30'
                      : 'bg-blue-600/20 border border-blue-500/30'
                  }`}
                >
                  <p className="text-white/90">{message.content}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
              {message.is_twin && (
                <div className="order-1 mr-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing Indicator */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center space-x-2"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className="bg-purple-600/20 border border-purple-500/30 rounded-2xl p-4">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-white/10">
        <div className="flex items-center space-x-3">
          <button className="p-3 hover:bg-white/10 rounded-lg transition-colors">
            <Paperclip className="w-5 h-5 text-gray-400" />
          </button>
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask your twin anything..."
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none transition-colors"
              disabled={isLoading}
            />
          </div>
          <button 
            onClick={isRecording ? stopRecording : startRecording}
            className={`p-3 hover:bg-white/10 rounded-lg transition-colors ${isRecording ? 'bg-red-500/20' : ''}`}
          >
            <Mic className={`w-5 h-5 ${isRecording ? 'text-red-400 animate-pulse' : 'text-gray-400'}`} />
          </button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Send className="w-5 h-5" />
          </motion.button>
        </div>
      </div>
    </div>
  )
}

export default ModernChat