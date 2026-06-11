export function LoadingState({ label = 'Loading' }: { label?: string }) {
    return (
        <div className="space-y-4 rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="h-5 w-32 animate-pulse rounded-full bg-white/10" />
            <div className="grid gap-3 sm:grid-cols-2">
                <div className="h-20 animate-pulse rounded-2xl bg-white/10" />
                <div className="h-20 animate-pulse rounded-2xl bg-white/10" />
            </div>
            <div className="h-3 w-48 animate-pulse rounded-full bg-white/10" />
            <p className="text-sm text-muted">{label}…</p>
        </div>
    )
}
