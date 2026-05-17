import api from './index'

export const getCycles = async () => {
  const response = await api.get('/api/cycles/')
  return response.data
}

export const createCycle = async (data) => {
  const response = await api.post('/api/cycles/', data)
  return response.data
}

export const activateCycle = async (id) => {
  const response = await api.post(`/api/cycles/${id}/activate/`)
  return response.data
}

export const closeCycle = async (id) => {
  const response = await api.post(`/api/cycles/${id}/close/`)
  return response.data
}

export const getThrustAreas = async () => {
  const response = await api.get('/api/thrust-areas/')
  return response.data
}

export const getUoMTypes = async () => {
  const response = await api.get('/api/uom-types/')
  return response.data
}
