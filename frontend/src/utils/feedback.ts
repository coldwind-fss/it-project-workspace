export type FeedbackKind = 'success' | 'error' | 'warning' | 'info'

export interface FeedbackToastOptions {
  kind?: FeedbackKind
  title?: string
  duration?: number
}

export interface FeedbackDialogOptions {
  title?: string
  confirmText?: string
  cancelText?: string
  kind?: FeedbackKind
  defaultValue?: string
  placeholder?: string
}

interface FeedbackHandler {
  toast: (message: string, options?: FeedbackToastOptions) => void
  confirm: (message: string, options?: FeedbackDialogOptions) => Promise<boolean>
  prompt: (message: string, options?: FeedbackDialogOptions) => Promise<string | null>
}

let handler: FeedbackHandler | null = null

export function registerFeedbackHandler(next: FeedbackHandler | null) {
  handler = next
}

export function showFeedback(message: unknown, options: FeedbackToastOptions = {}) {
  const text = String(message ?? '')
  if (handler) {
    handler.toast(text, options)
    return
  }
  window.dispatchEvent(new CustomEvent('pm-feedback-toast', { detail: { message: text, options } }))
}

export function showConfirm(message: string, options: FeedbackDialogOptions = {}) {
  if (handler) return handler.confirm(message, options)
  return Promise.resolve(window.confirm(message))
}

export function showPrompt(message: string, options: FeedbackDialogOptions = {}) {
  if (handler) return handler.prompt(message, options)
  return Promise.resolve(window.prompt(message, options.defaultValue || ''))
}
