import api from './index'

export const getCheckIns = async (params = {}) => {
  const response = await api.get('/api/checkins/', { params })
  return response.data
}

export const createCheckIn = async (data) => {
  const response = await api.post('/api/checkins/', data)
  return response.data
}

export const getPendingCheckIns = async () => {
  const response = await api.get('/api/checkins/pending/')
  return response.data
}

export const approveCheckIn = async ({ id, approval_comments = '' }) => {
  const response = await api.post(`/api/checkins/${id}/approve/`, { approval_comments })
  return response.data
}

export const rejectCheckIn = async ({ id, rejection_comments }) => {
  const response = await api.post(`/api/checkins/${id}/reject/`, { rejection_comments })
  return response.data
}
