import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/application-api'
export function useDemandSupplementEntryPage() {


const route = useRoute()
const supplementId = String(route.query.supplementId || '').trim()
const currentUser = ref<any>({})
const supplement = ref<any>(null)
const answers = ref<Record<string, string>>({})
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const canSubmit = computed(() => !!currentUser.value.sessionToken && !!supplement.value && supplement.value.questions?.filter((q: any) => q.required).every((q: any) => String(answers.value[q.key] || '').trim()))
function readUser() { try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} } }
function waitForDingTalkSdk(maxMs = 3500): Promise<any> { return new Promise(resolve => { const started = Date.now(); const tick = () => { const dd = (window as any).dd; if (dd) resolve(dd); else if (Date.now() - started >= maxMs) resolve(null); else window.setTimeout(tick, 120) }; tick() }) }
async function ensureAuth() {
  if (currentUser.value.sessionToken) return true
  const cfg: any = await Promise.race([api.getDingTalkConfig(), new Promise(resolve => window.setTimeout(() => resolve(null), 3500))])
  const dd = await waitForDingTalkSdk()
  if (!dd?.runtime?.permission?.requestAuthCode) { errorMessage.value = cfg?.configured ? '请在钉钉内打开此页面后再提交。' : '钉钉免登尚未配置，请联系管理员。'; return false }
  return await new Promise<boolean>(resolve => { const finish = async (code: string) => { if (!code) { errorMessage.value = '钉钉免登失败，请重试。'; resolve(false); return }; const login: any = await api.loginWithDingTalk(code); if (!login?.user) { errorMessage.value = '无法识别当前钉钉用户，请重新打开链接。'; resolve(false); return }; currentUser.value = login.user; localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(login.user)); resolve(true) }; const request = () => { const payload: any = { onSuccess: (res: any) => finish(res?.code || ''), onFail: () => { errorMessage.value = '钉钉免登失败，请重试。'; resolve(false) } }; const corpId = new URLSearchParams(window.location.search).get('corpId') || localStorage.getItem('pm-corp-id') || cfg?.corpId || ''; if (corpId) payload.corpId = corpId; dd.runtime.permission.requestAuthCode(payload) }; if (typeof dd.ready === 'function') dd.ready(request); else request() })
}
async function submit() { if (!canSubmit.value || saving.value) return; saving.value = true; errorMessage.value = ''; const result: any = await api.submitDemandPoolSupplement(supplementId, answers.value); saving.value = false; if (!result?.id) { errorMessage.value = '补充信息提交失败，请返回钉钉后重试。'; return }; successMessage.value = '业务补充信息已提交'; supplement.value = { ...supplement.value, ...result, status: 'submitted' } }
onMounted(async () => { readUser(); if (!supplementId) { errorMessage.value = '补充单链接无效。'; loading.value = false; return }; const authed = await ensureAuth(); if (authed) { const result: any = await api.getDemandPoolSupplement(supplementId); if (result) { supplement.value = result; answers.value = { ...(result.answers || {}) } } else errorMessage.value = '补充单读取失败，请返回钉钉后重试。' }; loading.value = false })
return { route, supplementId, currentUser, supplement, answers, loading, saving, errorMessage, successMessage, canSubmit, readUser, waitForDingTalkSdk, ensureAuth, submit }
}
