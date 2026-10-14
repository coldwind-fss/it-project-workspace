import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
export function useCollaborationUploadPage(){


const route = useRoute()
const router = useRouter()
const requirementId = String(route.query.requirementId || '').trim()
const projectId = String(route.query.projectId || '').trim()
const activityId = String(route.query.activityId || '').trim()
const requestedCollaborationId = String(route.query.collaborationId || '').trim()
const scopeId = requirementId || projectId

const currentUser = ref<any>({})
const requirement = ref<any>(null)
const activities = ref<any[]>([])
const collaborations = ref<any[]>([])
const selectedCollaborationId = ref(requestedCollaborationId)
const content = ref('')
const files = ref<File[]>([])
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const uploadError = ref('')
const successMessage = ref('')

const collaborationOptions = computed(() => collaborations.value.filter(item => !['resolved', 'closed'].includes(item.status)))
const selectedCollaboration = computed(() => collaborations.value.find(item => item.id === selectedCollaborationId.value) || collaborationOptions.value[0] || null)
const activityContext = computed(() => activities.value.find(item => item.id === activityId) || null)
const contextLabel = computed(() => activityContext.value ? '评论共享动态' : selectedCollaboration.value ? '继续协作讨论' : '新增业务反馈')
const canSubmit = computed(() => !!scopeId && (!!content.value.trim() || files.value.length > 0) && !!currentUser.value.sessionToken)

function readUser() {
  try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} }
}

function waitForDingTalkSdk(maxMs = 3500): Promise<any> {
  return new Promise(resolve => {
    const started = Date.now()
    const tick = () => {
      const dd = (window as any).dd
      if (dd) resolve(dd)
      else if (Date.now() - started >= maxMs) resolve(null)
      else window.setTimeout(tick, 120)
    }
    tick()
  })
}

async function ensureAuth() {
  if (currentUser.value.sessionToken) return true
  const cfg: any = await Promise.race([
    api.getDingTalkConfig(),
    new Promise(resolve => window.setTimeout(() => resolve(null), 3500)),
  ])
  const dd = await waitForDingTalkSdk()
  if (!dd?.runtime?.permission?.requestAuthCode) {
    errorMessage.value = cfg?.configured ? '请在钉钉内打开此页面后再提交反馈。' : '钉钉免登尚未配置，请联系管理员。'
    return false
  }
  const authAttempt = new Promise<boolean>(resolve => {
    const finish = async (code: string) => {
      if (!code) { errorMessage.value = '钉钉免登失败，请返回卡片后重试。'; resolve(false); return }
      const login: any = await api.loginWithDingTalk(code)
      if (!login?.user) { errorMessage.value = '无法识别当前钉钉用户，请重新打开卡片。'; resolve(false); return }
      currentUser.value = login.user
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(login.user))
      resolve(true)
    }
    const request = () => {
      const payload: any = { onSuccess: (res: any) => finish(res?.code || ''), onFail: () => { errorMessage.value = '钉钉免登失败，请返回卡片后重试。'; resolve(false) } }
      const search = new URLSearchParams(window.location.search)
      const corpId = search.get('corpId') || search.get('corpid') || localStorage.getItem('pm-corp-id') || cfg?.corpId || ''
      if (corpId) payload.corpId = corpId
      dd.runtime.permission.requestAuthCode(payload)
    }
    if (typeof dd.ready === 'function') dd.ready(request)
    else request()
  })
  return await Promise.race([
    authAttempt,
    new Promise<boolean>(resolve => window.setTimeout(() => {
      errorMessage.value = '钉钉免登响应超时，请返回卡片后重试。'
      resolve(false)
    }, 5000)),
  ])
}

async function loadContext() {
  if (!scopeId) {
    errorMessage.value = '当前卡片没有绑定有效的需求或产品编号。'
    loading.value = false
    return
  }
  const [req, activityRows, collaborationRows] = requirementId
    ? await Promise.all([
      api.getRequirement(requirementId),
      activityId ? api.getRequirementSharedActivities(requirementId) : Promise.resolve([]),
      activityId ? Promise.resolve([]) : api.getRequirementBusinessCollaborations(requirementId),
    ])
    : await Promise.all([
      api.getProject(projectId),
      activityId ? api.getProjectSharedActivities(projectId) : Promise.resolve([]),
      Promise.resolve([]),
    ])
  requirement.value = req
  if (Array.isArray(activityRows)) activities.value = activityRows
  if (Array.isArray(collaborationRows)) collaborations.value = collaborationRows
  if (!selectedCollaborationId.value && collaborationOptions.value.length) selectedCollaborationId.value = collaborationOptions.value[0].id
  if (!req) errorMessage.value = '需求信息读取失败，请返回卡片后重试。'
  loading.value = false
}

function addFiles(incoming: File[]) {
  for (const file of incoming) {
    if (file.size > 50 * 1024 * 1024) { uploadError.value = `附件「${file.name}」超过 50MB，未添加。`; continue }
    if (files.value.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) continue
    files.value.push(file)
  }
  if (files.value.length) uploadError.value = ''
}

function removeFile(index: number) { files.value.splice(index, 1) }

function handlePaste(event: ClipboardEvent) {
  const pasted = Array.from(event.clipboardData?.items || [])
    .filter(item => item.kind === 'file' && item.type.startsWith('image/'))
    .map(item => item.getAsFile())
    .filter(Boolean) as File[]
  if (!pasted.length) return
  event.preventDefault()
  addFiles(pasted.map((file, index) => new File([file], `clipboard-${Date.now()}-${index}.${file.type.split('/')[1] || 'png'}`, { type: file.type })))
}

async function submit() {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  errorMessage.value = ''
  uploadError.value = ''
  const text = content.value.trim() || '补充附件'
  let saved: any = null
  let ownerType = ''

  if (activityId) {
    saved = await api.createSharedActivityComment(activityId, { content: text })
    ownerType = 'shared_activity_comment'
  } else if (selectedCollaboration.value?.id) {
    saved = await api.createBusinessCollaborationMessage(selectedCollaboration.value.id, { content: text, messageType: 'message' })
    ownerType = 'collaboration_message'
  } else {
    saved = requirementId
      ? await api.createRequirementSharedActivity(requirementId, { activityType: 'feedback', title: '钉钉卡片反馈 / 补充', content: text })
      : await api.createProjectSharedActivity(projectId, { activityType: 'feedback', title: '钉钉卡片反馈 / 补充', content: text })
    ownerType = 'shared_activity'
  }

  if (!saved?.id) {
    errorMessage.value = '反馈保存失败，请返回卡片后重试。'
    saving.value = false
    return
  }

  const failed: string[] = []
  for (const file of files.value) {
    const uploaded = await api.uploadBusinessAttachment(ownerType, saved.id, file)
    if (!uploaded) failed.push(file.name)
  }
  saving.value = false
  if (failed.length) uploadError.value = `文字已同步，但以下附件上传失败：${failed.join('、')}`
  successMessage.value = failed.length ? '反馈已发送，部分附件需要重新补充' : '反馈与附件已发送'
  content.value = ''
  files.value = []
}

function openRequirement() { router.push(requirementId ? '/requirements/' + requirementId : '/projects/' + encodeURIComponent(projectId)) }
function goBack() { if (window.history.length > 1) window.history.back(); else window.close() }

onMounted(async () => {
  readUser()
  if (!scopeId) {
    errorMessage.value = '当前卡片没有绑定有效的需求或产品编号。'
    loading.value = false
    return
  }
  await ensureAuth()
  if (currentUser.value.sessionToken) await loadContext()
  else loading.value = false
})
return { route, router, requirementId, projectId, activityId, requestedCollaborationId, scopeId, currentUser, requirement, activities, collaborations, selectedCollaborationId, content, files, loading, saving, errorMessage, uploadError, successMessage, collaborationOptions, selectedCollaboration, activityContext, contextLabel, canSubmit, readUser, waitForDingTalkSdk, ensureAuth, loadContext, addFiles, removeFile, handlePaste, submit, openRequirement, goBack }
}
