import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './index.css'
import { reportClientLog } from './api'
import { showFeedback } from './utils/feedback'

// Keep existing business code readable while replacing native browser alerts
// with the same product-styled feedback surface used by the rest of the app.
window.alert = (message?: unknown) => showFeedback(message, { kind: /失败|错误|异常|无法|不能/.test(String(message || '')) ? 'error' : 'info' })

const app = createApp(App)

app.config.errorHandler = (err, instance, info) => {
  reportClientLog('error', 'Vue runtime error', {
    error: err instanceof Error ? { message: err.message, stack: err.stack } : String(err),
    info,
    component: instance?.$options?.name || '',
  })
}

window.addEventListener('error', event => {
  reportClientLog('error', event.message || 'Window error', {
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    stack: event.error?.stack,
  })
})

window.addEventListener('unhandledrejection', event => {
  const reason = event.reason
  reportClientLog('error', 'Unhandled promise rejection', {
    reason: reason instanceof Error ? { message: reason.message, stack: reason.stack } : String(reason),
  })
})

// Vite emits this event when a cached entry point tries to import a chunk that
// no longer exists after a deployment. Refresh once with a cache-busting query
// so a stale DingTalk/Feishu webview can recover without showing the fatal page.
window.addEventListener('vite:preloadError', event => {
  event.preventDefault()
  try {
    const key = 'pm-vite-preload-recovery'
    if (sessionStorage.getItem(key) === '1') return
    sessionStorage.setItem(key, '1')
    const url = new URL(window.location.href)
    url.searchParams.set('_pm_preload_reload', String(Date.now()))
    window.location.replace(url.toString())
  } catch {}
})

app.use(createPinia())
app.use(router)
app.mount('#root')
