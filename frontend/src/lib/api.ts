import axios from 'axios'
import type { ModelInfo, PredictionResult, TokenResponse } from '../types/api'
import { getToken } from './storage'
import type { HealthResponse } from './health'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL,
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface LoginPayload {
  subject: string
  tenant_id: string
  scopes?: string[]
}

export interface TextInferencePayload {
  text?: string
  question?: string
  context?: string
  model_id?: string
  use_ab_test?: boolean
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/api/v1/auth/token', payload)
  return data
}

export async function fetchModels(): Promise<ModelInfo[]> {
  const { data } = await api.get<{ models: ModelInfo[] }>('/api/v1/inference/models')
  return data.models
}

export async function fetchHealthLive(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/api/v1/health/live')
  return data
}

export async function fetchHealthReady(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/api/v1/health/ready')
  return data
}

export async function fetchHealthMetrics(): Promise<string> {
  const { data } = await api.get<string>('/api/v1/health/metrics', { responseType: 'text' })
  return data
}

export async function inferText(payload: TextInferencePayload, tenantId: string): Promise<PredictionResult> {
  const { data } = await api.post<PredictionResult>('/api/v1/inference/text', payload, {
    headers: { 'X-Tenant-ID': tenantId },
  })
  return data
}

export async function inferImage(file: File, tenantId: string, modelId?: string): Promise<PredictionResult> {
  const formData = new FormData()
  formData.append('file', file)
  if (modelId) {
    formData.append('model_id', modelId)
  }

  const { data } = await api.post<PredictionResult>('/api/v1/inference/vision/upload', formData, {
    headers: {
      'X-Tenant-ID': tenantId,
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function fetchValidationReport(): Promise<any> {
  const { data } = await api.get('/api/v1/inference/validation/report')
  return data
}
