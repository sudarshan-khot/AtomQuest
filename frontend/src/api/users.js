import api from './index'

export const getUsers = async () => {
  const response = await api.get('/api/user-management/')
  return response.data
}

export const getDepartments = async () => {
  const response = await api.get('/api/departments/')
  return response.data
}

export const createUser = async (data) => {
  const response = await api.post('/api/user-management/', data)
  return response.data
}

export const updateUser = async ({ id, ...data }) => {
  const response = await api.put(`/api/user-management/${id}/`, data)
  return response.data
}

export const deactivateUser = async (id) => {
  const response = await api.post(`/api/user-management/${id}/deactivate/`)
  return response.data
}

export const reactivateUser = async (id) => {
  const response = await api.post(`/api/user-management/${id}/reactivate/`)
  return response.data
}

export const getNotifications = async () => {
  const response = await api.get('/api/notifications/')
  return response.data
}
