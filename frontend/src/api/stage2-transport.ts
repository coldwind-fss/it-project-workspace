import { ApiError, request, sessionHeaders, API_BASE } from './transport'
import { call } from './compat'
export const get = <T>(path: string) => call<T>(path)
export const post = <T>(path: string, body?: unknown) => call<T>(path, 'POST', body)
export const put = <T>(path: string, body?: unknown) => call<T>(path, 'PUT', body)
export const del = <T>(path: string) => call<T>(path, 'DELETE')
export const postMultipart = <T>(path: string, body: FormData) => call<T>(path, 'POST', body)
export async function postDetailed<T>(path: string, body: unknown): Promise<T | { _failed: true; error?: string; detail?: string; status?: number }> {
  try { return await request<T>(path, 'POST', body) }
  catch (error) {
    if (error instanceof ApiError) return { ...(error.body && typeof error.body === 'object' ? error.body : {}), _failed: true, status: error.status }
    return { _failed: true, error: '网络请求失败，请刷新页面后重试' }
  }
}
export const lifecycleCall = <T>(path: string, method = 'GET', body?: unknown, token = '') => request<T>(path, method, body, token ? { 'X-PM-Collaboration-Token': token } : sessionHeaders())
export async function getBlob(path: string): Promise<Blob | null> {
  try { return await download(path) } catch { return null }
}
export async function download(path: string, token = ''): Promise<Blob> {
  const response = await fetch(API_BASE + path, { headers: token ? { 'X-PM-Collaboration-Token': token } : sessionHeaders(), cache: 'no-store' })
  if (!response.ok) throw new ApiError('附件不存在、未授权或链接已失效', response.status, null, response.headers.get('X-Request-Id') || '')
  return response.blob()
}
