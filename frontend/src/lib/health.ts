export interface HealthResponse {
  status: string
  timestamp: string
  service: string
}

export interface DashboardMetricPoint {
  timestamp: number
  apiLatencyMs: number
  requestCount: number
  cacheHits: number
  modelUsage: number
  uptimeSeconds: number
}

export interface DashboardSnapshot {
  live: HealthResponse | null
  ready: HealthResponse | null
  metricsText: string
  apiLatencyMs: number
  requestCount: number
  cacheHits: number
  uptimeSeconds: number
  requestByRoute: Array<{ route: string; count: number }>
  modelUsageByModel: Array<{ modelId: string; count: number }>
}

function extractMetricSeries(text: string, metricName: string): Array<{ labels: Record<string, string>; value: number }> {
  const lines = text.split('\n').filter((line) => line.startsWith(metricName))
  return lines.flatMap((line) => {
    const match = line.match(/^(?<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(\{(?<labels>[^}]*)\})?\s+(?<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)/)
    if (!match?.groups) {
      return []
    }
    const labels: Record<string, string> = {}
    const rawLabels = match.groups.labels ?? ''
    if (rawLabels) {
      for (const pair of rawLabels.split(',')) {
        const [key, rawValue] = pair.split('=')
        if (key && rawValue) {
          labels[key.trim()] = rawValue.trim().replace(/^"|"$/g, '')
        }
      }
    }
    return [{ labels, value: Number(match.groups.value) }]
  })
}

function getMetricValue(text: string, metricName: string): number {
  const series = extractMetricSeries(text, metricName)
  return series.reduce((sum, item) => sum + item.value, 0)
}

function getHistogramAverage(text: string, baseName: string): number {
  const sum = getMetricValue(text, `${baseName}_sum`)
  const count = getMetricValue(text, `${baseName}_count`)
  return count > 0 ? (sum / count) * 1000 : 0
}

function getUptimeSeconds(text: string): number {
  const startSeries = extractMetricSeries(text, 'process_start_time_seconds')
  if (!startSeries.length) {
    return 0
  }
  const startTime = startSeries[0].value * 1000
  return Math.max(0, (Date.now() - startTime) / 1000)
}

function sumGroupedByLabel(
  text: string,
  metricName: string,
  labelName: string,
): Array<{ key: string; value: number }> {
  const series = extractMetricSeries(text, metricName)
  const totals = new Map<string, number>()
  for (const point of series) {
    const key = point.labels[labelName] || 'unknown'
    totals.set(key, (totals.get(key) ?? 0) + point.value)
  }
  return Array.from(totals.entries())
    .map(([key, value]) => ({ key, value }))
    .sort((left, right) => right.value - left.value)
}

function deriveRequestByRoute(text: string): Array<{ route: string; count: number }> {
  return sumGroupedByLabel(text, 'ai_platform_requests_total', 'route').map((item) => ({
    route: item.key,
    count: item.value,
  }))
}

function deriveModelUsage(text: string): Array<{ modelId: string; count: number }> {
  return sumGroupedByLabel(text, 'ai_platform_inference_latency_seconds_count', 'model_id').map((item) => ({
    modelId: item.key,
    count: item.value,
  }))
}

export function parseDashboardSnapshot(params: {
  live: HealthResponse | null
  ready: HealthResponse | null
  metricsText: string
}): DashboardSnapshot {
  const { live, ready, metricsText } = params
  const apiLatencyMs = getHistogramAverage(metricsText, 'ai_platform_request_latency_seconds')
  const requestCount = getMetricValue(metricsText, 'ai_platform_requests_total')
  const cacheHits = getMetricValue(metricsText, 'ai_platform_cache_hits_total')
  const uptimeSeconds = getUptimeSeconds(metricsText)

  return {
    live,
    ready,
    metricsText,
    apiLatencyMs,
    requestCount,
    cacheHits,
    uptimeSeconds,
    requestByRoute: deriveRequestByRoute(metricsText),
    modelUsageByModel: deriveModelUsage(metricsText),
  }
}
