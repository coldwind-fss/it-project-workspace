import { request } from './transport'
import { showFeedback } from '../utils/feedback'
import type { components } from './generated'

export type DTO<K extends keyof components['schemas']> = components['schemas'][K]
export async function call<T>(path: string, method = 'GET', body?: unknown): Promise<T | null> {
  try { return await request<T>(path, method, body) }
  catch (error) { showFeedback(error instanceof Error ? error.message : '请求失败', { kind: 'error' }); return null }
}
export function query(values: Record<string, string | number | undefined>) {
  const p = new URLSearchParams()
  for (const [key, value] of Object.entries(values)) if (value !== undefined && value !== '' && value !== '全部') p.set(key, String(value))
  return p.size ? '?' + p.toString() : ''
}

