<template>
  <div class="pointer-events-none fixed inset-0 z-[100] flex flex-col items-end gap-3 p-4 sm:p-6">
    <TransitionGroup name="feedback-toast" tag="div" class="flex w-full max-w-sm flex-col items-end gap-3">
      <div v-for="item in toasts" :key="item.id" :class="toastClass(item.kind)" class="pointer-events-auto w-full rounded-xl border px-4 py-3 shadow-lg backdrop-blur">
        <div class="flex items-start gap-3">
          <component :is="iconFor(item.kind)" class="mt-0.5 h-4 w-4 shrink-0" />
          <div class="min-w-0 flex-1"><p v-if="item.title" class="text-xs font-semibold">{{ item.title }}</p><p class="text-sm leading-5">{{ item.message }}</p></div>
          <button type="button" class="rounded-md p-1 opacity-60 hover:bg-black/5 hover:opacity-100" aria-label="关闭" @click="removeToast(item.id)"><X class="h-3.5 w-3.5" /></button>
        </div>
      </div>
    </TransitionGroup>

    <Transition name="feedback-dialog">
      <div v-if="dialog" class="pointer-events-auto fixed inset-0 flex items-center justify-center bg-slate-900/30 p-4" @click.self="finishDialog(false)">
        <div class="w-full max-w-md rounded-2xl border border-gray-100 bg-white p-5 shadow-2xl">
          <div class="flex items-start gap-3"><div :class="dialogIconClass(dialog.kind)" class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"><component :is="iconFor(dialog.kind)" class="h-4.5 w-4.5" /></div><div class="min-w-0"><h3 class="text-sm font-semibold text-gray-900">{{ dialog.title }}</h3><p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-gray-600">{{ dialog.message }}</p></div></div>
          <input v-if="dialog.mode === 'prompt'" v-model="dialog.value" autofocus class="feishu-input mt-4 w-full" :placeholder="dialog.placeholder" @keyup.enter="finishDialog(true)" />
          <div class="mt-5 flex justify-end gap-2"><button type="button" class="feishu-btn-ghost text-xs" @click="finishDialog(false)">{{ dialog.cancelText }}</button><button type="button" class="feishu-btn-primary text-xs" @click="finishDialog(true)">{{ dialog.confirmText }}</button></div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-vue-next'
import { registerFeedbackHandler, type FeedbackDialogOptions, type FeedbackKind, type FeedbackToastOptions } from '../utils/feedback'

interface ToastItem { id: number; message: string; kind: FeedbackKind; title?: string }
interface DialogState { mode: 'confirm' | 'prompt'; message: string; title: string; kind: FeedbackKind; confirmText: string; cancelText: string; placeholder?: string; value: string; resolve: (value: boolean | string | null) => void }

const toasts = ref<ToastItem[]>([])
const dialog = ref<DialogState | null>(null)
let nextId = 1
const timers = new Map<number, ReturnType<typeof setTimeout>>()

function iconFor(kind: FeedbackKind) { return kind === 'success' ? CheckCircle2 : kind === 'warning' || kind === 'error' ? AlertTriangle : Info }
function toastClass(kind: FeedbackKind) { return kind === 'success' ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : kind === 'error' ? 'border-rose-100 bg-rose-50 text-rose-800' : kind === 'warning' ? 'border-amber-100 bg-amber-50 text-amber-800' : 'border-blue-100 bg-blue-50 text-blue-800' }
function dialogIconClass(kind: FeedbackKind) { return kind === 'error' ? 'bg-rose-50 text-rose-600' : kind === 'warning' ? 'bg-amber-50 text-amber-600' : kind === 'success' ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600' }
function removeToast(id: number) { const timer = timers.get(id); if (timer) clearTimeout(timer); timers.delete(id); toasts.value = toasts.value.filter(item => item.id !== id) }
function toast(message: string, options: FeedbackToastOptions = {}) { const id = nextId++; toasts.value.push({ id, message, kind: options.kind || 'info', title: options.title }); const duration = options.duration ?? 3600; if (duration > 0) timers.set(id, setTimeout(() => removeToast(id), duration)) }
function openDialog(mode: 'confirm' | 'prompt', message: string, options: FeedbackDialogOptions = {}) {
  return new Promise<boolean | string | null>(resolve => {
    dialog.value = { mode, message, resolve, title: options.title || (mode === 'prompt' ? '请补充说明' : '请确认操作'), kind: options.kind || 'warning', confirmText: options.confirmText || '确认', cancelText: options.cancelText || '取消', placeholder: options.placeholder, value: options.defaultValue || '' }
  })
}
function finishDialog(confirmed: boolean) { const current = dialog.value; if (!current) return; dialog.value = null; current.resolve(current.mode === 'prompt' ? (confirmed ? current.value : null) : confirmed) }
function handleToast(event: Event) { const detail = (event as CustomEvent).detail || {}; toast(String(detail.message ?? ''), detail.options || {}) }

onMounted(() => {
  const api = { toast, confirm: (message: string, options?: FeedbackDialogOptions) => openDialog('confirm', message, options).then(Boolean), prompt: (message: string, options?: FeedbackDialogOptions) => openDialog('prompt', message, options).then(value => typeof value === 'string' ? value : null) }
  registerFeedbackHandler(api)
  window.addEventListener('pm-feedback-toast', handleToast)
})
onUnmounted(() => { registerFeedbackHandler(null); window.removeEventListener('pm-feedback-toast', handleToast); timers.forEach(timer => clearTimeout(timer)) })
</script>

<style scoped>
.feedback-toast-enter-active, .feedback-toast-leave-active, .feedback-dialog-enter-active, .feedback-dialog-leave-active { transition: opacity .18s ease, transform .18s ease; }
.feedback-toast-enter-from, .feedback-toast-leave-to { opacity: 0; transform: translateY(-8px); }
.feedback-dialog-enter-from, .feedback-dialog-leave-to { opacity: 0; }
</style>
