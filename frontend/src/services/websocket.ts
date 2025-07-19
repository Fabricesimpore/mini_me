import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export const initializeWebSocket = (userId: string) => {
  if (socket) {
    socket.disconnect()
  }

  const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
  
  // For now, let's not connect WebSocket automatically
  console.log('WebSocket connection disabled for initial setup')
  return null

  socket.on('connect', () => {
    console.log('Connected to Digital Twin platform')
  })

  socket.on('disconnect', () => {
    console.log('Disconnected from Digital Twin platform')
  })

  socket.on('pattern_learned', (data) => {
    console.log('New pattern learned:', data)
    // Update UI or trigger notifications
  })

  return socket
}

export const sendBehavioralData = (data: any) => {
  if (socket && socket.connected) {
    socket.emit('behavioral_data', data)
  }
}

export const disconnectWebSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}