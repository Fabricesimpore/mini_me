import React from 'react'
import DigitalTwinChat from '../components/DigitalTwinChat'

const Chat: React.FC = () => {
  return (
    <div className="h-full">
      <div className="h-full max-w-4xl mx-auto">
        <DigitalTwinChat />
      </div>
    </div>
  )
}

export default Chat