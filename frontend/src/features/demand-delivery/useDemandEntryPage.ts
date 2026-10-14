import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, ref } from 'vue'
import { api } from '../../api/application-api'
export function useDemandEntryPage() {


const currentUser = ref<any>({})
const projects = ref<any[]>([])
const departmentOptions = ref<string[]>([])
const files = ref<File[]>([])
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const uploadError = ref('')
const successMessage = ref('')
const submittedDemandId = ref('')
const entryToken = ref('')
const entryContext = ref<any>(null)
const entryMode = ref<'collect' | 'idea' | 'materials'>('collect')
const form = ref<any>({ title: '', description: '', department: '', projectId: '', expectedDeliveryTime: '', businessPriority: 'normal', intakeLevel: 'L3' })
const materialsForm = ref<any>({ additionalInfo: '' })
const collectionTopics = [
  { key: 'repeat', label: '重复做同一件事' },
  { key: 'excel', label: 'Excel / 群消息太多' },
  { key: 'error', label: '容易出错或反复核对' },
  { key: 'software', label: '现有软件不好用' },
  { key: 'new_tool', label: '想做新工具 / 系统' },
  { key: 'data', label: '数据、报表或查询不便' },
  { key: 'other', label: '其他想法' },
]
const collectionForm = ref<any>({ topic: 'repeat', problem: '', frequency: '', desired: '' })
const identityName = computed(() => entryContext.value?.recipientName || currentUser.value.name || '')
const identityDepartment = computed(() => entryContext.value?.department || currentUser.value.department || form.value.department || '')
const canSubmit = computed(() => !!(currentUser.value.sessionToken || entryToken.value) && !!form.value.description.trim() && !!form.value.department.trim())
const isMaterials = computed(() => entryMode.value === 'materials' && !!entryContext.value?.demandId)
const canSubmitMaterials = computed(() => !!(currentUser.value.sessionToken || entryToken.value) && (!!materialsForm.value.additionalInfo.trim() || files.value.length > 0))
const canSubmitCollection = computed(() => !!(currentUser.value.sessionToken || entryToken.value) && !!collectionForm.value.problem.trim() && !!form.value.department.trim())
const isIdea = computed(() => entryMode.value === 'idea')
const isCollection = computed(() => entryMode.value === 'collect')

function readUser() { try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} } }
function readEntryToken() {
  const hash = window.location.hash || ''
  const hashQuery = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : ''
  const params = new URLSearchParams(hashQuery || window.location.search.slice(1))
  return params.get('recipientToken') || params.get('token') || ''
}
function readEntryMode() {
  const hash = window.location.hash || ''
  const hashQuery = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : ''
  const params = new URLSearchParams(hashQuery || window.location.search.slice(1))
  const mode = params.get('mode')
  if (mode === 'materials') return 'materials'
  if (mode === 'idea' || mode === 'new') return 'idea'
  return 'collect'
}
function withTimeout<T>(promise: Promise<T>, maxMs: number, fallback: T): Promise<T> {
  return new Promise(resolve => {
    const timer = window.setTimeout(() => resolve(fallback), maxMs)
    promise.then(value => { window.clearTimeout(timer); resolve(value) }).catch(() => { window.clearTimeout(timer); resolve(fallback) })
  })
}
function waitForDingTalkSdk(maxMs = 3500): Promise<any> { return new Promise(resolve => { const started = Date.now(); const tick = () => { const dd = (window as any).dd; if (dd) resolve(dd); else if (Date.now() - started >= maxMs) resolve(null); else window.setTimeout(tick, 120) }; tick() }) }
async function ensureAuth() {
  if (currentUser.value.sessionToken) return true
  const cfg: any = await Promise.race([api.getDingTalkConfig(), new Promise(resolve => window.setTimeout(() => resolve(null), 3500))])
  const dd = await waitForDingTalkSdk()
  if (!dd?.runtime?.permission?.requestAuthCode) { errorMessage.value = cfg?.configured ? '请在钉钉内打开此页面后再提交。' : '钉钉免登尚未配置，请联系管理员。'; return false }
  return await new Promise<boolean>(resolve => {
    let settled = false
    const finishOnce = (value: boolean) => { if (settled) return; settled = true; resolve(value) }
    const timer = window.setTimeout(() => { errorMessage.value = '钉钉免登响应超时，请从钉钉内重新打开链接。'; finishOnce(false) }, 7000)
    const finish = async (code: string) => { if (!code) { errorMessage.value = '钉钉免登失败，请重试。'; window.clearTimeout(timer); finishOnce(false); return }; const login: any = await withTimeout(api.loginWithDingTalk(code), 7000, null); if (!login?.user) { errorMessage.value = '无法识别当前钉钉用户，请重新打开链接。'; window.clearTimeout(timer); finishOnce(false); return }; currentUser.value = login.user; localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(login.user)); window.clearTimeout(timer); finishOnce(true) }
    const request = () => { try { const search = new URLSearchParams(window.location.search); const payload: any = { onSuccess: (res: any) => { void finish(res?.code || '') }, onFail: () => { errorMessage.value = '钉钉免登失败，请重试。'; window.clearTimeout(timer); finishOnce(false) } }; const corpId = search.get('corpId') || search.get('corpid') || localStorage.getItem('pm-corp-id') || cfg?.corpId || ''; if (corpId) payload.corpId = corpId; dd.runtime.permission.requestAuthCode(payload) } catch { errorMessage.value = '钉钉免登接口调用失败，请重试。'; window.clearTimeout(timer); finishOnce(false) } }
    try { if (typeof dd.ready === 'function') dd.ready(request); else request() } catch { errorMessage.value = '钉钉免登接口调用失败，请重试。'; window.clearTimeout(timer); finishOnce(false) }
  })
}
function addFiles(incoming: File[]) { for (const file of incoming) { if (file.size > 50 * 1024 * 1024) { uploadError.value = `附件「${file.name}」超过 50MB，未添加。`; continue }; if (!files.value.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) files.value.push(file) }; if (files.value.length) uploadError.value = '' }
function removeFile(index: number) { files.value.splice(index, 1) }
function handlePaste(event: ClipboardEvent) { const pasted = Array.from(event.clipboardData?.items || []).filter(item => item.kind === 'file' && item.type.startsWith('image/')).map(item => item.getAsFile()).filter(Boolean) as File[]; if (!pasted.length) return; event.preventDefault(); addFiles(pasted.map((file, index) => new File([file], `clipboard-${Date.now()}-${index}.${file.type.split('/')[1] || 'png'}`, { type: file.type }))) }
async function submit() { if (!canSubmit.value || saving.value) return; saving.value = true; errorMessage.value = ''; uploadError.value = ''; const saved: any = await api.createDemandPoolItem({ ...form.value, sourceType: 'dingtalk_link', recipientToken: entryToken.value }); if (!saved?.id) { errorMessage.value = entryToken.value ? '需求提交失败，链接身份已失效，请重新获取提报链接。' : '需求提交失败，请重新获取提报链接。'; saving.value = false; return }; const failed: string[] = []; for (const file of files.value) if (!await api.uploadBusinessAttachment('demand_pool', saved.id, file, entryToken.value)) failed.push(file.name); if (failed.length) uploadError.value = `文字已保存，但以下附件上传失败：${failed.join('、')}`; saving.value = false; submittedDemandId.value = saved.id; successMessage.value = isIdea.value ? '需求提报已提交到 IT 系统' : '需求想法已提交到 IT 系统'; files.value = [] }
async function submitCollection() {
  if (!canSubmitCollection.value || saving.value) return
  const topic = collectionTopics.find(item => item.key === collectionForm.value.topic)?.label || '其他想法'
  const lines = [`【${topic}】`, collectionForm.value.problem.trim()]
  if (collectionForm.value.frequency) lines.push(`发生频率：${collectionForm.value.frequency}`)
  if (collectionForm.value.desired.trim()) lines.push(`希望变化：${collectionForm.value.desired.trim()}`)
  saving.value = true; errorMessage.value = ''; uploadError.value = ''
  const saved: any = await api.submitDemandCollectionResponse({ topicKey: collectionForm.value.topic, topicLabel: topic, problem: collectionForm.value.problem.trim(), frequency: collectionForm.value.frequency, desired: collectionForm.value.desired.trim(), description: lines.join('\n'), department: form.value.department.trim(), recipientToken: entryToken.value })
  if (!saved?.id) { errorMessage.value = entryToken.value ? '需求提交失败，链接身份已失效，请重新获取提报链接。' : (saved?.error || '需求提交失败，请重新获取提报链接。'); saving.value = false; return }
  const failed: string[] = []; for (const file of files.value) if (!await api.uploadBusinessAttachment('demand_collection_response', saved.id, file, entryToken.value)) failed.push(file.name)
  if (failed.length) uploadError.value = `文字已保存，但以下附件上传失败：${failed.join('、')}`
  saving.value = false; submittedDemandId.value = saved.id; successMessage.value = '需求想法已提交给 IT，等待评估'; files.value = []
}
async function submitMaterials() {
  if (!canSubmitMaterials.value || saving.value || !entryContext.value?.demandId) return
  saving.value = true; errorMessage.value = ''; uploadError.value = ''
  const saved: any = await api.submitDemandPoolMaterials({ demandId: entryContext.value.demandId, recipientToken: entryToken.value, additionalInfo: materialsForm.value.additionalInfo, hasAttachments: files.value.length > 0 })
  if (!saved?.id) { errorMessage.value = saved?.error || '补充资料提交失败，请重新打开链接。'; saving.value = false; return }
  const failed: string[] = []
  for (const file of files.value) if (!await api.uploadBusinessAttachment('demand_pool_supplement', saved.id, file, entryToken.value)) failed.push(file.name)
  if (failed.length) uploadError.value = `文字已保存，但以下附件上传失败：${failed.join('、')}`
  saving.value = false; submittedDemandId.value = entryContext.value.demandId; successMessage.value = '需求补充资料已提交'; files.value = []
}
function continueSubmission() { successMessage.value = ''; submittedDemandId.value = ''; materialsForm.value = { additionalInfo: '' }; collectionForm.value = { topic: 'repeat', problem: '', frequency: '', desired: '' }; form.value = { title: '', description: '', department: currentUser.value.department || entryContext.value?.department || '', projectId: '', expectedDeliveryTime: '', businessPriority: 'normal', intakeLevel: 'L3' }; files.value = []; uploadError.value = ''; errorMessage.value = '' }
onMounted(async () => {
  readUser()
  entryMode.value = readEntryMode() as 'collect' | 'idea' | 'materials'
  entryToken.value = readEntryToken()
  try {
    // Load the public form metadata first.  DingTalk auth is intentionally
    // independent so a delayed SDK callback cannot keep the whole page in a
    // permanent “preparing form” state.
    const [projectRows, options] = await Promise.all([
      withTimeout(api.getProjects(), 7000, null),
      withTimeout(api.getDingTalkOptions(), 7000, null),
    ])
    if (Array.isArray(projectRows)) projects.value = projectRows
    if (options?.departments?.length) departmentOptions.value = options.departments
    form.value.department = currentUser.value.department || ''
    if (entryToken.value) {
      const context: any = await withTimeout(api.getDemandPoolEntryContext(entryToken.value), 5000, null)
      if (context?.valid) {
        entryContext.value = context
        if (context.entryMode === 'materials') entryMode.value = 'materials'
        else if (context.entryMode === 'idea') entryMode.value = 'idea'
        currentUser.value = { ...currentUser.value, name: context.recipientName || currentUser.value.name || '钉钉用户', dingUserId: context.recipientUserId || currentUser.value.dingUserId || '', department: context.department || currentUser.value.department || '' }
        // A department-targeted robot link carries the source department. It
        // takes precedence over any stale browser session value so the
        // recipient does not have to trigger a second identity lookup by
        // touching the selector.
        if (context.department) form.value.department = context.department
      } else {
        errorMessage.value = '提报链接身份无法识别，请重新获取链接。'
        entryToken.value = ''
      }
    }
  } catch {
    errorMessage.value = '提报表单初始化失败，请刷新或从钉钉内重新打开链接。'
  } finally {
    loading.value = false
  }
  // The intake route is intentionally independent from DingTalk JS auth. A
  // robot-issued recipient token is the identity handoff for external
  // browsers; a generic link must not start a background免登 request merely
  // because the user focuses the department selector.
  if (!entryToken.value && !currentUser.value.sessionToken && !errorMessage.value) {
    errorMessage.value = '请从钉钉机器人发送的专属提报链接进入后提交。'
  }
  if (!form.value.department) form.value.department = currentUser.value.department || ''
})
return { currentUser, projects, departmentOptions, files, loading, saving, errorMessage, uploadError, successMessage, submittedDemandId, entryToken, entryContext, entryMode, form, materialsForm, collectionTopics, collectionForm, identityName, identityDepartment, canSubmit, isMaterials, canSubmitMaterials, canSubmitCollection, isIdea, isCollection, readUser, readEntryToken, readEntryMode, withTimeout, waitForDingTalkSdk, ensureAuth, addFiles, removeFile, handlePaste, submit, submitCollection, submitMaterials, continueSubmission }
}
