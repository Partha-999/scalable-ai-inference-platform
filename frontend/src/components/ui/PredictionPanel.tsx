import { useState } from 'react'
import { Code2, Layers3 } from 'lucide-react'
import type { PredictionResult } from '../../types/api'
import { JsonViewer } from './JsonViewer'

export function PredictionPanel({ result }: { result: PredictionResult | null }) {
    const [tab, setTab] = useState<'summary' | 'json'>('summary')

    if (!result) {
        return (
            <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-muted">
                Run an inference to see predictions, confidence, and latency.
            </div>
        )
    }

    return (
        <div className="rounded-3xl border border-white/10 bg-panelAlt/80 p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="inline-flex rounded-full border border-white/10 bg-white/5 p-1">
                    <button
                        type="button"
                        onClick={() => setTab('summary')}
                        className={[
                            'inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition',
                            tab === 'summary' ? 'bg-white/10 text-white' : 'text-muted hover:text-white',
                        ].join(' ')}
                    >
                        <Layers3 size={16} />
                        Summary
                    </button>
                    <button
                        type="button"
                        onClick={() => setTab('json')}
                        className={[
                            'inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition',
                            tab === 'json' ? 'bg-white/10 text-white' : 'text-muted hover:text-white',
                        ].join(' ')}
                    >
                        <Code2 size={16} />
                        JSON
                    </button>
                </div>
                <p className="text-xs uppercase tracking-[0.25em] text-muted">Request ID: {result.request_id}</p>
            </div>

            {tab === 'summary' ? (
                <>
                    <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        <Stat label="Label" value={result.label} />
                        <Stat label="Confidence" value={`${(result.confidence * 100).toFixed(1)}%`} />
                        <Stat label="Latency" value={`${result.latency_ms.toFixed(1)} ms`} />
                        <Stat label="Cache" value={result.cached ? 'HIT' : 'MISS'} />
                    </div>
                    {result.predictions[0] && 'text' in result.predictions[0] ? (
                        <div className="mt-6 space-y-4">
                            <div>
                                <p className="text-xs uppercase tracking-[0.25em] text-muted mb-2">📄 Extracted Text</p>
                                <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4 text-sm font-medium text-white leading-relaxed whitespace-pre-wrap">
                                    {result.predictions[0].text}
                                </div>
                            </div>
                            {result.predictions[0].words && result.predictions[0].words.length > 0 && (
                                <div>
                                    <p className="text-xs uppercase tracking-[0.25em] text-muted mb-2">📍 Word-level Detections</p>
                                    <div className="overflow-hidden rounded-2xl border border-white/10">
                                        <table className="min-w-full divide-y divide-white/10 text-left text-sm">
                                            <thead className="bg-white/5 text-muted">
                                                <tr>
                                                    <th className="px-4 py-3 font-medium">Word</th>
                                                    <th className="px-4 py-3 font-medium">Bounding Box (x1, y1, x2, y2)</th>
                                                    <th className="px-4 py-3 font-medium">Confidence</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-white/10 bg-slate-950/20">
                                                {result.predictions[0].words.map((w: any, idx: number) => (
                                                    <tr key={idx}>
                                                        <td className="px-4 py-3 text-white">{w.text}</td>
                                                        <td className="px-4 py-3 text-muted font-mono">[{w.bbox?.join(', ')}]</td>
                                                        <td className="px-4 py-3 text-accent font-semibold">{Math.round((w.confidence || 0.95) * 100)}%</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="mt-6 overflow-hidden rounded-2xl border border-white/10">
                            <table className="min-w-full divide-y divide-white/10 text-left text-sm">
                                <thead className="bg-white/5 text-muted">
                                    <tr>
                                        <th className="px-4 py-3 font-medium">Prediction</th>
                                        <th className="px-4 py-3 font-medium">Score</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/10 bg-slate-950/20">
                                    {result.predictions.slice(0, 5).map((prediction, index) => (
                                        <tr key={`${prediction.label}-${index}`}>
                                            <td className="px-4 py-3 text-white">{prediction.label}</td>
                                            <td className="px-4 py-3 text-muted">{Number(prediction.score).toFixed(4)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            ) : (
                <div className="mt-5">
                    <JsonViewer data={result} />
                </div>
            )}
        </div>
    )
}

function Stat({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-muted">{label}</p>
            <p className="mt-2 text-lg font-semibold text-white">{value}</p>
        </div>
    )
}
