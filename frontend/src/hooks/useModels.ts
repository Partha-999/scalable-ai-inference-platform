import { useEffect, useState } from 'react'
import { fetchModels } from '../lib/api'
import type { ModelInfo } from '../types/api'

export function useModels() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    fetchModels()
      .then((items) => {
        if (active) {
          setModels(items)
          setError('')
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Failed to load models')
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  return { models, loading, error }
}
