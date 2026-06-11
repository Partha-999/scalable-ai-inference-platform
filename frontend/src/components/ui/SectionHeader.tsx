export function SectionHeader({
    eyebrow,
    title,
    description,
}: {
    eyebrow: string
    title: string
    description: string
}) {
    return (
        <div className="mb-6">
            <p className="text-xs uppercase tracking-[0.35em] text-accent">{eyebrow}</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">{title}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{description}</p>
        </div>
    )
}
