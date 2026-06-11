export type Modality = 'vision' | 'text'

export interface ModelInfo {
  model_id: string
  modality: Modality
  framework: string
  version: string
  enabled: boolean
  ab_group: string
  endpoint_name?: string | null
  description?: string | null
}

export interface PredictionItem {
  label: string
  score: number
  [key: string]: unknown
}

export interface PredictionResult {
  request_id: string
  tenant_id: string
  model_id: string
  modality: Modality
  label: string
  confidence: number
  predictions: PredictionItem[]
  cached: boolean
  latency_ms: number
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}
