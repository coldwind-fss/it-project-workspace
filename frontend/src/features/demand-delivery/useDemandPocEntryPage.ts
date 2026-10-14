import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/application-api'
export function useDemandPocEntryPage() {


const route = useRoute()
const demandId = String(route.query.demandId || '').trim()
const currentUser = ref<any>({})
const demand = ref<any>(null)
const pocs = ref<any[]>([])
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const files = ref<File[]>([])
const form = ref<any>({ summary: '', artifactType: 'text', aiUsed: 'none', aiNotes: '' })
const canSubmit = computed(() => !!currentUser.value.sessionToken && !!form.value.summary.trim() && !!demand.value?.canEvaluate)
function readUser() { try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} } }
function addFiles(incoming: File[]) { files.value.push(...incoming.filter(file => file.size <= 50 * 1024 * 1024)) }
function removeFile(index: number) { files.value.splice(index, 1) }
function waitForDingTalkSdk(maxMs = 3500): Promise<any> { return new Promise(resolve => { const started = Date.now(); const tick = () => { const dd = (window as any).dd; if (dd) resolve(dd); else if (Date.now() - started >= maxMs) resolve(null); else window.setTimeout(tick, 120) }; tick() }) }
async function ensureAuth() { if (currentUser.value.sessionToken) return true; const cfg: any = await Promise.race([api.getDingTalkConfig(), new Promise(resolve => window.setTimeout(() => resolve(null), 3500))]); const dd = await waitForDingTalkSdk(); if (!dd?.runtime?.permission?.requestAuthCode) { errorMessage.value = cfg?.configured ? '请在钉钉内打开此页面后再提交。' : '钉钉免登尚未配置，请联系管理员。'; return false }; return await new Promise<boolean>(resolve => { const finish = async (code: string) => { if (!code) { errorMessage.value = '钉钉免登失败，请重试。'; resolve(false); return }; const login: any = await api.loginWithDingTalk(code); if (!login?.user) { errorMessage.value = '无法识别当前钉钉用户，请重新打开链接。'; resolve(false); return }; currentUser.value = login.user; localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(login.user)); resolve(true) }; const request = () => { const payload: any = { onSuccess: (res: any) => finish(res?.code || ''), onFail: () => { errorMessage.value = '钉钉免登失败，请重试。'; resolve(false) } }; const corpId = new URLSearchParams(window.location.search).get('corpId') || localStorage.getItem('pm-corp-id') || cfg?.corpId || ''; if (corpId) payload.corpId = corpId; dd.runtime.permission.requestAuthCode(payload) }; if (typeof dd.ready === 'function') dd.ready(request); else request() }) }
async function submit() { if (!canSubmit.value || saving.value) return; saving.value = true; errorMessage.value = ''; const result: any = await api.createDemandPoolPoc(demandId, { summary: form.value.summary, artifactType: form.value.artifactType, aiUsed: form.value.aiUsed, aiNotes: form.value.aiNotes }); if (!result?.id) { saving.value = false; errorMessage.value = '验证记录保存失败，请确认当前账号有 IT 评估权限。'; return }; for (const file of files.value) await api.uploadBusinessAttachment('demand_pool_poc', result.id, file); saving.value = false; successMessage.value = '验证记录已保存'; pocs.value.unshift(result) }
onMounted(async () => { readUser(); if (!demandId) { errorMessage.value = '需求链接无效。'; loading.value = false; return }; const authed = await ensureAuth(); if (authed) { const [item, rows] = await Promise.all([api.getDemandPoolItem(demandId), api.getDemandPoolPocs(demandId)]); if (item) demand.value = item; else errorMessage.value = '需求读取失败，请返回需求池重试。'; if (Array.isArray(rows)) pocs.value = rows }; loading.value = false })
return { route, demandId, currentUser, demand, pocs, loading, saving, errorMessage, successMessage, files, form, canSubmit, readUser, addFiles, removeFile, waitForDingTalkSdk, ensureAuth, submit }
}
