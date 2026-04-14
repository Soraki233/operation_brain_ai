import request from '@/utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  confirmPassword: string
  email: string
}

export interface AuthResponse {
  token: string
  username: string
}

export function login(data: LoginParams) {
  return request.post<AuthResponse>('/auth/login', data)
}

export function register(data: RegisterParams) {
  return request.post<AuthResponse>('/auth/register', data)
}
