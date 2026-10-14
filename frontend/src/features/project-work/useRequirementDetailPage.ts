import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
import { typeColors, priorityColors, statusColors, assigneeMap, changeTypeConfig } from '../../data/mockData'
import type { Requirement, Priority, RequirementStatus } from '../../types'
import { calculatePriorityAssessment, isPriorityAssessmentComplete, needsPriorityOverrideReason } from '../../utils/priorityAssessment'
export function useRequirementDetailPage() {


const route = useRoute()
const router = useRouter()
const id = computed(() => String(route.params.id || ''))

const STATUS_OPTS: RequirementStatus[] = ['待处理', '进行中', '待交付', '已交付', '已关闭']
const TYPE_OPTS = ['业务确认', '产品设计', '技术建设', '新增功能', '功能优化', '问题修复', '验证交付']
const ITEM_KIND_OPTS = [
  { key: 'initial_build', label: '初始建设' }, { key: 'feature', label: '新功能 / 模块' },
  { key: 'bugfix', label: '问题修复' }, { key: 'enhancement', label: '功能优化' },
  { key: 'integration', label: '接口 / 数据集成' }, { key: 'design', label: '产品设计' }, { key: 'operation', label: '运营维护' },
]
const CHANGE_OBJECT_OPTS = ['模块', '功能', '字段', '流程', '页面交互', '接口数据', '系统基础', '其他']
const IMPACT_OPTS = ['核心', '重要', '常规']
const WORKLOAD_OPTS = ['大', '中', '小']
const impactColors: Record<string, string> = { 核心: '#dc2626', 重要: '#d97706', 常规: '#64748b' }
const PRIORITY_OPTS: Priority[] = ['P0', 'P1', 'P2', 'P3', 'P4']

const req = ref<Requirement | null>(null)
const activityRevision = ref(0)
async function refreshLifecycleRelated() {
  const currentId = id.value
  const [updated, history] = await Promise.all([api.getRequirement(currentId), api.getRequirementChangelogs(currentId)])
  if (id.value !== currentId) return
  if (updated) req.value = updated
  if (history) changelogs.value = history
  activityRevision.value++
}
const changelogs = ref<any[]>([])
const detailLoading = ref(true)
const detailError = ref('')
const projects = ref<any[]>([])
const editing = ref(false)
const saving = ref(false)
const form = ref<any>({})
const previewModal = ref({ images: [] as any[], index: 0, open: false })
const showDeliveryImages = ref(false)
const peopleOpts = ref(['桑葚-於思旭', '玖杉-周荣', '安妮-宗艳琪'])
const devOpts = ref<string[]>([])
const deptOpts = ref<string[]>([])
const currentUser = ref<any>({})
const outcomeRequests = ref<any[]>([])
const postlaunchOutcomeRequests = computed(() => outcomeRequests.value.filter(item => ['day7', 'day30'].includes(item.stage)))
const outcomeContacts = ref<any[]>([])
const outcomeRecipientUserId = ref('')
const outcomeRecipientName = ref('')
const sendingOutcome = ref(false)

const canManageOutcome = computed(() => ['admin', 'super_admin', 'editor'].includes(String(currentUser.value.role || '')))
const canSendOutcomeGoal = computed(() => !!req.value && !['已上线', '已关闭', '已归档'].includes(String(req.value.status || '')))
const outcomeHint = computed(() => {
  const type = String(req.value?.type || '')
  if (type === '验证交付' || type === '问题修复') return '当前类型通常不需要成果目标确认；如确有需要，仍可按需发送。'
  return '建议在开发开始前发送；业务端只需确认方向，不需要填写基线、人数或成本。'
})

const projName = computed(() => {
  const p = projects.value.find((p: any) => p.id === (form.value.projectId || req.value?.projectId))
  return p?.name || req.value?.projectName || ''
})
const assessmentProjectPriority = computed(() => projects.value.find((p: any) => p.id === form.value.projectId)?.priority || 'P2')
const statusChanged = computed(() => !!req.value && !!form.value.status && form.value.status !== req.value.status)
const statusOnlyEdit = computed(() => {
  if (!req.value || !statusChanged.value) return false
  const fields = ['title', 'type', 'itemKind', 'parentRequirementId', 'versionTarget', 'priority', 'projectId', 'assignee', 'requester', 'department', 'description', 'acceptanceCriteria', 'expectedDeliveryTime', 'storyPoints', 'changeObject', 'impactLevel', 'workloadLevel']
  return fields.every(field => String(form.value[field] || '') === String((req.value as any)[field] || '')) &&
    JSON.stringify(form.value.images || []) === JSON.stringify(req.value.images || []) &&
    JSON.stringify(form.value.priorityEvaluation || {}) === JSON.stringify(req.value.priorityEvaluation || {})
})

function getAssignee(name: string) {
  const first = String(name || '').split(/[,，]/).map(item => item.trim()).find(Boolean) || ''
  return assigneeMap[first] || { initials: first.slice(0, 1) || '?', color: '#9ca3af' }
}
function getConfig(type: string) {
  return changeTypeConfig[type] || { color: '#6b7280', bgColor: '#f3f4f6', icon: '📝', desc: '' }
}

function startEdit() {
  if (!req.value) return
  form.value = {
    title: req.value.title, status: req.value.status, priority: req.value.priority,
    itemKind: req.value.itemKind || 'feature', parentRequirementId: req.value.parentRequirementId || '', versionTarget: req.value.versionTarget || '',
    assignee: req.value.assignee, requester: req.value.requester,
    department: req.value.department || req.value.projectDepartment || '',
    description: req.value.description, acceptanceCriteria: req.value.acceptanceCriteria || '', projectId: req.value.projectId,
    type: req.value.type, storyPoints: req.value.storyPoints,
    changeObject: req.value.changeObject || '功能', impactLevel: req.value.impactLevel || '常规', workloadLevel: req.value.workloadLevel || '中',
    expectedDeliveryTime: req.value.expectedDeliveryTime || '',
    images: req.value.images || [],
    priorityEvaluation: req.value.priorityEvaluation || {},
    reason: '',
  }
  editing.value = true
}
function cancelEdit() { editing.value = false; form.value = {} }

async function saveEdit() {
  if (!id.value) return
  // Capture this before recalculating an existing assessment. Recalculation
  // refreshes evaluatedAt and must not turn a status-only historical edit into
  // a full edit that is blocked by legacy missing fields.
  const statusOnly = statusOnlyEdit.value
  const priorityChanged = form.value.priority !== req.value?.priority
  if (priorityChanged && ['P0', 'P1'].includes(form.value.priority)) {
    if (!isPriorityAssessmentComplete(form.value.priorityEvaluation)) {
      alert('选择P0或P1时，请先完成4项优先级智能评估')
      return
    }
    form.value.priorityEvaluation = calculatePriorityAssessment(form.value.priorityEvaluation, assessmentProjectPriority.value)
    if (needsPriorityOverrideReason(form.value.priority, form.value.priorityEvaluation) && !String(form.value.priorityEvaluation.overrideReason || '').trim()) {
      alert('当前优先级高于系统建议，请填写调整原因')
      return
    }
  } else if (isPriorityAssessmentComplete(form.value.priorityEvaluation)) {
    form.value.priorityEvaluation = calculatePriorityAssessment(form.value.priorityEvaluation, assessmentProjectPriority.value)
  }
  if (statusChanged.value && !String(form.value.reason || '').trim()) {
    alert('状态变更需要填写调整说明')
    return
  }
  if (!statusOnly && (!form.value.department || !form.value.assignee || !form.value.expectedDeliveryTime)) {
    alert('归属部门、负责人、预计交付时间为必填项')
    saving.value = false
    return
  }
  saving.value = true
  const payload: any = statusOnly ? { status: form.value.status, reason: form.value.reason } : { ...form.value }
  if (!statusOnly && priorityChanged && !payload.reason) {
    const evaluation = form.value.priorityEvaluation || {}
    payload.reason = evaluation.overrideReason || (evaluation.recommendedPriority ? `智能评估建议${evaluation.recommendedPriority}（${evaluation.score}分）` : '调整需求优先级')
  }
  const updated = await api.updateRequirement(id.value, {
    ...payload,
    operator: form.value.assignee || req.value?.assignee || '系统',
  })
  if (updated) {
    req.value = updated
    activityRevision.value++
    editing.value = false
    form.value = {}
    const cl = await api.getRequirementChangelogs(id.value)
    if (cl) changelogs.value = cl
  }
  saving.value = false
}

function imageSrc(img: any) { return img?.data || img?.url || img }
function previewImages(imgs: any[], index = 0) { previewModal.value = { images: imgs || [], index, open: true } }

function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  appendImageFiles(Array.from(input.files || []))
  input.value = ''
}

function handleImagePaste(event: ClipboardEvent) {
  const files = Array.from(event.clipboardData?.files || [])
  if (!files.some(file => file.type.startsWith('image/'))) return
  event.preventDefault()
  appendImageFiles(files)
}

function appendImageFiles(files: File[]) {
  const imageFiles = files.filter(file => file.type.startsWith('image/'))
  if (!imageFiles.length) return
  if (!form.value.images) form.value.images = []
  imageFiles.forEach(file => {
    const reader = new FileReader()
    reader.onload = () => {
      form.value.images.push({
        id: 'img' + Date.now() + Math.random().toString(16).slice(2),
        name: file.name,
        type: file.type,
        data: String(reader.result || ''),
      })
    }
    reader.readAsDataURL(file)
  })
}

function removeImage(index: number) {
  form.value.images = [...(form.value.images || [])]
  form.value.images.splice(index, 1)
}

function outcomeContactById(userId: string) {
  return outcomeContacts.value.find(person => (person.userId || person.userid || person.dingUserId) === userId) || {}
}
async function sendOutcomeGoal() {
  if (!id.value || sendingOutcome.value) return
  const person = outcomeContactById(outcomeRecipientUserId.value)
  const recipientName = String(person.name || outcomeRecipientName.value || req.value?.requester || '').trim()
  if (!recipientName) { alert('请指定业务目标确认人'); return }
  sendingOutcome.value = true
  const result: any = await api.createRequirementOutcomeRequest(id.value, { stage: 'goal', recipientUserId: outcomeRecipientUserId.value, recipientName })
  sendingOutcome.value = false
  if (!result?.id) { alert(result?.error || '目标确认链接发送失败，请检查联系人和权限'); return }
  if (!outcomeRequests.value.some(item => item.id === result.id)) outcomeRequests.value.unshift(result)
  outcomeRecipientName.value = recipientName
  alert(result.notificationStatus === 'failed' ? '链接已生成，但钉钉发送失败，可复制链接手动发送' : '上线前目标确认链接已发送')
}
async function copyOutcomeLink(link: string) {
  if (!link) return
  try { await navigator.clipboard.writeText(link); alert('链接已复制') } catch { alert(link) }
}

let detailLoadSequence = 0
async function loadDetail() {
  const sequence = ++detailLoadSequence
  const requirementId = id.value
  detailLoading.value = true
  detailError.value = ''
  req.value = null
  changelogs.value = []
  outcomeRequests.value = []
  outcomeRecipientUserId.value = ''
  outcomeRecipientName.value = ''
  try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} }
  if (!requirementId) {
    detailError.value = '当前地址没有携带有效的需求编号。'
    detailLoading.value = false
    return
  }
  const [p, r, cl, outcomes] = await Promise.all([
    api.getProjects(),
    api.getRequirement(requirementId),
    api.getRequirementChangelogs(requirementId),
    api.getRequirementOutcomeRequests(requirementId),
  ])
  if (sequence !== detailLoadSequence) return
  if (p) projects.value = p
  if (r) req.value = r
  if (cl) changelogs.value = cl
  if (Array.isArray(outcomes)) outcomeRequests.value = outcomes
  if (!r) {
    detailError.value = `需求编号「${requirementId}」的详情接口没有返回数据，请重试或返回需求列表。`
    detailLoading.value = false
    return
  }
  detailLoading.value = false
  outcomeRecipientName.value = String((r as any).requester || '').split(/[,，]/).map((item: string) => item.trim()).find(Boolean) || ''

  // Editing options are non-critical to the read-only detail view. Load them
  // after the main requirement payload so a slow DingTalk endpoint cannot make
  // a valid requirement appear blank.
  api.getDingTalkOptions().then(opts => {
    if (sequence !== detailLoadSequence || !opts) return
    const people = [
      ...(opts.businessOwners || []),
      ...((opts.users || []).map((u: any) => u.name).filter(Boolean)),
    ]
    if (people.length) peopleOpts.value = Array.from(new Set(people))
    if (Array.isArray(opts.users)) outcomeContacts.value = opts.users.filter((person: any) => person && (person.name || person.userId || person.userid || person.dingUserId))
    if (!outcomeRecipientUserId.value && outcomeRecipientName.value && outcomeContacts.value.length) {
      const matched = outcomeContacts.value.find(person => String(person.name || '').trim() === outcomeRecipientName.value)
      if (matched) outcomeRecipientUserId.value = matched.userId || matched.userid || matched.dingUserId || ''
    }
    if (opts.developers?.length) devOpts.value = Array.from(new Set(opts.developers.map((d: any) => d.name || d.devOwnerName).filter(Boolean)))
    if (opts.departments?.length) deptOpts.value = opts.departments
  })
}

watch(id, loadDetail, { immediate: true })
return { route, router, id, STATUS_OPTS, TYPE_OPTS, ITEM_KIND_OPTS, CHANGE_OBJECT_OPTS, IMPACT_OPTS, WORKLOAD_OPTS, impactColors, PRIORITY_OPTS, req, activityRevision, refreshLifecycleRelated, changelogs, detailLoading, detailError, projects, editing, saving, form, previewModal, showDeliveryImages, peopleOpts, devOpts, deptOpts, currentUser, outcomeRequests, postlaunchOutcomeRequests, outcomeContacts, outcomeRecipientUserId, outcomeRecipientName, sendingOutcome, canManageOutcome, canSendOutcomeGoal, outcomeHint, projName, assessmentProjectPriority, statusChanged, statusOnlyEdit, getAssignee, getConfig, startEdit, cancelEdit, saveEdit, imageSrc, previewImages, handleImageUpload, handleImagePaste, appendImageFiles, removeImage, outcomeContactById, sendOutcomeGoal, copyOutcomeLink, detailLoadSequence, loadDetail, typeColors, priorityColors, statusColors, assigneeMap, changeTypeConfig }
}
