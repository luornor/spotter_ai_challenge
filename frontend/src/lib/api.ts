export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'


export async function api(path: string, opts: RequestInit = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
        ...opts,
    })
    if (!res.ok) {
        const text = await res.text()
        throw new Error(text || 'API error')
    }
    return res.json()
}