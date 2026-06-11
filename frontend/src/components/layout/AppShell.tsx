import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export function AppShell() {
    return (
        <div className="min-h-screen bg-mesh text-text">
            <div className="flex min-h-screen flex-col xl:flex-row">
                <Sidebar />
                <div className="flex min-w-0 flex-1 flex-col">
                    <Topbar />
                    <main className="flex-1 px-4 pb-8 pt-4 sm:px-6 lg:px-8">
                        <div className="mx-auto w-full max-w-7xl">
                            <Outlet />
                        </div>
                    </main>
                </div>
            </div>
        </div>
    )
}
