import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const http = axios.create({ baseURL: '/api' })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const text = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : ''
    if (status === 401 && router.currentRoute.value.path !== '/login') {
      localStorage.removeItem('token')
      router.push('/login')
    } else {
      ElMessage.error(text || '请求失败')
    }
    return Promise.reject(error)
  },
)

export default http
