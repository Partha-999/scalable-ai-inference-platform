import { useEffect, useMemo, useState } from 'react'
import { fetchModels } from '../lib/api'
import type { ModelInfo } from '../types/api'
import { Panel } from '../components/ui/Panel'
import { SectionHeader } from '../components/ui/SectionHeader'
import { MetricCard } from '../components/ui/MetricCard'
import { LoadingState } from '../components/ui/LoadingState'
import { useToast } from '../context/ToastContext'

export function ModelsPage() {
    const [models, setModels] = useState<ModelInfo[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [search, setSearch] = useState('')
    const { pushToast } = useToast()

    useEffect(() => {
        let active = true
        fetchModels()
            .then((items) => {
                if (active) {
                    setModels(items)
                    setError('')
                    pushToast({ title: 'Models loaded', description: `${items.length} models available`, variant: 'success' })
                }
            })
            .catch((err) => {
                if (active) {
                    const message = err instanceof Error ? err.message : 'Failed to load models'
                    setError(message)
                    pushToast({ title: 'Model registry error', description: message, variant: 'error' })
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

    const filteredModels = useMemo(() => {
        const query = search.trim().toLowerCase()
        if (!query) {
            return models
        }
        return models.filter((model) => {
            const blob = [model.model_id, model.description, model.endpoint_name, model.framework, model.version, model.modality, model.ab_group]
                .filter(Boolean)
                .join(' ')
                .toLowerCase()
            return blob.includes(query)
        })
    }, [models, search])

    const metrics = useMemo(() => {
        const enabled = filteredModels.filter((model) => model.enabled).length
        const vision = filteredModels.filter((model) => model.modality === 'vision').length
        const text = filteredModels.filter((model) => model.modality === 'text').length
        return [
            { label: 'Enabled', value: String(enabled) },
            { label: 'Text models', value: String(text) },
            { label: 'Vision models', value: String(vision) },
        ]
    }, [filteredModels])

    return (
        <div>
            <SectionHeader
                eyebrow="Registry"
                title="Model catalog"
                description="The backend registry drives model selection, A/B routing, and the live inference forms."
            />

            <div className="grid gap-4 md:grid-cols-3">
                {metrics.map((metric) => (
                    <MetricCard key={metric.label} label={metric.label} value={metric.value} />
                ))}
            </div>

            <Panel className="mt-6 p-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                        <p className="text-sm text-muted">Search and inspect registry entries across text and vision modalities.</p>
                    </div>
                    <label className="w-full max-w-md space-y-2 md:w-96">
                        <span className="text-xs uppercase tracking-[0.25em] text-muted">Search models</span>
                        <input
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                            placeholder="Search by model, framework, version, or A/B group"
                            className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
                        />
                    </label>
                </div>

                {loading ? <LoadingState label="Loading model registry" /> : null}
                {error ? <StateMessage text={error} tone="error" /> : null}
                {!loading && !error ? (
                    <div className="grid gap-4 lg:grid-cols-2">
                        {filteredModels.length ? filteredModels.map((model) => (
                            <article key={model.model_id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">{model.model_id}</h3>
                                        <p className="mt-1 text-sm text-muted">{model.description || model.endpoint_name || 'Managed in registry'}</p>
                                    </div>
                                    <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
                                        {model.modality}
                                    </span>
                                </div>
                                <div className="mt-4 grid gap-2 text-sm text-muted sm:grid-cols-2">
                                    <Meta label="Framework" value={model.framework} />
                                    <Meta label="Version" value={model.version} />
                                    <Meta label="A/B Group" value={model.ab_group} />
                                    <Meta label="Enabled" value={String(model.enabled)} />
                                </div>
                            </article>
                        )) : (
                            <StateMessage text="No models matched your search." />
                        )}
                    </div>
                ) : null}
            </Panel>
        </div>
    )
}

function Meta({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.25em] text-muted">{label}</p>
            <p className="mt-1 text-white">{value}</p>
        </div>
    )
}

function StateMessage({ text, tone = 'default' }: { text: string; tone?: 'default' | 'error' }) {
    return (
        <div
            className={[
                'rounded-2xl border px-4 py-3 text-sm',
                tone === 'error'
                    ? 'border-rose-500/30 bg-rose-500/10 text-rose-200'
                    : 'border-white/10 bg-white/5 text-muted',
            ].join(' ')}
        >
            {text}
        </div>
    )
}
