import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for LLM
})

export async function extractComplaint({ file, text }) {
  const formData = new FormData()
  if (file) {
    formData.append('file', file)
  }
  if (text) {
    formData.append('text', text)
  }
  const res = await api.post('/api/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function saveComplaint(payload) {
  const res = await api.post('/api/complaints', payload)
  return res.data
}

export async function listComplaints() {
  const res = await api.get('/api/complaints')
  return res.data
}

export default api
