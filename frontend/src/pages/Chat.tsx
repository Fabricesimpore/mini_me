import React from 'react'
import ModernChat from '../components/ModernChat'
import { motion } from 'framer-motion'

const Chat: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-full flex flex-col"
    >
      <div className="mb-6">
        <h1 className="text-3xl font-bold gradient-text">Chat with Your Digital Twin</h1>
        <p className="text-gray-400 mt-2">Have a conversation with your AI consciousness</p>
      </div>
      <div className="flex-1 max-w-4xl mx-auto w-full">
        <ModernChat />
      </div>
    </motion.div>
  )
}

export default Chat