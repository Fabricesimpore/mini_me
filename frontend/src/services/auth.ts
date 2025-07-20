import { api } from './api'

export const authService = {
  async login(username: string, password: string) {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    
    const response = await api.post('/api/auth/token', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  async register(email: string, username: string, password: string) {
    const response = await api.post('/api/auth/register', {
      email,
      username,
      password,
    })
    return response.data
  },

  async getMe(token: string) {
    const response = await api.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.data
  },
}