import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { ModelsPage } from './pages/ModelsPage'
import { TextInferencePage } from './pages/TextInferencePage'
import { ImageInferencePage } from './pages/ImageInferencePage'
import { CertificationPage } from './pages/CertificationPage'

function Protected({ children }: { children: ReactNode }) {
    const { token } = useAuth()
    return token ? <>{children}</> : <Navigate to="/login" replace />
}

function AppRoutes() {
    const { token } = useAuth()

    return (
        <Routes>
            <Route path="/login" element={token ? <Navigate to="/models" replace /> : <LoginPage />} />
            <Route
                path="/"
                element={
                    <Protected>
                        <AppShell />
                    </Protected>
                }
            >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="models" element={<ModelsPage />} />
                <Route path="text" element={<TextInferencePage />} />
                <Route path="image" element={<ImageInferencePage />} />
                <Route path="certification" element={<CertificationPage />} />
            </Route>
            <Route path="*" element={<Navigate to={token ? '/dashboard' : '/login'} replace />} />
        </Routes>
    )
}

export default function App() {
    return (
        <AuthProvider>
            <ToastProvider>
                <AppRoutes />
            </ToastProvider>
        </AuthProvider>
    )
}
