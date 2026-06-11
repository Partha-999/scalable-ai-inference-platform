import { BarChart3, Bot, FileImage, Gauge, Layers3, LogOut, ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: Gauge },
    { to: '/models', label: 'Models', icon: Layers3 },
    { to: '/text', label: 'Text Inference', icon: Bot },
    { to: '/image', label: 'Image Upload', icon: FileImage },
    { to: '/certification', label: 'Certification', icon: ShieldCheck },
]

export function Sidebar() {
    const { logout } = useAuth()

    return (
        <aside className="hidden w-72 border-r border-white/10 bg-panel/95 backdrop-blur xl:flex xl:flex-col">
            <div className="border-b border-white/10 px-6 py-6">
                <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-accent2 text-slate-950 shadow-glow">
                        <BarChart3 size={20} />
                    </div>
                    <div>
                        <p className="text-sm uppercase tracking-[0.25em] text-muted">AI Platform</p>
                        <h1 className="text-lg font-semibold text-white">Inference Studio</h1>
                    </div>
                </div>
            </div>
            <nav className="flex-1 space-y-2 px-4 py-6">
                {navItems.map((item) => {
                    const Icon = item.icon
                    return (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                [
                                    'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition',
                                    isActive
                                        ? 'bg-white/10 text-white ring-1 ring-white/10'
                                        : 'text-muted hover:bg-white/5 hover:text-white',
                                ].join(' ')
                            }
                        >
                            <Icon size={18} />
                            {item.label}
                        </NavLink>
                    )
                })}
            </nav>
            <div className="border-t border-white/10 p-4">
                <button
                    onClick={logout}
                    className="flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white transition hover:bg-white/10"
                >
                    <LogOut size={16} />
                    Logout
                </button>
            </div>
        </aside>
    )
}
