import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器 — 注入 JWT token
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 — 统一错误处理
api.interceptors.response.use(
  (response) => {
    const { code, message } = response.data
    if (code === 401) {
      // 登录/注册页的 401 交由组件自行处理，不触发全局拦截
      const isAuthPage = ['/login', '/register'].includes(window.location.pathname)
      if (!isAuthPage) {
        const userStore = useUserStore()
        userStore.clearAuth()
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
      return Promise.reject(new Error(message))
    }
    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          ElMessage.error('未登录或登录已过期')
          break
        case 403:
          ElMessage.error(data?.message || '无权操作')
          break
        case 409:
          ElMessage.error(data?.message || '数据冲突')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        case 502:
          ElMessage.error('AI 服务暂时不可用，请稍后重试')
          break
        default:
          ElMessage.error(data?.message || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络后重试')
    } else {
      ElMessage.error('网络异常，请检查连接')
    }
    return Promise.reject(error)
  }
)

export default api
