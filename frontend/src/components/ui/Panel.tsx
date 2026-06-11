import type { ReactNode } from 'react'

export function Panel({ children, className = '' }: { children: ReactNode; className?: string }) {
    return <div className={`rounded-3xl border border-white/10 bg-panel/80 shadow-glow backdrop-blur ${className}`}>{children}</div>
}
