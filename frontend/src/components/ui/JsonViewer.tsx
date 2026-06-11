import { useState } from 'react'
import { ClipboardCopy, Code2 } from 'lucide-react'

export function JsonViewer({ data }: { data: unknown }) {
    const [copied, setCopied] = useState(false)
    const formatted = JSON.stringify(data, null, 2)

    async function copyJson() {
        await navigator.clipboard.writeText(formatted)
        setCopied(true)
        window.setTimeout(() => setCopied(false), 1500)
    }

    return (
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-slate-950/55">
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                <div className="flex items-center gap-2 text-sm font-medium text-white">
                    <Code2 size={16} className="text-accent" />
                    JSON response
                </div>
                <button
                    type="button"
                    onClick={copyJson}
                    className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-white/10"
                >
                    <ClipboardCopy size={14} />
                    {copied ? 'Copied' : 'Copy'}
                </button>
            </div>
            <pre className="max-h-[32rem] overflow-auto p-4 text-xs leading-6 text-slate-200">
                <code>{formatted}</code>
            </pre>
        </div>
    )
}
