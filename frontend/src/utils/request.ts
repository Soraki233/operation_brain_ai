import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { createDiscreteApi } from 'naive-ui'
import router from '@/router'

const { message } = createDiscreteApi(['message'])

let handling401 = false

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401 && !handling401) {
      handling401 = true
      message.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      router
        .push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
        .finally(() => {
          handling401 = false
        })
    }
    if (error.response?.status !== 200) {
      message.error(error.response?.data.message)
    }
    return Promise.reject(error)
  },
)

// 拦截器已解包 response.data，重新声明类型使 T 直接作为返回值
interface Request extends AxiosInstance {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
}

const request = instance as Request

export default request
