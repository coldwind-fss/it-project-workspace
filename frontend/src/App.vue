<template>
  <div v-if="routeError" class="flex min-h-screen items-center justify-center bg-slate-50 px-6">
    <div class="w-full max-w-md rounded-2xl border border-amber-200 bg-white p-7 text-center shadow-sm">
      <p class="text-base font-semibold text-gray-900">页面加载遇到问题</p>
      <p class="mt-2 text-sm leading-6 text-gray-500">请重新加载当前页面；如果仍然出现空白，请把当前链接发给 IT。</p>
      <button type="button" class="feishu-btn-primary mt-5 justify-center px-5" @click="reloadPage">重新加载</button>
    </div>
  </div>
  <div v-else-if="entering" class="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-gray-600">正在进入系统…</div>
  <Suspense v-else>
    <template #default><router-view /></template>
    <template #fallback>
      <div class="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-gray-500">页面加载中…</div>
    </template>
  </Suspense>
  <FeedbackHost />
</template>

<script setup lang="ts">
import { computed, onErrorCaptured, ref } from 'vue'
import { useRouter } from 'vue-router'
import { reportClientLog } from './api'
import FeedbackHost from './components/FeedbackHost.vue'

const routeError = ref('')
const router=useRouter()
const entering=computed(()=>!router.currentRoute.value.matched.length)
router.onError(()=>{routeError.value='页面加载失败'})
const errorReference = ref('')
let errorReported = false

onErrorCaptured((error, instance, info) => {
  const errorMessage = String((error as Error)?.message || error || info || '页面加载失败')
  errorReference.value = `PM-${Date.now().toString(36).toUpperCase()}`
  routeError.value = errorMessage
  if (!errorReported) {
    errorReported = true
    reportClientLog('error', 'Vue captured render error', {
      errorId: errorReference.value,
      error: error instanceof Error ? { message: error.message, stack: error.stack } : String(error),
      info,
      component: instance?.$options?.name || instance?.$options?.__name || '',
      path: window.location.href,
    })
  }
  return false
})
function reloadPage() {
  const url = new URL(window.location.href)
  url.searchParams.set('_pm_error_reload', String(Date.now()))
  window.location.replace(url.toString())
}
</script>
