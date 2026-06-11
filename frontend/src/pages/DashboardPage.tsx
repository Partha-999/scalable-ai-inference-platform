import {
    Area,
    AreaChart,
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts'
import { Activity, Clock3, Database, Gauge, Layers3, RefreshCw, Server, TimerReset } from 'lucide-react'
import { Panel } from '../components/ui/Panel'
import { SectionHeader } from '../components/ui/SectionHeader'
import { LoadingState } from '../components/ui/LoadingState'
import { MetricCard } from '../components/ui/MetricCard'
import { useDashboardMetrics } from '../hooks/useDashboardMetrics'

const PIE_COLORS = ['#70E1FF', '#A78BFA', '#4ADE80', '#FB7185']

export function DashboardPage() {
    const { snapshot, chartData, loading, error, lastUpdated } = useDashboardMetrics()

    return (
        <div className="space-y-6">
            <SectionHeader
                eyebrow="Dashboard"
                title="Operational metrics"
                description="Live API health, request volume, cache efficiency, and model usage refresh every five seconds."
            />

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
                <MetricCard label="API latency" value={snapshot ? `${snapshot.apiLatencyMs.toFixed(2)} ms` : '—'} hint="Average request latency" />
                <MetricCard label="Request count" value={snapshot ? `${snapshot.requestCount.toFixed(0)}` : '—'} hint="Cumulative from /health/metrics" />
                <MetricCard label="Cache hits" value={snapshot ? `${snapshot.cacheHits.toFixed(0)}` : '—'} hint="Redis cache hit counter" />
                <MetricCard label="Model usage" value={snapshot ? `${snapshot.modelUsageByModel.reduce((sum, item) => sum + item.count, 0).toFixed(0)}` : '—'} hint="Inference counter across models" />
                <MetricCard label="Uptime" value={snapshot ? formatUptime(snapshot.uptimeSeconds) : '—'} hint="Derived from process metrics" />
                <MetricCard label="Health" value={snapshot?.live?.status ?? '—'} hint={snapshot?.ready?.status ?? '—'} />
            </div>

            <Panel className="p-5 sm:p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h2 className="text-xl font-semibold text-white">Live overview</h2>
                        <p className="mt-1 text-sm text-muted">Auto-refreshes every 5 seconds from the backend health endpoints.</p>
                    </div>
                    <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs uppercase tracking-[0.25em] text-muted">
                        <RefreshCw size={14} />
                        {lastUpdated ? `Updated ${new Date(lastUpdated).toLocaleTimeString()}` : 'Waiting for first refresh'}
                    </div>
                </div>

                {loading ? <LoadingState label="Loading dashboard" /> : null}
                {error ? <StateMessage text={error} tone="error" /> : null}

                {!loading && !error ? (
                    <div className="mt-6 grid gap-6 xl:grid-cols-2">
                        <ChartPanel title="API latency" subtitle="Rolling average latency from request histogram">
                            <ResponsiveContainer width="100%" height={280}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="latencyFill" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#70E1FF" stopOpacity={0.35} />
                                            <stop offset="95%" stopColor="#70E1FF" stopOpacity={0.02} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                                    <XAxis dataKey="time" tick={{ fill: '#90A0BC', fontSize: 12 }} />
                                    <YAxis tick={{ fill: '#90A0BC', fontSize: 12 }} width={40} />
                                    <Tooltip contentStyle={{ background: '#0b1220', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16 }} />
                                    <Area type="monotone" dataKey="apiLatencyMs" stroke="#70E1FF" fill="url(#latencyFill)" strokeWidth={2} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </ChartPanel>

                        <ChartPanel title="Request count vs cache hits" subtitle="Snapshot totals across polling windows">
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={chartData.slice(-6)}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                                    <XAxis dataKey="time" tick={{ fill: '#90A0BC', fontSize: 12 }} />
                                    <YAxis tick={{ fill: '#90A0BC', fontSize: 12 }} width={40} />
                                    <Tooltip contentStyle={{ background: '#0b1220', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16 }} />
                                    <Legend wrapperStyle={{ color: '#90A0BC' }} />
                                    <Bar dataKey="requestCount" fill="#A78BFA" radius={[8, 8, 0, 0]} />
                                    <Bar dataKey="cacheHits" fill="#4ADE80" radius={[8, 8, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartPanel>

                        <ChartPanel title="Model usage" subtitle="Top models from inference counters" className="xl:col-span-2">
                            <div className="grid gap-6 xl:grid-cols-2">
                                <ResponsiveContainer width="100%" height={280}>
                                    <BarChart data={snapshot?.modelUsageByModel ?? []} layout="vertical" margin={{ left: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                                        <XAxis type="number" tick={{ fill: '#90A0BC', fontSize: 12 }} />
                                        <YAxis type="category" dataKey="modelId" tick={{ fill: '#90A0BC', fontSize: 12 }} width={120} />
                                        <Tooltip contentStyle={{ background: '#0b1220', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16 }} />
                                        <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                                            {(snapshot?.modelUsageByModel ?? []).map((entry, index) => (
                                                <Cell key={entry.modelId} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>

                                <ResponsiveContainer width="100%" height={280}>
                                    <PieChart>
                                        <Tooltip contentStyle={{ background: '#0b1220', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16 }} />
                                        <Pie
                                            data={snapshot?.modelUsageByModel ?? []}
                                            dataKey="count"
                                            nameKey="modelId"
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={4}
                                        >
                                            {(snapshot?.modelUsageByModel ?? []).map((entry, index) => (
                                                <Cell key={entry.modelId} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                            ))}
                                        </Pie>
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </ChartPanel>
                    </div>
                ) : null}
            </Panel>

            <Panel className="p-5 sm:p-6">
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    <HealthPill icon={Activity} label="Live" value={snapshot?.live?.status ?? 'unknown'} />
                    <HealthPill icon={Server} label="Ready" value={snapshot?.ready?.status ?? 'unknown'} />
                    <HealthPill icon={Database} label="Cache hits" value={snapshot ? snapshot.cacheHits.toFixed(0) : '—'} />
                    <HealthPill icon={Clock3} label="Latency" value={snapshot ? `${snapshot.apiLatencyMs.toFixed(2)} ms` : '—'} />
                </div>
            </Panel>
        </div>
    )
}

function formatUptime(seconds: number): string {
    const total = Math.max(0, Math.floor(seconds))
    const hours = Math.floor(total / 3600)
    const minutes = Math.floor((total % 3600) / 60)
    const remainder = total % 60
    return `${hours}h ${minutes}m ${remainder}s`
}

function ChartPanel({
    title,
    subtitle,
    className = '',
    children,
}: {
    title: string
    subtitle: string
    className?: string
    children: React.ReactNode
}) {
    return (
        <div className={["rounded-3xl border border-white/10 bg-white/5 p-4 sm:p-5", className].join(' ')}>
            <div className="mb-4">
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="mt-1 text-sm text-muted">{subtitle}</p>
            </div>
            {children}
        </div>
    )
}

function HealthPill({
    icon: Icon,
    label,
    value,
}: {
    icon: typeof Activity
    label: string
    value: string
}) {
    return (
        <div className="rounded-3xl border border-white/10 bg-slate-950/30 p-4">
            <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10 text-accent">
                    <Icon size={18} />
                </div>
                <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-muted">{label}</p>
                    <p className="mt-1 text-base font-semibold text-white">{value}</p>
                </div>
            </div>
        </div>
    )
}

function StateMessage({ text, tone = 'default' }: { text: string; tone?: 'default' | 'error' }) {
    return (
        <div
            className={[
                'mt-6 rounded-2xl border px-4 py-3 text-sm',
                tone === 'error'
                    ? 'border-rose-500/30 bg-rose-500/10 text-rose-200'
                    : 'border-white/10 bg-white/5 text-muted',
            ].join(' ')}
        >
            {text}
        </div>
    )
}
