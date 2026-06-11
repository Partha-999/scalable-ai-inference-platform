import type { FormEvent } from 'react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Panel } from '../components/ui/Panel'
import { useToast } from '../context/ToastContext'

export function LoginPage() {
    const navigate = useNavigate()
    const { login } = useAuth()
    const { pushToast } = useToast()
    const [subject, setSubject] = useState('demo-user')
    const [tenantId, setTenantId] = useState('tenant-acme')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setLoading(true)
        setError('')
        try {
            await login(subject.trim(), tenantId.trim())
            pushToast({ title: 'Signed in', description: `Tenant ${tenantId.trim()} authenticated`, variant: 'success' })
            navigate('/models', { replace: true })
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Login failed'
            setError(message)
            pushToast({ title: 'Login failed', description: message, variant: 'error' })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-mesh px-4 py-10 text-text sm:px-6 lg:px-8">
            <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-8 lg:grid-cols-[1.05fr_0.95fr]">
                <div className="space-y-6">
                    <p className="text-xs uppercase tracking-[0.35em] text-accent">AI Inference Studio</p>
                    <h1 className="max-w-2xl text-5xl font-semibold leading-tight text-white">
                        Ship vision and text inference workflows from one production-ready console.
                    </h1>
                    <p className="max-w-xl text-base leading-7 text-muted">
                        Multi-tenant JWT login, model registry visibility, real-time inference, and upload-based vision analytics backed by your FastAPI service.
                    </p>
                    <div className="grid gap-4 sm:grid-cols-3">
                        <Feature label="JWT" value="Local storage" />
                        <Feature label="Models" value="Live registry" />
                        <Feature label="Latency" value="Inline metrics" />
                    </div>
                </div>

                <Panel className="p-8">
                    <h2 className="text-2xl font-semibold text-white">Sign in</h2>
                    <p className="mt-2 text-sm text-muted">Use the backend JWT endpoint to mint a token for your tenant.</p>

                    <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
                        <Field label="Subject" value={subject} onChange={setSubject} placeholder="demo-user" />
                        <Field label="Tenant ID" value={tenantId} onChange={setTenantId} placeholder="tenant-acme" />
                        {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-2xl bg-gradient-to-r from-accent to-accent2 px-4 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
                        >
                            {loading ? 'Signing in…' : 'Login'}
                        </button>
                    </form>
                </Panel>
            </div>
        </div>
    )
}

function Field({
    label,
    value,
    onChange,
    placeholder,
}: {
    label: string
    value: string
    onChange: (value: string) => void
    placeholder: string
}) {
    return (
        <label className="block space-y-2">
            <span className="text-sm font-medium text-white">{label}</span>
            <input
                value={value}
                onChange={(event) => onChange(event.target.value)}
                placeholder={placeholder}
                className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
            />
        </label>
    )
}

function Feature({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-3xl border border-white/10 bg-white/5 p-4 backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">{label}</p>
            <p className="mt-3 text-lg font-semibold text-white">{value}</p>
        </div>
    )
}
