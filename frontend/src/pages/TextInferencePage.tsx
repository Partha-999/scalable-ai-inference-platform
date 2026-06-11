import type { FormEvent, ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { inferText } from '../lib/api'
import type { PredictionResult } from '../types/api'
import { Panel } from '../components/ui/Panel'
import { SectionHeader } from '../components/ui/SectionHeader'
import { PredictionPanel } from '../components/ui/PredictionPanel'
import { LoadingState } from '../components/ui/LoadingState'
import { useModels } from '../hooks/useModels'
import { useToast } from '../context/ToastContext'

export function TextInferencePage() {
    const { models, loading: modelsLoading, error: modelsError } = useModels()
    const { pushToast } = useToast()
    const [mode, setMode] = useState<'sentiment' | 'qa'>('sentiment')
    const [text, setText] = useState('I love the way this platform handles inference workloads.')
    const [question, setQuestion] = useState('What is the capital of France?')
    const [context, setContext] = useState('Paris is the capital and most populous city of France.')
    const [modelId, setModelId] = useState('')
    const [useAbTest, setUseAbTest] = useState(true)
    const [tenantId, setTenantId] = useState('tenant-acme')
    const [search, setSearch] = useState('')
    const [result, setResult] = useState<PredictionResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const textModels = useMemo(() => {
        const query = search.trim().toLowerCase()
        return models.filter((model) => {
            if (model.modality !== 'text') {
                return false
            }
            if (!query) {
                return true
            }
            return [model.model_id, model.framework, model.version, model.ab_group, model.description, model.endpoint_name]
                .filter(Boolean)
                .join(' ')
                .toLowerCase()
                .includes(query)
        })
    }, [models, search])

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setLoading(true)
        setError('')
        try {
            const payload =
                mode === 'qa'
                    ? { question, context, model_id: modelId || undefined, use_ab_test: useAbTest }
                    : { text, model_id: modelId || undefined, use_ab_test: useAbTest }
            const response = await inferText(payload, tenantId)
            setResult(response)
            pushToast({
                title: 'Inference complete',
                description: `${response.label} • ${(response.confidence * 100).toFixed(1)}% confidence`,
                variant: 'success',
            })
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Inference failed'
            setError(message)
            pushToast({ title: 'Text inference failed', description: message, variant: 'error' })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <SectionHeader
                eyebrow="Text"
                title="Text inference"
                description="Switch between sentiment-style text and question answering without changing the backend contract."
            />

            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <Panel className="p-5 sm:p-6">
                    <div className="flex flex-wrap gap-3">
                        <Tab active={mode === 'sentiment'} onClick={() => setMode('sentiment')}>
                            Sentiment / Classification
                        </Tab>
                        <Tab active={mode === 'qa'} onClick={() => setMode('qa')}>
                            Question Answering
                        </Tab>
                    </div>

                    <div className="mt-5 grid gap-4 md:grid-cols-[1fr_14rem]">
                        <label className="space-y-2">
                            <span className="text-xs uppercase tracking-[0.25em] text-muted">Search models</span>
                            <input
                                value={search}
                                onChange={(event) => setSearch(event.target.value)}
                                placeholder="Search registry"
                                className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
                            />
                        </label>
                        <label className="space-y-2">
                            <span className="text-xs uppercase tracking-[0.25em] text-muted">Tenant</span>
                            <input
                                value={tenantId}
                                onChange={(event) => setTenantId(event.target.value)}
                                className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
                            />
                        </label>
                    </div>

                    <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
                        <div className="grid gap-4 sm:grid-cols-2">
                            <label className="space-y-2">
                                <span className="text-sm font-medium text-white">Model</span>
                                <select
                                    value={modelId}
                                    onChange={(event) => setModelId(event.target.value)}
                                    className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none focus:border-accent/50"
                                >
                                    <option value="">Auto from registry</option>
                                    {textModels.map((model) => (
                                        <option key={model.model_id} value={model.model_id}>
                                            {model.model_id}
                                        </option>
                                    ))}
                                </select>
                            </label>
                            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-muted">
                                {textModels.length} matching text models
                            </div>
                        </div>

                        {modelsLoading ? <LoadingState label="Loading available text models" /> : null}
                        {modelsError ? <ErrorBanner text={modelsError} /> : null}

                        <label className="flex items-center gap-3 text-sm text-muted">
                            <input
                                checked={useAbTest}
                                onChange={(event) => setUseAbTest(event.target.checked)}
                                type="checkbox"
                            />
                            Enable A/B routing
                        </label>

                        {mode === 'qa' ? (
                            <>
                                <Field label="Question" value={question} onChange={setQuestion} />
                                <Field label="Context" value={context} onChange={setContext} multiline />
                            </>
                        ) : (
                            <Field label="Text" value={text} onChange={setText} multiline />
                        )}

                        {error ? <ErrorBanner text={error} /> : null}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-2xl bg-gradient-to-r from-accent to-accent2 px-5 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70 sm:w-auto"
                        >
                            {loading ? 'Running inference…' : 'Infer'}
                        </button>
                    </form>
                </Panel>

                <PredictionPanel result={result} />
            </div>
        </div>
    )
}

function Tab({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={[
                'rounded-full px-4 py-2 text-sm font-medium transition',
                active ? 'bg-white/10 text-white ring-1 ring-white/10' : 'bg-white/5 text-muted hover:text-white',
            ].join(' ')}
        >
            {children}
        </button>
    )
}

function Field({
    label,
    value,
    onChange,
    multiline = false,
}: {
    label: string
    value: string
    onChange: (value: string) => void
    multiline?: boolean
}) {
    const className =
        'w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-accent/50 focus:ring-2 focus:ring-accent/20'
    return (
        <label className="block space-y-2">
            <span className="text-sm font-medium text-white">{label}</span>
            {multiline ? (
                <textarea rows={5} value={value} onChange={(event) => onChange(event.target.value)} className={className} />
            ) : (
                <input value={value} onChange={(event) => onChange(event.target.value)} className={className} />
            )}
        </label>
    )
}

function ErrorBanner({ text }: { text: string }) {
    return <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{text}</div>
}
