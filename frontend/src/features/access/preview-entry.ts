import { shallowRef } from 'vue'

// Configured only by the existing public preview release packaging.
export const PREVIEW_ENTRY = import.meta.env.VITE_PREVIEW_ENTRY || ''
export const entranceProblem = shallowRef('')
const recoveryKey = 'itpm-preview-entry-recovery'

export function enterPreview(path: string): boolean {
  if (!PREVIEW_ENTRY) return false
  try {
    const lastAttempt = Number(sessionStorage.getItem(recoveryKey) || 0)
    if (Date.now() - lastAttempt < 15000) return false
    sessionStorage.setItem(recoveryKey, String(Date.now()))
    const url = new URL(PREVIEW_ENTRY, window.location.origin)
    url.searchParams.set('next', path)
    window.location.replace(url.toString())
    return true
  } catch { return false }
}

export function entranceReady() {
  entranceProblem.value = ''
  try { sessionStorage.removeItem(recoveryKey) } catch {}
}

export function retryEntrance() {
  try { sessionStorage.removeItem(recoveryKey) } catch {}
  window.location.reload()
}
