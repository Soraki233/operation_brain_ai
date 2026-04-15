import request from '@/utils/request'
import type { HTTPResponse } from './core'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  phone: string
  verificationCode: string
  password: string
  confirmPassword: string
}

export interface AuthResponse {
  token: string
  username: string
}

export function login(data: LoginParams) {
  return request.post<AuthResponse>('/users/login', data)
}

export function register(data: RegisterParams) {
  return request.post<AuthResponse>('/users/register', data)
}



export function sendVerificationCode(phone: string) {
  return request.get<HTTPResponse>('/users/send-verification-code', { params: { phone } })
}
