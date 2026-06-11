import type { DragEvent, FormEvent } from 'react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { FileImage, UploadCloud, X } from 'lucide-react'
import { inferImage } from '../lib/api'
import type { PredictionResult } from '../types/api'
import { Panel } from '../components/ui/Panel'
import { SectionHeader } from '../components/ui/SectionHeader'
import { PredictionPanel } from '../components/ui/PredictionPanel'
import { LoadingState } from '../components/ui/LoadingState'
import { useModels } from '../hooks/useModels'
import { useToast } from '../context/ToastContext'

export function ImageInferencePage() {
    const { models, loading: modelsLoading, error: modelsError } = useModels()
    const { pushToast } = useToast()
    const [tenantId, setTenantId] = useState('tenant-acme')
    const [modelId, setModelId] = useState('')
    const [file, setFile] = useState<File | null>(null)
    const [previewUrl, setPreviewUrl] = useState('')
    const [result, setResult] = useState<PredictionResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [dragActive, setDragActive] = useState(false)
    const fileInputRef = useRef<HTMLInputElement | null>(null)

    const visionModels = useMemo(() => models.filter((model) => model.modality === 'vision'), [models])

    useEffect(() => {
        if (!file) {
            setPreviewUrl('')
            return
        }
        const objectUrl = URL.createObjectURL(file)
        setPreviewUrl(objectUrl)
        return () => URL.revokeObjectURL(objectUrl)
    }, [file])

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        if (!file) {
            setError('Please choose a JPG or PNG file.')
            pushToast({ title: 'Image required', description: 'Choose a JPG or PNG file before submitting.', variant: 'info' })
            return
        }
        setLoading(true)
        setError('')
        try {
            const response = await inferImage(file, tenantId, modelId || undefined)
            setResult(response)
            pushToast({
                title: 'Image analyzed',
                description: `${response.label} • ${(response.confidence * 100).toFixed(1)}% confidence`,
                variant: 'success',
            })
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Upload inference failed'
            setError(message)
            pushToast({ title: 'Image inference failed', description: message, variant: 'error' })
        } finally {
            setLoading(false)
        }
    }

    function setSelectedFile(nextFile: File | null) {
        setFile(nextFile)
        if (nextFile) {
            pushToast({ title: 'File selected', description: nextFile.name, variant: 'info' })
        }
    }

    function handleDrop(event: DragEvent<HTMLDivElement>) {
        event.preventDefault()
        setDragActive(false)
        const dropped = event.dataTransfer.files?.[0]
        if (dropped) {
            setSelectedFile(dropped)
        }
    }

    return (
        <div className="space-y-6">
            <SectionHeader
                eyebrow="Vision"
                title="Image upload inference"
                description="Upload JPG or PNG files and inspect top predictions with confidence and latency metrics."
            />

            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <Panel className="p-5 sm:p-6">
                    <form className="space-y-5" onSubmit={handleSubmit}>
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                                <p className="text-sm text-muted">Upload-based inference with drag and drop, inline preview, and live result feedback.</p>
                            </div>
                            <div className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs uppercase tracking-[0.25em] text-muted">
                                {visionModels.length} vision models
                            </div>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2">
                            <Field label="Tenant ID" value={tenantId} onChange={setTenantId} />
                            <label className="space-y-2">
                                <span className="text-sm font-medium text-white">Model</span>
                                <select
                                    value={modelId}
                                    onChange={(event) => setModelId(event.target.value)}
                                    className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none focus:border-accent/50"
                                >
                                    <option value="">Auto from registry</option>
                                    {visionModels.map((model) => (
                                        <option key={model.model_id} value={model.model_id}>
                                            {model.model_id}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        </div>

                        {modelsLoading ? <LoadingState label="Loading available vision models" /> : null}
                        {modelsError ? <ErrorBanner text={modelsError} /> : null}

                        <div
                            onDragEnter={() => setDragActive(true)}
                            onDragOver={(event) => {
                                event.preventDefault()
                                setDragActive(true)
                            }}
                            onDragLeave={() => setDragActive(false)}
                            onDrop={handleDrop}
                            className={[
                                'rounded-3xl border border-dashed p-6 transition',
                                dragActive ? 'border-accent bg-accent/10' : 'border-white/10 bg-white/5',
                            ].join(' ')}
                        >
                            <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
                                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-accent">
                                    <UploadCloud size={24} />
                                </div>
                                <div className="flex-1">
                                    <p className="text-base font-medium text-white">Drop a JPG or PNG here</p>
                                    <p className="mt-1 text-sm text-muted">Or browse from your device and run vision inference immediately.</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/10"
                                >
                                    Browse files
                                </button>
                            </div>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/png,image/jpeg"
                                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                                className="sr-only"
                            />
                            {file ? (
                                <div className="mt-4 flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3 text-sm text-white">
                                    <div className="flex min-w-0 items-center gap-2">
                                        <FileImage size={16} className="shrink-0 text-accent" />
                                        <span className="truncate">{file.name}</span>
                                    </div>
                                    <button type="button" onClick={() => setSelectedFile(null)} className="text-muted transition hover:text-white">
                                        <X size={16} />
                                    </button>
                                </div>
                            ) : null}
                        </div>

                        {previewUrl ? (
                            <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/5">
                                <img src={previewUrl} alt="Preview" className="max-h-96 w-full object-cover" />
                            </div>
                        ) : null}

                        {error ? <ErrorBanner text={error} /> : null}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-2xl bg-gradient-to-r from-accent to-accent2 px-5 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70 sm:w-auto"
                        >
                            {loading ? 'Running inference…' : 'Analyze image'}
                        </button>
                    </form>
                </Panel>

                <PredictionPanel result={result} />
            </div>
        </div>
    )
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
    return (
        <label className="block space-y-2">
            <span className="text-sm font-medium text-white">{label}</span>
            <input
                value={value}
                onChange={(event) => onChange(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
            />
        </label>
    )
}

function ErrorBanner({ text }: { text: string }) {
    return <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{text}</div>
}
