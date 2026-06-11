import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { login as apiLogin } from '../lib/api'
import { clearToken, getToken, setToken } from '../lib/storage'

interface AuthContextValue {
    token: string | null
    login: (subject: string, tenantId: string, scopes?: string[]) => Promise<void>
    logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setTokenState] = useState<string | null>(getToken())

    useEffect(() => {
        setTokenState(getToken())
    }, [])

    const value = useMemo<AuthContextValue>(
        () => ({
            token,
            login: async (subject, tenantId, scopes = []) => {
                const result = await apiLogin({ subject, tenant_id: tenantId, scopes })
                setToken(result.access_token)
                setTokenState(result.access_token)
            },
            logout: () => {
                clearToken()
                setTokenState(null)
            },
        }),
        [token],
    )

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider')
    }
    return context
}
