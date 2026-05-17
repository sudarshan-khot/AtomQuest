import api from './index'

export const getGoals = async (params = {}) => {
  const response = await api.get('/api/goals/', { params })
  return response.data
}

export const getGoal = async (id) => {
  const response = await api.get(`/api/goals/${id}/`)
  return response.data
}

export const createGoal = async (data) => {
  const response = await api.post('/api/goals/', data)
  return response.data
}

export const updateGoal = async ({ id, ...data }) => {
  const response = await api.patch(`/api/goals/${id}/`, data)
  return response.data
}

export const deleteGoal = async (id) => {
  await api.delete(`/api/goals/${id}/`)
}

export const submitGoal = async (id) => {
  const response = await api.post(`/api/goals/${id}/submit/`)
  return response.data
}

export const approveGoal = async ({ id, approval_comments = '' }) => {
  const response = await api.post(`/api/goals/${id}/approve/`, { approval_comments })
  return response.data
}

export const rejectGoal = async ({ id, rejection_reason }) => {
  const response = await api.post(`/api/goals/${id}/reject/`, { rejection_reason })
  return response.data
}

export const getPendingGoals = async () => {
  const response = await api.get('/api/goals/pending/')
  return response.data
}

export const editDuringReview = async ({ id, ...data }) => {
  const response = await api.patch(`/api/goals/${id}/edit_during_review/`, data)
  return response.data
}
