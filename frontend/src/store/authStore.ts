import { create } from 'zustand'
import { authService } from '../services/auth'

interface User {
  id: string
  email: string
  username: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const response = await authService.login(email, password)
    set({
      token: response.access_token,
      isAuthenticated: true,
    })
    
    // Fetch user data
    const userData = await authService.getMe(response.access_token)
    set({ user: userData })
  },

  register: async (email: string, username: string, password: string) => {
    const userData = await authService.register(email, username, password)
    set({ user: userData })
    
    // Auto-login after registration using email
    const response = await authService.login(email, password)
    set({
      token: response.access_token,
      isAuthenticated: true,
    })
  },

  logout: () => {
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  },

  setUser: (user: User) => set({ user }),
}))