import { ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { navItems } from './Sidebar'

export function Topbar() {
    const { token } = useAuth()

    return (
        <header className="border-b border-white/10 bg-panel/60 backdrop-blur">
            <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
                <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-muted">FastAPI backend</p>
                    <h2 className="text-lg font-semibold text-white">127.0.0.1:8000 connected</h2>
                </div>
                <div className="flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-sm text-emerald-300">
                    <ShieldCheck size={16} />
                    {token ? 'Authenticated' : 'Unauthenticated'}
                </div>
            </div>
            <nav className="flex gap-2 overflow-x-auto border-t border-white/10 px-4 py-3 sm:px-6 xl:hidden">
                {navItems.map((item) => {
                    const Icon = item.icon
                    return (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                [
                                    'inline-flex items-center gap-2 whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition',
                                    isActive ? 'bg-white/10 text-white' : 'bg-white/5 text-muted hover:text-white',
                                ].join(' ')
                            }
                        >
                            <Icon size={16} />
                            {item.label}
                        </NavLink>
                    )
                })}
            </nav>
        </header>
    )
}
