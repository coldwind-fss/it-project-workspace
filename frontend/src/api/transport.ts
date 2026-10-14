import { SESSION_STORAGE_KEY } from '@/api/session-storage'
export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly body: unknown, readonly requestId: string) {
    super(message)
    this.name = 'ApiError'
  }
}
export const API_BASE = import.meta.env.VITE_API_BASE || '/pm/api'
export function sessionHeaders(extra: Record<string, string> = {}): Record<string, string> {
  let token = ''
  try { token = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}').sessionToken || '' } catch {}
  return { ...extra, 'X-PM-Session': token }
}
export async function request<T>(path: string, method = 'GET', body?: unknown, headers = sessionHeaders(), signal?: AbortSignal): Promise<T> {
  const multipart = body instanceof FormData
  const url = API_BASE + path + (method === 'GET' ? (path.includes('?') ? '&' : '?') + '_t=' + Date.now() : '')
  const response = await fetch(url, { method, signal, headers: body === undefined || multipart ? headers : { ...headers, 'Content-Type': 'application/json' }, cache: 'no-store', body: body === undefined ? undefined : multipart ? body : JSON.stringify(body) })
  const value = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(value?.error || value?.detail || `请求失败（HTTP ${response.status}）`, response.status, value, response.headers.get('X-Request-Id') || '')
  return value as T
}
