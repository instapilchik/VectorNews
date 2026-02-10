import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token getter/setter to avoid circular imports with pinia stores
let tokenGetter: (() => string | null) | null = null
let logoutHandler: (() => void) | null = null

export function setAuthInterceptors(
  getToken: () => string | null,
  onUnauthorized: () => void,
) {
  tokenGetter = getToken
  logoutHandler = onUnauthorized
}

apiClient.interceptors.request.use((config) => {
  const token = tokenGetter?.()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logoutHandler?.()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default apiClient
