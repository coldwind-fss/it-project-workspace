import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/application-api'
export function useDemandReviewEntryPage() {


const route = useRoute()
const reviewId = String(route.query.reviewId || '').trim()
const reviewToken = String(route.query.token || '').trim()
const currentUser = ref<any>({})
const review = ref<any>(null)
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const form = ref<any>({ decision: '', prioritySuggestion: '', comment: '' })
const branchDecisionMap = ref<Record<string, any>>({})
const reviewHint = computed(() => {
  const type = review.value?.demand?.solutionType
  if (type === 'workflow_automation') return '这个需求是否确实有必要推进，且优先级是否高于日常事项？重点看是否高频重复、影响多人或容易出错。'
  if (type === 'new_app_platform') return '这个新应用或平台是否属于当前必须建设的能力，是否值得投入正式项目资源？'
  if (type === 'software_replacement') return '现有软件是否确实需要替换，替换的必要性和当前时机是否成立？'
  if (type === 'data_integration') return '数据、报表或系统打通是否有明确的业务必要性，是否需要现在推进？'
  if (type === 'technical_foundation') return '这项稳定性、安全或基础能力建设是否需要优先处理，延后是否会带来明显风险？'
  if (type === 'existing_capability') return '这项已有系统能力是否有必要纳入当前项目，是否值得安排优先开发？'
  if (type === 'complex_refactor') return '这项重构是否有明确的必要性，继续维持现状是否会影响业务或系统稳定？'
  return '请结合需求原始描述和 IT 初筛摘要，判断这件事有没有必要做，以及应该排在什么优先级。'
})
const canSubmit = computed(() => {
  if (!(reviewToken || currentUser.value.sessionToken) || !form.value.decision || !form.value.prioritySuggestion) return false
  const branches = review.value?.demand?.l3Branches || []
  return branches.every((branch: any) => !!branchDecisionMap.value[branch.id]?.decision && !!branchDecisionMap.value[branch.id]?.prioritySuggestion)
})
function branchDecisionLabel(key: string) { return ({ support: '有必要实施', adjust: '有必要，但建议调整', reject: '暂无实施必要' } as Record<string, string>)[key] || key }
function syncBranchDecisions(result: any) {
  const stored = Array.isArray(result?.branchDecisions) ? result.branchDecisions : []
  const byId = new Map<string, { decision?: string; prioritySuggestion?: string; comment?: string }>(stored.map((item: any) => [String(item.branchId || item.branchKey || ''), item]))
  const next: Record<string, any> = {}
  for (const branch of result?.demand?.l3Branches || []) {
    const saved = byId.get(String(branch.id)) || byId.get(String(branch.branchKey)) || {}
    next[branch.id] = { decision: saved.decision || '', prioritySuggestion: saved.prioritySuggestion || '', comment: saved.comment || '' }
  }
  branchDecisionMap.value = next
}
function readUser() { try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} } }
function waitForDingTalkSdk(maxMs = 3500): Promise<any> { return new Promise(resolve => { const started = Date.now(); const tick = () => { const dd = (window as any).dd; if (dd) resolve(dd); else if (Date.now() - started >= maxMs) resolve(null); else window.setTimeout(tick, 120) }; tick() }) }
function withTimeout<T>(promise: Promise<T>, maxMs: number, fallback: T): Promise<T> {
  return new Promise(resolve => {
    const timer = window.setTimeout(() => resolve(fallback), maxMs)
    promise.then(value => { window.clearTimeout(timer); resolve(value) }).catch(() => { window.clearTimeout(timer); resolve(fallback) })
  })
}
async function ensureAuth() {
  if (currentUser.value.sessionToken) return true
  const cfg: any = await withTimeout(api.getDingTalkConfig(), 3500, null)
  const dd = await waitForDingTalkSdk()
  if (!dd?.runtime?.permission?.requestAuthCode) { errorMessage.value = cfg?.configured ? '请在钉钉内打开此页面后再提交。' : '钉钉免登尚未配置，请联系管理员。'; return false }
  return await new Promise<boolean>(resolve => {
    let settled = false
    const finishOnce = (value: boolean) => { if (settled) return; settled = true; window.clearTimeout(timer); resolve(value) }
    const timer = window.setTimeout(() => { errorMessage.value = '钉钉免登响应超时，请关闭后从钉钉通知中重新打开。'; finishOnce(false) }, 9000)
    const finish = async (code: string) => {
      if (!code) { errorMessage.value = '钉钉免登未返回授权码，请从钉钉内重新打开。'; finishOnce(false); return }
      const login: any = await withTimeout(api.loginWithDingTalk(code), 7000, null)
      if (!login?.user) { errorMessage.value = '无法识别当前钉钉用户，请重新打开链接。'; finishOnce(false); return }
      currentUser.value = login.user; localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(login.user)); finishOnce(true)
    }
    const request = () => {
      try {
        const search = new URLSearchParams(window.location.search)
        const payload: any = { onSuccess: (res: any) => { void finish(res?.code || '') }, onFail: () => { errorMessage.value = '钉钉免登失败，请重试。'; finishOnce(false) } }
        const corpId = search.get('corpId') || search.get('corpid') || localStorage.getItem('pm-corp-id') || cfg?.corpId || ''
        if (corpId) payload.corpId = corpId
        dd.runtime.permission.requestAuthCode(payload)
      } catch { errorMessage.value = '钉钉免登接口调用失败，请重试。'; finishOnce(false) }
    }
    if (typeof dd.ready === 'function') dd.ready(request); else request()
  })
}
async function submit() {
  if (!canSubmit.value || saving.value) return
  saving.value = true; errorMessage.value = ''
  const branchDecisions = Object.entries(branchDecisionMap.value).map(([branchId, value]) => ({ branchId, ...value }))
  const payload = { ...form.value, branchDecisions }
  const result: any = reviewToken
    ? await withTimeout(api.submitDemandPoolReviewByToken(reviewToken, payload), 8000, null)
    : await withTimeout(api.submitDemandPoolReview(reviewId, payload), 8000, null)
  saving.value = false
  if (!result?.id) { errorMessage.value = '评估意见提交失败或已超时，请重新打开最新评估链接。'; return }
  successMessage.value = '业务评估意见已提交'; review.value = result
}
onMounted(async () => {
  readUser()
  if (!reviewToken && !reviewId) { errorMessage.value = '评估链接无效。'; loading.value = false; return }
  let result: any = null
  if (reviewToken) {
    result = await withTimeout(api.getDemandPoolReviewByToken(reviewToken), 8000, null)
  } else {
    const authed = await ensureAuth()
    if (authed) result = await withTimeout(api.getDemandPoolReview(reviewId), 8000, null)
  }
  if (result) {
    review.value = result
    form.value = { decision: result.decision || '', prioritySuggestion: result.prioritySuggestion || '', comment: result.comment || '' }
    syncBranchDecisions(result)
  } else if (!errorMessage.value) {
    errorMessage.value = '评估链接读取失败或已超时，请重新打开最新评估链接。'
  }
  loading.value = false
})
return { route, reviewId, reviewToken, currentUser, review, loading, saving, errorMessage, successMessage, form, branchDecisionMap, reviewHint, canSubmit, branchDecisionLabel, syncBranchDecisions, readUser, waitForDingTalkSdk, withTimeout, ensureAuth, submit }
}
