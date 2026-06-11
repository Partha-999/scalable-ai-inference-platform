export function MetricCard({
    label,
    value,
    hint,
}: {
    label: string
    value: string
    hint?: string
}) {
    return (
        <div className="rounded-3xl border border-white/10 bg-panelAlt/70 p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-muted">{label}</p>
            <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
            {hint ? <p className="mt-2 text-sm text-muted">{hint}</p> : null}
        </div>
    )
}
