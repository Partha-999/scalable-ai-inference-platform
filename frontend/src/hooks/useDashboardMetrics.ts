import { useEffect, useMemo, useState } from 'react'
import { fetchHealthLive, fetchHealthMetrics, fetchHealthReady } from '../lib/api'
import { parseDashboardSnapshot, type DashboardMetricPoint, type DashboardSnapshot } from '../lib/health'

const REFRESH_INTERVAL_MS = 5000
const MAX_POINTS = 12

export function useDashboardMetrics() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null)
  const [history, setHistory] = useState<DashboardMetricPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<number | null>(null)

  useEffect(() => {
    let active = true

    async function refresh() {
      try {
        const [live, ready, metricsText] = await Promise.all([
          fetchHealthLive(),
          fetchHealthReady(),
          fetchHealthMetrics(),
        ])
        if (!active) {
          return
        }

        const parsed = parseDashboardSnapshot({ live, ready, metricsText })
        setSnapshot(parsed)
        setHistory((current) => [
          ...current,
          {
            timestamp: Date.now(),
            apiLatencyMs: parsed.apiLatencyMs,
            requestCount: parsed.requestCount,
            cacheHits: parsed.cacheHits,
            modelUsage: parsed.modelUsageByModel.reduce((sum, item) => sum + item.count, 0),
            uptimeSeconds: parsed.uptimeSeconds,
          },
        ].slice(-MAX_POINTS))
        setLastUpdated(Date.now())
        setError('')
        setLoading(false)
      } catch (err) {
        if (!active) {
          return
        }
        setError(err instanceof Error ? err.message : 'Failed to load dashboard metrics')
        setLoading(false)
      }
    }

    refresh()
    const timer = window.setInterval(refresh, REFRESH_INTERVAL_MS)

    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [])

  const chartData = useMemo(
    () =>
      history.map((point) => ({
        time: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        apiLatencyMs: Number(point.apiLatencyMs.toFixed(2)),
        requestCount: point.requestCount,
        cacheHits: point.cacheHits,
        modelUsage: point.modelUsage,
        uptimeSeconds: Number(point.uptimeSeconds.toFixed(0)),
      })),
    [history],
  )

  return { snapshot, history, chartData, loading, error, lastUpdated }
}
