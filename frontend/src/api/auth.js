import api from './index'

export const login = async ({ username, password }) => {
  const response = await api.post('/api-token-auth/', { username, password })
  return response.data
}

export const getMe = async () => {
  const response = await api.get('/api/users/me/')
  return response.data
}

export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}
