import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
import { hasAction } from '../access/session-access'
import { deliveryStandardFields, deliveryStandardLabel, normalizeDeliveryStandardType, valueMetricPresets } from '../../shared/deliveryStandards'
export function useDemandPoolPage() {


const route = useRoute()
const router = useRouter()
const currentUser = ref<any>({})
const items = ref<any[]>([])
const projects = ref<any[]>([])
const requirements = ref<any[]>([])
const developerOptions = ref<any[]>([])
const contactUsers = ref<any[]>([])
const departmentOptions = ref<string[]>([])
const contactsLoading = ref(false)
const contactsLoaded = ref(false)
let contactsRequest: Promise<any> | null = null
const statusOptions = ref<any[]>([])
const decisionOptions = ref<any[]>([])
const priorityOptions = ref<any[]>([
  { key: 'urgent', label: '希望尽快' },
  { key: 'planned', label: '计划内' },
  { key: 'normal', label: '暂无明确时间' },
])
const businessReviewDecisionOptions = [
  { key: 'support', label: '有必要实施' },
  { key: 'adjust', label: '有必要，但建议调整' },
  { key: 'reject', label: '暂无实施必要' },
]
const reviewPriorityOptions = [
  { key: 'P0', label: 'P0' }, { key: 'P1', label: 'P1' },
  { key: 'P2', label: 'P2' }, { key: 'P3', label: 'P3' },
]
const intakeLevelOptions = ref<any[]>([
  { key: 'L2', label: 'L2 项目' },
  { key: 'L3', label: 'L3 新功能 / 复杂需求重构' },
])
const solutionTypeOptions = ref<any[]>([])
const impactScopeOptions = ref<any[]>([])
const complexityOptions = ref<any[]>([])
const aiOptions = ref<any[]>([])
const pocOptions = ref<any[]>([])
const nextActionOptions = ref<any[]>([])
const templates = ref<Record<string, any[]>>({})
const lifecycleOptions = ref<any>({ solutionTypes: [], itemKinds: [], templates: {} })
const activeStatus = ref('all')
const selectedId = ref('')
const showForm = ref(String(route.query.new || '') === '1')
const showNotify = ref(false)
const loading = ref(false)
const saving = ref(false)
const savingEvaluation = ref(false)
const triageSplitEnabled = ref(false)
const triageBranches = ref<any[]>([])
const branchDecisionDraft = ref<Record<string, any>>({})
const assigningReviews = ref(false)
const reusingBusinessReview = ref(false)
const reuseBusinessReviewError = ref('')
const sendingNotify = ref(false)
const creatingConfirmation = ref(false)
const resendingConfirmation = ref(false)
const confirmationDraft = ref<any>(emptyConfirmationDraft())
const converting = ref(false)
const savingSupplement = ref(false)
const creatingPoc = ref(false)
const updatingPoc = ref(false)
const savingValueCard = ref(false)
const creatingOutcomeRequest = ref(false)
const pocModalOpen = ref(false)
const savingPocModal = ref(false)
const formError = ref('')
const conversionError = ref('')
const uploadError = ref('')
const notifyError = ref('')
const pocModalError = ref('')
const files = ref<File[]>([])
const pocModalFiles = ref<File[]>([])
const form = ref<any>({ title: '', description: '', department: '', projectId: '', expectedDeliveryTime: '', businessPriority: 'normal', intakeLevel: 'L3' })
const evaluation = ref<any>({ decision: '', requestType: '', solutionType: '', intakePath: '', aiMode: 'none', aiScenario: '', pocRequirement: 'none', impactScope: 'single_department', complexityLevel: 'medium', completeness: 'complete', similarDemandId: '', nextAction: 'final_review', reason: '', notes: '' })
const confirmationTemplateType = computed(() => normalizeDeliveryStandardType(selectedItem.value?.solutionType || evaluation.value.solutionType || 'custom'))
const confirmationTemplateLabel = computed(() => deliveryStandardLabel(confirmationTemplateType.value))
const confirmationTemplateFields = computed(() => deliveryStandardFields(confirmationTemplateType.value))
const confirmationMetricPresets = computed(() => valueMetricPresets(confirmationTemplateType.value))
const confirmationFieldsFor = (type: any) => deliveryStandardFields(normalizeDeliveryStandardType(type))
const canCreateConfirmation = computed(() => {
  const draft = confirmationDraft.value
  const definition = draft.valueDefinition || {}
  if (!draft.expected?.trim() || !definition.expectedSummary?.trim()) return false
  const metrics = Array.isArray(definition.metrics) ? definition.metrics : []
  if (!definition.verificationMode || definition.verificationMode === 'outcome') return true
  return definition.verificationMode === 'quantitative' && metrics.length > 0 && metrics.every(confirmationMetricComplete)
})
const supplementAnswers = ref<Record<string, string>>({})
const pocForm = ref<any>({ goal: '', baseline: '', scope: '', testData: '', successCriteria: '', ownerUserId: '', ownerName: '', dueDate: '' })
const pocModalForm = ref<any>({ summary: '', artifactType: 'text', aiUsed: 'none', aiNotes: '' })
const valueCardForm = ref<any>({ ownerName: '', baselineSummary: '', expectedSummary: '', day7Summary: '', day30Summary: '', targetMet: '', metrics: [] })
const reviewAssignment = ref<any>({ leaderUserId: '', departmentUserId: '' })
const businessReviewReuse = ref<any>({ contactName: '', contactUserId: '', communicationDate: new Date().toISOString().slice(0, 10), source: '会议沟通', decision: 'support', prioritySuggestion: 'P2', summary: '' })
const notifyForm = ref<any>({ entryMode: 'collect', targetType: 'person', targetUserId: '', targetValue: '', demandId: '', message: '', scheduleCycle: 'once', scheduleTime: '', scheduleDay: 1, scheduleWeekdays: [1, 2, 3, 4, 5] })
const demandNotifications = ref<any[]>([])
const collectionManagerOpen = ref(false)
const collectionConfigOpen = ref(true)
const collectionLoading = ref(false)
const collectionRetrying = ref(false)
const collectionBatches = ref<any[]>([])
const selectedCollectionBatch = ref<any>(null)
const selectedCollectionResponse = ref<any>(null)
const judgingCollection = ref(false)
const collectionJudgment = ref<any>({ judgment: '', judgmentReason: '', similarDemandId: '', nextAction: '' })
const conversion = ref<any>({ mode: 'create', title: '', projectName: '', projectId: '', requirementId: '', solutionType: '', itemKind: 'feature', phaseTemplateKeys: [], type: '新增功能', priority: 'P2', assignee: '', department: '', expectedDeliveryTime: '', acceptanceCriteria: '', splitEnabled: false, splitUnits: [] })

const filteredItems = computed(() => activeStatus.value === 'all' ? items.value : items.value.filter(item => item.status === activeStatus.value))
const selectedItem = computed(() => items.value.find(item => item.id === selectedId.value) || filteredItems.value[0] || null)
const collectionLinkCandidates = computed(() => items.value.filter(item => item.id !== selectedCollectionResponse.value?.convertedDemandId && item.id !== selectedCollectionResponse.value?.convertedDemand?.id).slice(0, 200))
const collectionJudgmentReady = computed(() => {
  const judgment = collectionJudgment.value.judgment
  if (!judgment) return false
  if (judgment === 'duplicate' && !collectionJudgment.value.similarDemandId) return false
  return true
})
const canSubmit = computed(() => !!form.value.description.trim() && !!form.value.department.trim() && !!currentUser.value.sessionToken)
const canManage = computed(() => hasAction('demand_pool.manage') || !!selectedItem.value?.canEvaluate)
const branchDecisionsComplete = computed(() => {
  const branches = selectedItem.value?.l3Branches || []
  return branches.length > 0 && branches.every((branch: any) => {
    const draft = branchDecisionDraft.value[branch.id]
    return !!draft?.decision && (!['defer', 'reject'].includes(draft.decision) || !!String(draft.reason || '').trim())
  })
})
const canAssignReviews = computed(() => !!reviewAssignment.value.leaderUserId || !!reviewAssignment.value.departmentUserId)
const canReuseBusinessReview = computed(() => !!selectedItem.value?.solutionType
  && !!String(businessReviewReuse.value.contactName || '').trim()
  && !!String(businessReviewReuse.value.communicationDate || '').trim()
  && !!businessReviewReuse.value.decision
  && !!businessReviewReuse.value.prioritySuggestion
  && !!String(businessReviewReuse.value.summary || '').trim())
const demandEntryLink = computed(() => `${window.location.origin}${window.location.pathname}#/entry/demand`)
const pocEntryLink = computed(() => selectedItem.value ? `${window.location.origin}${window.location.pathname}#/entry/demand-poc?demandId=${encodeURIComponent(selectedItem.value.id)}` : '#')
const templateQuestions = computed(() => templates.value[evaluation.value.solutionType] || [])
const lifecycleSolutionTypeOptions = computed(() => lifecycleOptions.value.solutionTypes?.filter((item: any) => item.key !== 'unknown') || solutionTypeOptions.value)
const l3ItemKindOptions = computed(() => (lifecycleOptions.value.itemKinds || []).filter((item: any) => item.key !== 'initial_build'))
const solutionTypeAlias: Record<string, string> = { new_app_platform: 'custom_application', custom: 'custom_application', existing_capability: 'custom_application', workflow: 'workflow_automation', rpa: 'workflow_automation', data: 'data_integration', integration: 'data_integration', ai: 'ai_agent', agent: 'ai_agent' }
const normalizeLifecycleSolutionType = (value: any) => solutionTypeAlias[String(value || '').trim()] || String(value || '').trim()
const conversionProject = computed(() => projects.value.find((project: any) => project.id === conversion.value.projectId) || null)
const conversionSolutionType = computed(() => conversion.value.mode === 'create_l2' ? conversion.value.solutionType : (conversionProject.value?.solutionType || ''))
const conversionPhaseTemplates = computed(() => lifecycleOptions.value.templates?.[conversionSolutionType.value] || conversionProject.value?.phaseTemplates || [])
const conversionRequirements = computed(() => requirements.value.filter((item: any) => item.projectId === conversion.value.projectId))
const conversionModeHelp = computed(() => {
  if (conversion.value.mode === 'create_l2') return '新应用、系统或工作流使用此入口；系统会先建立 L2，再自动生成一个“初始建设”L3，并写入对应类型的阶段卡。'
  if (conversion.value.mode === 'create') return '已有应用增加功能、优化、集成或修复时使用；必须先选归属 L2。一个业务提报如包含多个独立交付物，可在这里拆成多个 L3。'
  return '需求已经属于已有工作时使用；先选 L2，再从该 L2 下选择要关联的 L3。'
})
const valuePolicy = computed(() => selectedItem.value?.valuePolicy || { level: 'light', label: '轻量记录', reason: '分类后系统会按需提示。', ownerRole: '业务负责人确认目标，IT 记录上线前后的证据。', expectationLabel: '期望变化', baselineLabel: '当前情况（可选）', metricHint: '用一句话说明现在怎样、上线后希望怎样即可；没有数字也可以。', requiresExpectation: false, requiresBaseline: false, isTechnical: false })
const outcomeStageOptions = [
  { key: 'goal', label: '发起成果确认' },
  { key: 'day7', label: '发起 3 天回执' },
  { key: 'day30', label: '发起 30 天复盘' },
]
const summaryCards = computed(() => {
  const count = (status: string) => items.value.filter(item => item.status === status).length
  return [
    { key: 'all', label: '全部提报', value: items.value.length, color: 'text-gray-800' },
    { key: 'pending_evaluation', label: '待评估', value: count('pending_evaluation'), color: 'text-rose-600' },
    { key: 'evaluating', label: '评估中', value: count('evaluating'), color: 'text-amber-600' },
    { key: 'awaiting_confirmation', label: '待正式立项', value: count('awaiting_confirmation'), color: 'text-violet-600' },
    { key: 'converted', label: '已转正式L3', value: count('converted'), color: 'text-emerald-600' },
  ]
})
const lifecycleStages = computed(() => {
  const item = selectedItem.value
  if (!item) return []
  const reviewTotal = Number(item.reviewSummary?.total || 0)
  const reviewPending = Number(item.reviewSummary?.pending || 0)
  const reviewDone = reviewTotal > 0 && reviewPending === 0
  const hasDecision = !!item.evaluationDecision
  const poc = item.pocs?.[0]
  const pocDone = !!poc && ['completed', 'documented'].includes(poc.status)
  const pocInProgress = !!poc && !pocDone && poc.status !== 'cancelled'
  const pocBranch = item.evaluationDecision === 'poc' || item.status === 'poc' || !!poc
  const formalDone = !!item.requirementId
  const outcomeDone = !!item.valueCard || !!item.outcomeRequests?.length
  const triageState = item.solutionType ? 'done' : 'current'
  const reviewState = !item.solutionType ? 'locked' : reviewDone ? 'done' : 'current'
  const decisionState = hasDecision ? 'done' : !item.solutionType ? 'locked' : 'current'
  const pocState = pocDone ? 'done' : pocInProgress || (pocBranch && !pocDone) ? 'current' : hasDecision ? 'na' : 'locked'
  const formalState = formalDone ? 'done' : item.evaluationDecision === 'implement' && (!item.pocRequirement || item.pocRequirement === 'none' || pocDone) ? 'current' : 'locked'
  const outcomeState = outcomeDone ? 'done' : formalDone ? 'current' : 'locked'
  return [
    { key: 'intake', label: '需求提报', state: 'done', summary: `${item.requesterName || '业务人员'} 已提交原始需求` },
    { key: 'triage', label: 'IT 初筛', state: triageState, summary: item.solutionTypeLabel || '等待选择需求类型' },
    { key: 'review', label: '业务评估', state: reviewState, summary: reviewTotal ? `${item.reviewSummary?.submitted || 0}/${reviewTotal} 条回执` : '尚未发起评估' },
    { key: 'decision', label: 'IT 综合决策', state: decisionState, summary: item.evaluationDecisionLabel || '等待综合判断' },
    { key: 'poc', label: 'PoC 验证', state: pocState, summary: pocDone ? '验证记录已完成' : pocInProgress ? '验证进行中' : pocBranch ? '等待登记验证结论' : '按需启用' },
    { key: 'formal', label: '正式立项', state: formalState, summary: formalDone ? (item.requirementTitle || 'L2/L3 已建立') : '等待创建或关联 L2/L3' },
    { key: 'outcome', label: '成果回访', state: outcomeState, summary: outcomeDone ? '已有目标 / 回访记录' : formalDone ? '等待 3 天回执与 30 天复盘' : '正式上线后进行' },
  ]
})
function lifecycleStageLabel(state: string) {
  return state === 'done' ? '已完成' : state === 'current' ? '进行中' : state === 'na' ? '不适用' : '待前置'
}
function lifecycleStageClass(state: string) {
  if (state === 'done') return 'border-emerald-200 bg-emerald-50 text-emerald-900'
  if (state === 'current') return 'border-blue-300 bg-blue-50 text-blue-900 shadow-sm'
  if (state === 'na') return 'border-slate-200 bg-white text-slate-400'
  return 'border-slate-200 bg-slate-50 text-slate-400'
}
function decisionLabelFor(key: string) {
  return decisionOptions.value.find(item => item.key === key)?.label || ({ implement: '实施', poc: 'PoC', defer: '暂缓', reject: '不承接', merge: '合并已有需求', ordinary: '转普通事项' } as Record<string, string>)[key] || key
}
function solutionTypeLabelFor(key: string) {
  return solutionTypeOptions.value.find(item => item.key === key)?.label || key
}

function readUser() {
  try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} }
  if (!form.value.department) form.value.department = currentUser.value.department || ''
}
function addFiles(incoming: File[]) {
  for (const file of incoming) {
    if (file.size > 50 * 1024 * 1024) { uploadError.value = `附件「${file.name}」超过 50MB，未添加。`; continue }
    if (!files.value.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) files.value.push(file)
  }
  if (files.value.length) uploadError.value = ''
}
function removeFile(index: number) { files.value.splice(index, 1) }
function handlePaste(event: ClipboardEvent) {
  const pasted = Array.from(event.clipboardData?.items || []).filter(item => item.kind === 'file' && item.type.startsWith('image/')).map(item => item.getAsFile()).filter(Boolean) as File[]
  if (!pasted.length) return
  event.preventDefault()
  addFiles(pasted.map((file, index) => new File([file], `clipboard-${Date.now()}-${index}.${file.type.split('/')[1] || 'png'}`, { type: file.type })))
}
async function uploadPending(ownerId: string) {
  const failed: string[] = []
  for (const file of files.value) if (!await api.uploadBusinessAttachment('demand_pool', ownerId, file)) failed.push(file.name)
  if (failed.length) uploadError.value = `提报已保存，但以下附件上传失败：${failed.join('、')}`
}
async function submit() {
  if (!canSubmit.value || saving.value) return
  saving.value = true; formError.value = ''; uploadError.value = ''
  const saved: any = await api.createDemandPoolItem({ ...form.value })
  if (!saved?.id) { formError.value = '提报失败，请检查登录状态后重试。'; saving.value = false; return }
  if (files.value.length) await uploadPending(saved.id)
  saved.attachments = []
  items.value.unshift(saved); selectedId.value = saved.id; showForm.value = false
  form.value = { title: '', description: '', department: currentUser.value.department || '', projectId: '', expectedDeliveryTime: '', businessPriority: 'normal', intakeLevel: 'L3' }
  files.value = []; saving.value = false
}
function valueMetricRows(card: any) {
  const baseline = Array.isArray(card?.baseline?.metrics) ? card.baseline.metrics : []
  const expected = Array.isArray(card?.expected?.metrics) ? card.expected.metrics : []
  const byKey = new Map<string, any>()
  for (const item of [...baseline, ...expected]) {
    const key = String(item?.key || '').trim()
    if (!key) continue
    byKey.set(key, { ...(byKey.get(key) || {}), ...item })
  }
  return Array.from(byKey.values()).map(item => ({
    key: item.key || '', label: item.label || '', unit: item.unit || '',
    baselineValue: item.baselineValue ?? '', targetValue: item.targetValue ?? '',
    measurementWindow: item.measurementWindow || '', source: item.source || '', direction: item.direction || '',
  }))
}
function emptyConfirmationDraft() {
  return {
    scope: '', scenarios: '', expected: '', evidence: '', exclusions: '',
    valueDefinition: {
      verificationMode: 'outcome', baselineSummary: '', expectedSummary: '', metricOwnerName: '', metricOwnerUserId: '',
      nonQuantifiableReason: '', metrics: [],
    },
  }
}
function emptySplitUnit(title = '', itemKind = 'feature') {
  return { title, itemKind, scope: '', acceptanceDelta: '', valueMetricKeys: [] }
}
function emptyTriageBranch(title = '', itemKind = 'feature', branchKey = '') {
  return { id: '', branchKey: branchKey || `work-item-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`, title, itemKind, scope: '', difference: '', relationToValue: 'shared', proposedPriority: '', dependency: '', formalRequirementId: '' }
}
function toggleTriageBranches() {
  if (!triageSplitEnabled.value) { triageBranches.value = []; return }
  if (triageBranches.value.length < 2) triageBranches.value = [emptyTriageBranch(selectedItem.value?.title || '', 'feature', 'work-item-1'), emptyTriageBranch('', 'feature', 'work-item-2')]
}
function addTriageBranch() { triageBranches.value.push(emptyTriageBranch('', 'feature', `work-item-${triageBranches.value.length + 1}`)) }
function removeTriageBranch(index: number) { if (triageBranches.value.length > 2) triageBranches.value.splice(index, 1) }
function toggleSplitUnits() {
  if (!conversion.value.splitEnabled) {
    conversion.value.splitUnits = []
    return
  }
  if (!Array.isArray(conversion.value.splitUnits) || conversion.value.splitUnits.length < 2) {
    conversion.value.splitUnits = [emptySplitUnit(conversion.value.title || '', conversion.value.itemKind || 'feature'), emptySplitUnit('', conversion.value.itemKind || 'feature')]
  }
}
function addSplitUnit() {
  if (!Array.isArray(conversion.value.splitUnits)) conversion.value.splitUnits = []
  conversion.value.splitUnits.push(emptySplitUnit('', conversion.value.itemKind || 'feature'))
}
function removeSplitUnit(index: number) {
  if (conversion.value.splitUnits.length <= 2) return
  conversion.value.splitUnits.splice(index, 1)
}
function confirmationMetricComplete(metric: any) {
  return !!String(metric?.key || '').trim()
    && !!String(metric?.label || '').trim()
    && !!String(metric?.unit || '').trim()
    && String(metric?.baselineValue ?? '').trim() !== ''
    && String(metric?.targetValue ?? '').trim() !== ''
    && !!String(metric?.measurementWindow || '').trim()
    && !!String(metric?.source || '').trim()
    && ['higher', 'lower'].includes(String(metric?.direction || ''))
}
function addConfirmationMetric(preset?: any) {
  const definition = confirmationDraft.value.valueDefinition
  if (!Array.isArray(definition.metrics)) definition.metrics = []
  const candidate = preset || { key: '', label: '', unit: '', direction: '', sourceHint: '', windowHint: '' }
  if (candidate.key && definition.metrics.some((metric: any) => metric.key === candidate.key)) return
  definition.metrics.push({
    key: candidate.key || '', label: candidate.label || '', unit: candidate.unit || '',
    baselineValue: '', targetValue: '', measurementWindow: candidate.windowHint || '',
    source: candidate.sourceHint || '', direction: candidate.direction || '',
  })
}
function removeConfirmationMetric(index: number) {
  confirmationDraft.value.valueDefinition.metrics.splice(index, 1)
}
function addValueMetric() {
  valueCardForm.value.metrics.push({ key: '', label: '', unit: '', baselineValue: '', targetValue: '', measurementWindow: '', source: '', direction: '' })
}
function removeValueMetric(index: number) { valueCardForm.value.metrics.splice(index, 1) }
function syncEvaluation(item: any) {
  evaluation.value = {
    decision: item?.evaluationDecision || '', requestType: item?.requestType || '',
    solutionType: item?.solutionType || '', intakePath: item?.intakePath || '',
    aiMode: item?.aiMode || 'none', aiScenario: item?.aiScenario || '',
    pocRequirement: item?.pocRequirement || 'none', impactScope: item?.impactScope || 'single_department',
    complexityLevel: item?.complexityLevel || 'medium', completeness: item?.completeness || 'complete',
    similarDemandId: item?.similarDemandId || '', nextAction: item?.nextAction || 'final_review',
    reason: item?.evaluationReason || '', notes: item?.evaluationNotes || '',
  }
  businessReviewReuse.value = {
    contactName: item?.requesterName || '', contactUserId: item?.requesterUserId || '',
    communicationDate: new Date().toISOString().slice(0, 10), source: '会议沟通',
    decision: 'support', prioritySuggestion: 'P2', summary: '',
  }
  const latestSupplement = item?.supplements?.[0]
  supplementAnswers.value = latestSupplement?.answers && typeof latestSupplement.answers === 'object' ? { ...latestSupplement.answers } : {}
  const latestPoc = item?.pocs?.[0]
  pocForm.value = latestPoc ? { goal: latestPoc.goal || '', baseline: latestPoc.baseline || '', scope: latestPoc.scope || '', testData: latestPoc.testData || '', successCriteria: latestPoc.successCriteria || '', ownerUserId: latestPoc.ownerUserId || '', ownerName: latestPoc.ownerName || '', dueDate: latestPoc.dueDate || '' } : { goal: '', baseline: '', scope: '', testData: '', successCriteria: '', ownerUserId: '', ownerName: '', dueDate: '' }
  const card = item?.valueCard
  valueCardForm.value = { ownerName: card?.ownerName || item?.requesterName || '', baselineSummary: card?.baseline?.summary || '', expectedSummary: card?.expected?.summary || '', day7Summary: card?.day7?.summary || '', day30Summary: card?.day30?.summary || '', targetMet: card?.targetMet || '', metrics: valueMetricRows(card) }
  const savedBranches = Array.isArray(item?.l3Branches) ? item.l3Branches.filter((branch: any) => branch.status !== 'removed') : []
  triageSplitEnabled.value = savedBranches.length > 0
  triageBranches.value = savedBranches.map((branch: any, index: number) => ({ id: branch.id || '', branchKey: branch.branchKey || `work-item-${index + 1}`, title: branch.title || '', itemKind: branch.itemKind || 'feature', scope: branch.scope || '', difference: branch.difference || '', relationToValue: branch.relationToValue || 'shared', proposedPriority: branch.proposedPriority || '', dependency: branch.dependency || '', formalRequirementId: branch.formalRequirementId || '' }))
  const decisionDraft: Record<string, any> = {}
  for (const branch of savedBranches) decisionDraft[branch.id] = { decision: branch.itDecision || '', reason: branch.itReason || '', notes: branch.itNotes || '' }
  branchDecisionDraft.value = decisionDraft
}
function syncConfirmationDraft(item: any) {
  const content = item?.confirmation?.content || {}
  const legacy = item?.confirmation || {}
  const card = item?.valueCard || {}
  const storedDefinition = content.valueDefinition && typeof content.valueDefinition === 'object' ? content.valueDefinition : {}
  const next: any = {
    scope: content.scope || legacy.usageScope || '',
    scenarios: content.scenarios || legacy.businessProcess || '',
    expected: content.expected || legacy.acceptanceCriteria || '',
    evidence: content.evidence || '',
    exclusions: content.exclusions || '',
    valueDefinition: {
       verificationMode: storedDefinition.verificationMode || (valueMetricRows(card).length ? 'quantitative' : 'outcome'),
      baselineSummary: storedDefinition.baselineSummary || card?.baseline?.summary || '',
      expectedSummary: storedDefinition.expectedSummary || card?.expected?.summary || '',
      metricOwnerName: storedDefinition.metricOwnerName || card?.ownerName || currentUser.value?.name || '',
      metricOwnerUserId: storedDefinition.metricOwnerUserId || card?.ownerUserId || currentUser.value?.userId || '',
      nonQuantifiableReason: storedDefinition.nonQuantifiableReason || '',
      metrics: Array.isArray(storedDefinition.metrics) ? storedDefinition.metrics.map((metric: any) => ({ ...metric })) : valueMetricRows(card),
    },
  }
  for (const field of deliveryStandardFields(normalizeDeliveryStandardType(item?.solutionType || evaluation.value.solutionType || 'custom'))) next[field.key] = content[field.key] || ''
  confirmationDraft.value = next
}
watch(selectedItem, syncEvaluation, { immediate: true })
watch(selectedItem, syncConfirmationDraft, { immediate: true })
function defaultConversionAssignee(item: any) {
  const candidates = [currentUser.value?.name, item?.requesterName].map(value => String(value || '').trim()).filter(Boolean)
  if (!candidates.length) return ''
  if (!developerOptions.value.length) return candidates[0]
  return candidates.find(name => developerOptions.value.some(person => samePersonName(person.name || '', name))) || ''
}
function syncConversion(item: any) {
  const suggestedType = item?.requestType === 'L3需求重构' ? '功能优化' : item?.requestType === '技术建设' ? '技术建设' : '新增功能'
  const suggestedSolutionType = normalizeLifecycleSolutionType(item?.solutionType || item?.demandSolutionType || evaluation.value.solutionType || '')
  const savedBranches = Array.isArray(item?.l3Branches) ? item.l3Branches.filter((branch: any) => branch.status !== 'removed') : []
  const savedSplitUnits = savedBranches.map((branch: any) => ({ branchId: branch.id || '', title: branch.title || '', itemKind: branch.itemKind || 'feature', scope: branch.scope || '', acceptanceDelta: branch.difference || '', valueMetricKeys: [] }))
  conversion.value = {
    mode: item?.intakeLevel === 'L2' ? 'create_l2' : (conversion.value.mode || 'create'), title: item?.title || '', projectName: item?.projectName || item?.title || '', projectId: item?.projectId || '', requirementId: '',
    solutionType: suggestedSolutionType, itemKind: 'feature', phaseTemplateKeys: [], type: suggestedType, priority: 'P2', assignee: defaultConversionAssignee(item), department: item?.department || '',
    expectedDeliveryTime: item?.expectedDeliveryTime || '', acceptanceCriteria: item?.confirmation?.content?.expected || item?.confirmation?.acceptanceCriteria || '', splitEnabled: savedSplitUnits.length >= 2, splitUnits: savedSplitUnits,
  }
  conversionError.value = ''
}
watch(selectedItem, syncConversion, { immediate: true })
watch([developerOptions, currentUser], () => {
  if (!conversion.value.assignee && selectedItem.value && conversion.value.mode !== 'link') conversion.value.assignee = defaultConversionAssignee(selectedItem.value)
}, { deep: true })
function syncConversionPhases() {
  const keys = conversionPhaseTemplates.value.map((phase: any) => phase.phaseKey).filter(Boolean)
  const current = Array.isArray(conversion.value.phaseTemplateKeys) ? conversion.value.phaseTemplateKeys : []
  if (!current.length || current.some((key: string) => !keys.includes(key))) conversion.value.phaseTemplateKeys = [...keys]
}
function setConversionMode(mode: string) {
  conversion.value.mode = mode
  conversion.value.requirementId = ''
  if (mode === 'create_l2') conversion.value.solutionType = normalizeLifecycleSolutionType(selectedItem.value?.solutionType || evaluation.value.solutionType || '')
  if (mode === 'create' && !conversion.value.projectId) conversion.value.projectId = selectedItem.value?.projectId || ''
  syncConversionPhases()
}
watch(() => [conversion.value.mode, conversion.value.solutionType, conversion.value.projectId], syncConversionPhases)
watch(lifecycleOptions, syncConversionPhases, { deep: true })
async function saveTriage() {
  if (!selectedItem.value || savingEvaluation.value) return
  if (!evaluation.value.solutionType) { alert('请先选择解决方案类型'); return }
  const branches = triageSplitEnabled.value ? triageBranches.value : []
  if (triageSplitEnabled.value && (branches.length < 2 || branches.some((branch: any) => !String(branch.title || '').trim() || !String(branch.itemKind || '').trim()))) { alert('独立 L3 工作项至少需要 2 个，并补齐每个工作项的标题和工作类型'); return }
  savingEvaluation.value = true
  const payload: any = {
    solutionType: evaluation.value.solutionType,
    intakePath: evaluation.value.intakePath,
    aiMode: evaluation.value.aiMode,
    aiScenario: evaluation.value.aiScenario,
    pocRequirement: evaluation.value.pocRequirement,
    impactScope: evaluation.value.impactScope,
    complexityLevel: evaluation.value.complexityLevel,
    completeness: evaluation.value.completeness,
    similarDemandId: evaluation.value.similarDemandId,
    nextAction: 'business_review',
  }
  if (selectedItem.value.status === 'pending_evaluation') payload.status = 'evaluating'
  const result: any = selectedItem.value.status === 'converted' ? selectedItem.value : await api.updateDemandPoolItem(selectedItem.value.id, payload)
  if (!result) { savingEvaluation.value = false; alert('IT 初筛保存失败，请检查需求类型和当前流程阶段'); return }
  let savedResult: any = result
  if (triageSplitEnabled.value) {
    const branchResult: any = selectedItem.value.status === 'converted'
      ? await api.historicalDecomposeDemandPool(selectedItem.value.id, { branches })
      : await api.saveDemandPoolDecomposition(selectedItem.value.id, { branches, requireMultiple: true, mode: 'triage' })
    if (!branchResult?.demand) { savingEvaluation.value = false; alert(branchResult?.error || '独立 L3 工作项保存失败'); return }
    savedResult = branchResult.demand
  }
  savingEvaluation.value = false
  const index = items.value.findIndex(item => item.id === result.id)
  if (index >= 0) items.value[index] = savedResult
  alert(selectedItem.value.status === 'converted' ? '历史独立 L3 工作项补录已保存，原流程未重跑' : 'IT 初筛与独立 L3 工作项已保存，下一步可发起业务评估')
}
async function saveDecision() {
  if (!selectedItem.value || savingEvaluation.value) return
  if (!evaluation.value.decision) { alert('请选择综合结论'); return }
  if (['defer', 'reject'].includes(evaluation.value.decision) && !evaluation.value.reason.trim()) { alert('暂缓或不承接时请填写综合判断说明'); return }
  const pendingReviews = Number(selectedItem.value.reviewSummary?.pending || 0)
  if (evaluation.value.decision === 'implement' && pendingReviews > 0) { alert('请等待所有业务评估完成后再形成实施结论'); return }
  if (evaluation.value.decision === 'implement' && evaluation.value.pocRequirement === 'required' && !selectedItem.value.pocs?.some((poc: any) => poc.status === 'completed' && ['passed', 'partial', 'continue', 'documented'].includes(poc.conclusion))) { alert('当前需求设置为“必须先完成 PoC”，请先登记并完成 PoC 验证'); return }
  if (selectedItem.value.l3Branches?.length && !branchDecisionsComplete.value) { alert('请逐项填写每个独立 L3 的 IT 结论；暂缓或不承接还需写明原因'); return }
  savingEvaluation.value = true
  const payload: any = {
    solutionType: evaluation.value.solutionType,
    intakePath: evaluation.value.intakePath,
    aiMode: evaluation.value.aiMode,
    aiScenario: evaluation.value.aiScenario,
    pocRequirement: evaluation.value.pocRequirement,
    impactScope: evaluation.value.impactScope,
    complexityLevel: evaluation.value.complexityLevel,
    completeness: evaluation.value.completeness,
    similarDemandId: evaluation.value.similarDemandId,
    nextAction: evaluation.value.decision === 'poc' ? 'poc_register' : 'final_review',
    evaluationDecision: evaluation.value.decision,
    evaluationReason: evaluation.value.reason,
    evaluationNotes: evaluation.value.notes,
  }
  const result: any = await api.updateDemandPoolItem(selectedItem.value.id, payload)
  if (!result) { savingEvaluation.value = false; alert('综合决策保存失败，请检查业务评估是否已完成及 PoC 策略'); return }
  let savedResult: any = result
  if (selectedItem.value.l3Branches?.length) {
    const branchResult: any = await api.saveDemandPoolBranchDecisions(selectedItem.value.id, { decisions: selectedItem.value.l3Branches.map((branch: any) => ({ branchId: branch.id, ...branchDecisionDraft.value[branch.id] })) })
    if (!branchResult?.demand) { savingEvaluation.value = false; alert(branchResult?.error || '独立 L3 决策保存失败'); return }
    savedResult = branchResult.demand
  }
  savingEvaluation.value = false
  const index = items.value.findIndex(item => item.id === result.id)
  if (index >= 0) items.value[index] = savedResult
  alert('IT 综合决策已保存' + (selectedItem.value.l3Branches?.length ? '，各独立 L3 已分别记录' : ''))
}
async function submitSupplement() {
  if (!selectedItem.value || savingSupplement.value) return
  savingSupplement.value = true
  const existing = selectedItem.value.supplements?.[0]
  let supplement: any = existing
  if (!supplement) supplement = await api.createDemandPoolSupplement(selectedItem.value.id, { solutionType: evaluation.value.solutionType, questions: templateQuestions.value })
  const result: any = supplement?.id ? await api.submitDemandPoolSupplement(supplement.id, supplementAnswers.value) : null
  savingSupplement.value = false
  if (!result) { alert('业务补充保存失败，请检查必填信息'); return }
  await load()
  alert('业务补充已提交，需求进入综合决策')
}
async function createPoc() {
  if (!selectedItem.value || creatingPoc.value) return
  creatingPoc.value = true
  const result: any = await api.createDemandPoolPoc(selectedItem.value.id, { ...pocForm.value })
  creatingPoc.value = false
  if (!result?.id) { alert('PoC 创建失败，请补齐验证目标、通过标准、负责人和时间'); return }
  await load()
  alert('PoC 验证记录已创建')
}
function openPocModal() {
  if (!selectedItem.value) return
  pocModalError.value = ''
  pocModalForm.value = { summary: '', artifactType: 'text', aiUsed: 'none', aiNotes: '' }
  pocModalFiles.value = []
  pocModalOpen.value = true
}
function closePocModal() {
  if (savingPocModal.value) return
  pocModalOpen.value = false
  pocModalError.value = ''
  pocModalFiles.value = []
}
function addPocModalFiles(incoming: File[]) {
  const accepted: File[] = []
  for (const file of incoming) {
    if (file.size > 50 * 1024 * 1024) { pocModalError.value = `附件「${file.name}」超过 50MB，未添加。`; continue }
    if (!pocModalFiles.value.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) accepted.push(file)
  }
  if (accepted.length) { pocModalFiles.value.push(...accepted); pocModalError.value = '' }
}
function removePocModalFile(index: number) { pocModalFiles.value.splice(index, 1) }
async function submitPocModal() {
  if (!selectedItem.value || savingPocModal.value) return
  const summary = String(pocModalForm.value.summary || '').trim()
  if (!summary) { pocModalError.value = '请至少填写一段验证结论或步骤规划。'; return }
  savingPocModal.value = true
  pocModalError.value = ''
  const result: any = await api.createDemandPoolPoc(selectedItem.value.id, { summary, artifactType: pocModalForm.value.artifactType, aiUsed: pocModalForm.value.aiUsed, aiNotes: pocModalForm.value.aiNotes })
  if (!result?.id) { savingPocModal.value = false; pocModalError.value = result?.error || '验证记录保存失败，请检查当前账号和需求阶段。'; return }
  const failed: string[] = []
  for (const file of pocModalFiles.value) if (!await api.uploadBusinessAttachment('demand_pool_poc', result.id, file)) failed.push(file.name)
  await load()
  savingPocModal.value = false
  pocModalOpen.value = false
  pocModalFiles.value = []
  alert(failed.length ? `验证记录已保存，但附件上传失败：${failed.join('、')}` : '验证记录已保存')
}
async function completePoc(conclusion: string) {
  const poc = selectedItem.value?.pocs?.[0]
  if (!poc || updatingPoc.value) return
  updatingPoc.value = true
  const result: any = await api.updateDemandPoolPoc(poc.id, { status: 'completed', conclusion, result: poc.result || '' })
  updatingPoc.value = false
  if (!result?.id) { alert('PoC 更新失败'); return }
  await load()
  alert('PoC 结果已保存')
}
async function saveValueCard() {
  if (!selectedItem.value || savingValueCard.value) return
  savingValueCard.value = true
  const formValue = valueCardForm.value
  const metrics = (Array.isArray(formValue.metrics) ? formValue.metrics : []).map((item: any) => ({
    key: String(item.key || '').trim(), label: String(item.label || '').trim(), unit: String(item.unit || '').trim(),
    baselineValue: item.baselineValue, targetValue: item.targetValue, measurementWindow: String(item.measurementWindow || '').trim(),
    source: String(item.source || '').trim(), direction: String(item.direction || '').trim(),
  })).filter((item: any) => item.key && (item.baselineValue !== '' || item.targetValue !== ''))
  const hasAnyValue = [formValue.baselineSummary, formValue.expectedSummary, formValue.day7Summary, formValue.day30Summary, formValue.targetMet].some(value => String(value || '').trim()) || metrics.length > 0
  if (!hasAnyValue) { savingValueCard.value = false; alert('请至少记录一项成果信息；如果当前无需验证，可以先不创建记录。'); return }
  const baseline = { summary: formValue.baselineSummary, ...(metrics.length ? { metrics } : {}) }
  const expected = { summary: formValue.expectedSummary, ...(metrics.length ? { metrics } : {}) }
  const result: any = await api.saveDemandPoolValueCard(selectedItem.value.id, { baseline, expected, day7: { summary: formValue.day7Summary }, day30: { summary: formValue.day30Summary }, targetMet: formValue.targetMet, ownerName: formValue.ownerName || selectedItem.value.requesterName || currentUser.value.name || '' })
  savingValueCard.value = false
  if (!result?.id) { alert(result?.error || '成果记录保存失败，请检查当前需求类型和必填目标'); return }
  await load()
  alert('成果验证记录已保存')
}
async function createOutcomeRequest(stage: string) {
  if (!selectedItem.value || creatingOutcomeRequest.value || !valueCardForm.value.ownerName) return
  creatingOutcomeRequest.value = true
  const recipient = contactByName(valueCardForm.value.ownerName)
  const scheduledAt = stage === 'day7' || stage === 'day30' ? new Date(Date.now() + (stage === 'day7' ? 7 : 30) * 86400000).toISOString().slice(0, 19).replace('T', ' ') : ''
  const result: any = await api.createDemandPoolOutcomeRequest(selectedItem.value.id, { stage, recipientName: valueCardForm.value.ownerName, recipientUserId: recipient.userId || recipient.userid || recipient.dingUserId || '', sendNow: !scheduledAt, scheduledAt })
  creatingOutcomeRequest.value = false
  if (!result?.id) { alert(result?.error || '成果回访链接生成失败'); return }
  await load()
  alert(`${result.stageLabel || '成果回访'}${scheduledAt ? '已安排，系统将在到期时自动发送' : '链接已生成'}${result.notificationStatus === 'failed' ? '，但钉钉发送失败，可复制链接手动发送' : ''}`)
}
function openMaterialsNotify() {
  if (!selectedItem.value) return
  showNotify.value = true
  notifyForm.value.entryMode = 'materials'
  notifyForm.value.demandId = selectedItem.value.id
  void loadContacts()
}
function contactByName(name: string) { return contactUsers.value.find(person => samePersonName(person.name || '', name || '')) || {} }
function samePersonName(left: string, right: string) { return String(left || '').trim().toLowerCase() === String(right || '').trim().toLowerCase() }
function contactById(id: string) { return contactUsers.value.find(person => (person.userId || person.userid || person.dingUserId) === id) || {} }
async function loadContacts(force = false) {
  if (contactsRequest) return contactsRequest
  if (contactsLoaded.value && !force) return contactsLoaded.value
  contactsLoading.value = true
  contactsRequest = api.getDingTalkOptions().then((contacts: any) => {
    departmentOptions.value = Array.isArray(contacts?.departments) ? contacts.departments : []
    developerOptions.value = Array.isArray(contacts?.developers) ? contacts.developers : []
    contactUsers.value = Array.isArray(contacts?.users) ? contacts.users : []
    contactsLoaded.value = !!contacts && typeof contacts === 'object'
    return contacts
  }).catch(() => {
    contactsLoaded.value = false
    return null
  }).finally(() => {
    contactsLoading.value = false
    contactsRequest = null
  })
  return contactsRequest
}
async function assignReviews() {
  if (!selectedItem.value || assigningReviews.value || !canAssignReviews.value) return
  assigningReviews.value = true
  const reviewers: any[] = []
  if (reviewAssignment.value.leaderUserId) { const person = contactById(reviewAssignment.value.leaderUserId); reviewers.push({ role: 'leader', userId: reviewAssignment.value.leaderUserId, name: person.name || '' }) }
  if (reviewAssignment.value.departmentUserId && reviewAssignment.value.departmentUserId !== reviewAssignment.value.leaderUserId) { const person = contactById(reviewAssignment.value.departmentUserId); reviewers.push({ role: 'department_owner', userId: reviewAssignment.value.departmentUserId, name: person.name || '' }) }
  const result: any = await api.assignDemandPoolReviews(selectedItem.value.id, { reviewers })
  assigningReviews.value = false
  if (!result?.demand) { alert(result?.error || '业务评估链接发送失败，请确认联系人和权限'); return }
  const index = items.value.findIndex(item => item.id === result.demand.id)
  if (index >= 0) items.value[index] = result.demand
  alert(result.createdCount ? `已发起 ${result.createdCount} 个业务评估` : '所选评估人已有待处理评估，无需重复发送')
}
async function reuseBusinessReview() {
  if (!selectedItem.value || reusingBusinessReview.value) return
  reuseBusinessReviewError.value = ''
  const missing: string[] = []
  if (!selectedItem.value.solutionType) missing.push('先完成 IT 初筛')
  if (!String(businessReviewReuse.value.contactName || '').trim()) missing.push('已有沟通确认人')
  if (!String(businessReviewReuse.value.communicationDate || '').trim()) missing.push('沟通日期')
  if (!businessReviewReuse.value.decision) missing.push('业务判断')
  if (!businessReviewReuse.value.prioritySuggestion) missing.push('优先级')
  if (!String(businessReviewReuse.value.summary || '').trim()) missing.push('沟通结论摘要')
  if (missing.length) {
    reuseBusinessReviewError.value = `请先补充：${missing.join('、')}`
    return
  }
  reusingBusinessReview.value = true
  const contact = contactByName(businessReviewReuse.value.contactName)
  const result: any = await api.reuseDemandPoolBusinessReview(selectedItem.value.id, {
    contactName: businessReviewReuse.value.contactName,
    contactUserId: contact.userId || contact.userid || contact.dingUserId || businessReviewReuse.value.contactUserId || '',
    communicationDate: businessReviewReuse.value.communicationDate,
    source: businessReviewReuse.value.source,
    decision: businessReviewReuse.value.decision,
    prioritySuggestion: businessReviewReuse.value.prioritySuggestion,
    summary: businessReviewReuse.value.summary,
  })
  reusingBusinessReview.value = false
  if (!result?.demand || result?._failed) { reuseBusinessReviewError.value = result?.error || '复用已有业务沟通失败，请检查当前阶段和填写内容'; return }
  const index = items.value.findIndex(item => item.id === result.demand.id)
  if (index >= 0) items.value[index] = result.demand
  await nextTick()
  document.getElementById('demand-pool-decision-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  alert('已复用已有业务沟通，未发送新的业务评估通知；现在可以进入 IT 综合决策')
}
async function sendNotify() {
  if (sendingNotify.value) return
  notifyError.value = ''
  if (notifyForm.value.targetType === 'person' && !notifyForm.value.targetUserId) { notifyError.value = '请选择接收人'; return }
  if (notifyForm.value.targetType === 'department' && !notifyForm.value.targetValue) { notifyError.value = '请选择接收部门'; return }
  if (notifyForm.value.entryMode === 'collect' && notifyForm.value.scheduleCycle !== 'once' && !notifyForm.value.scheduleTime) { notifyError.value = '请选择定期发送时间'; return }
  sendingNotify.value = true
  const person = notifyForm.value.targetUserId ? contactById(notifyForm.value.targetUserId) : {}
  if (notifyForm.value.entryMode === 'collect' && notifyForm.value.scheduleCycle === 'custom' && !notifyForm.value.scheduleWeekdays?.length) { notifyError.value = '请选择至少一个发送日'; sendingNotify.value = false; return }
  const requestKey = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `collection-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const result: any = await api.sendDemandPoolNotification({ requestKey, entryMode: notifyForm.value.entryMode, demandId: notifyForm.value.entryMode === 'materials' ? notifyForm.value.demandId : '', targetType: notifyForm.value.targetType, targetValue: notifyForm.value.targetType === 'person' ? (person.name || '') : notifyForm.value.targetValue, targetUserId: notifyForm.value.targetUserId, message: notifyForm.value.message, scheduleCycle: notifyForm.value.entryMode === 'collect' ? notifyForm.value.scheduleCycle : 'once', scheduleTime: notifyForm.value.scheduleTime, scheduleDay: notifyForm.value.scheduleDay, scheduleWeekdays: notifyForm.value.scheduleWeekdays })
  sendingNotify.value = false
  if (!result?.id) { notifyError.value = '发送失败，请检查联系人或钉钉配置'; return }
  const failedNames = (result.failureDetails || []).map((item: any) => item.name || item.userId || '未知接收人').slice(0, 8).join('、')
  if (result.status === 'failed') { notifyError.value = `本次没有确认成功的发送结果，请勿立即重复发送。${failedNames ? `失败人员：${failedNames}。` : ''}${result.error || '请检查钉钉联系人和机器人配置。'}`; return }
  if (result.status === 'attention_required') { notifyError.value = `通知存在结果不确定的接收人，系统未自动补发，请打开批次确认后再处理。${failedNames ? `相关人员：${failedNames}。` : ''}`; await loadNotifications(); await loadCollectionBatches(); return }
  notifyForm.value = { ...notifyForm.value, targetUserId: '', demandId: '', message: '' }
  await loadNotifications()
  if (notifyForm.value.entryMode === 'collect') await loadCollectionBatches()
  if (result.status === 'partial') { notifyError.value = `通知已部分发送：成功 ${result.successCount} 人，失败 ${result.failureCount} 人。已有消息可能已经送达，请勿重复发送。${failedNames ? `失败人员：${failedNames}。` : ''}`; return }
  alert(result.status === 'scheduled' ? '征集计划已保存，系统会按设定时间自动发送' : `钉钉已受理 ${result.successCount} 人的发送请求`)
}
async function openCollectionManager() {
  if (!canManage.value) return
  collectionManagerOpen.value = true
  collectionConfigOpen.value = true
  notifyForm.value.entryMode = 'collect'
  selectedCollectionBatch.value = null
  selectedCollectionResponse.value = null
  void loadContacts()
  await loadCollectionBatches()
}
function closeCollectionManager() {
  if (judgingCollection.value) return
  collectionManagerOpen.value = false
  selectedCollectionBatch.value = null
  selectedCollectionResponse.value = null
}
function configureCollection() {
  collectionManagerOpen.value = true
  collectionConfigOpen.value = true
  notifyForm.value.entryMode = 'collect'
  notifyForm.value.demandId = ''
  notifyError.value = ''
  void loadContacts()
}
async function loadCollectionBatches() {
  if (!canManage.value) return
  collectionLoading.value = true
  const rows: any = await api.getDemandCollectionBatches()
  if (Array.isArray(rows)) collectionBatches.value = rows
  collectionLoading.value = false
}
async function openCollectionBatch(batchId: string) {
  const batch: any = await api.getDemandCollectionBatch(batchId)
  if (!batch?.id) { alert(batch?.error || '批次读取失败，请刷新重试'); return }
  selectedCollectionBatch.value = batch
  selectedCollectionResponse.value = batch.responses?.[0] || null
  if (selectedCollectionResponse.value) selectCollectionResponse(selectedCollectionResponse.value)
}
async function retryCollectionFailures() {
  if (!selectedCollectionBatch.value?.id || collectionRetrying.value) return
  if (!window.confirm('只补发本批次明确失败且确认未受理的人员；已受理和结果不确定人员不会补发。继续吗？')) return
  collectionRetrying.value = true
  const result: any = await api.retryDemandCollectionFailures(selectedCollectionBatch.value.id)
  collectionRetrying.value = false
  if (!result?.batch) { alert(result?.error || '补发失败，请稍后重试'); return }
  selectedCollectionBatch.value = result.batch
  if (result.failureCount) alert(`补发完成：本次受理 ${result.successCount || 0} 人，仍失败 ${result.failureCount} 人`)
  else alert(`补发完成：本次受理 ${result.successCount || 0} 人`)
  await loadCollectionBatches()
}
function selectCollectionResponse(response: any) {
  selectedCollectionResponse.value = response
  collectionJudgment.value = {
    judgment: response.judgment === 'pending' ? '' : response.judgment || '',
    judgmentReason: response.judgmentReason || '',
    similarDemandId: response.similarDemandId || '',
    nextAction: response.nextAction || '',
  }
}
function openCollectionLinkedDemand() {
  const demandId = selectedCollectionResponse.value?.convertedDemandId || selectedCollectionResponse.value?.convertedDemand?.id
  if (!demandId) return
  selectedId.value = demandId
  collectionManagerOpen.value = false
}
async function judgeCollectionResponse() {
  if (!selectedCollectionResponse.value || judgingCollection.value || !collectionJudgmentReady.value) return
  judgingCollection.value = true
  const result: any = await api.judgeDemandCollectionResponse(selectedCollectionResponse.value.id, { ...collectionJudgment.value })
  judgingCollection.value = false
  if (!result?.id) { alert(result?.error || '判断保存失败，请重试'); return }
  selectedCollectionResponse.value = result
  if (selectedCollectionBatch.value?.responses) {
    const index = selectedCollectionBatch.value.responses.findIndex((item: any) => item.id === result.id)
    if (index >= 0) selectedCollectionBatch.value.responses[index] = result
  }
  await loadCollectionBatches()
  alert(result.convertedDemandId ? (result.judgment === 'duplicate' ? '已保存判断，并已关联已有需求' : '已保存判断，并已转入正式需求池待 IT 评估') : '已保存 IT 判断')
}
async function loadNotifications() { if (!canManage.value) return; const rows: any = await api.getDemandPoolNotifications(); if (Array.isArray(rows)) demandNotifications.value = rows }
async function toggleNotification(plan: any) { const result: any = await api.updateDemandPoolNotification(plan.id, { enabled: !plan.enabled }); if (!result) { alert('计划状态更新失败'); return }; const index = demandNotifications.value.findIndex(item => item.id === plan.id); if (index >= 0) demandNotifications.value[index] = result }
async function createConfirmation() {
  if (!selectedItem.value || creatingConfirmation.value || !canCreateConfirmation.value) return
  creatingConfirmation.value = true
  const result: any = await api.createDemandPoolConfirmation(selectedItem.value.id, { recipientUserId: selectedItem.value.requesterUserId, recipientName: selectedItem.value.requesterName, templateType: confirmationTemplateType.value, content: { ...confirmationDraft.value, valueDefinition: { ...confirmationDraft.value.valueDefinition, verificationMode: confirmationDraft.value.valueDefinition.verificationMode || 'outcome', metricOwnerName: confirmationDraft.value.valueDefinition.metricOwnerName || currentUser.value?.name || '', metricOwnerUserId: confirmationDraft.value.valueDefinition.metricOwnerUserId || currentUser.value?.userId || '', metrics: confirmationDraft.value.valueDefinition.metrics.map((metric: any) => ({ ...metric })) } } })
  creatingConfirmation.value = false
  if (!result?.link) { alert(result?.error || '交付与价值确认链接生成失败，请检查评估状态'); return }
  confirmationDraft.value = emptyConfirmationDraft()
  await load()
  alert('交付与价值确认单已保存，请核对内容后发送给业务确认')
}
async function resendConfirmation() {
  if (!selectedItem.value || resendingConfirmation.value || selectedItem.value.confirmation?.status !== 'pending') return
  resendingConfirmation.value = true
  const result: any = await api.resendDemandPoolConfirmation(selectedItem.value.id)
  resendingConfirmation.value = false
  if (!result?.demandId) { alert(result?.error || '确认链接发送失败'); return }
  await load()
  if (result.notificationStatus === 'success') alert(`确认链接已发送给${result.recipientName || '业务负责人'}`)
  else alert(`确认链接已生成，但发送失败：${result.notificationError || '未知原因'}，可复制链接手动发送`)
}
async function deleteDemand(item: any) {
  if (!item?.id) return
  if (!window.confirm(`确定删除提报「${item.title}」？删除后会移入回收站。`)) return
  const result: any = await api.deleteDemandPoolItem(item.id)
  if (!result?.ok) { alert('删除失败，请确认这是你自己创建的提报'); return }
  const index = items.value.findIndex(row => row.id === item.id)
  if (index >= 0) items.value.splice(index, 1)
  selectedId.value = items.value[0]?.id || ''
  alert('提报已移入回收站')
}
async function copyConfirmationLink(link: string) {
  if (!link) return
  try { await navigator.clipboard.writeText(link); alert('链接已复制') } catch { alert(link) }
}
async function convert() {
  if (!selectedItem.value || converting.value) return
  conversionError.value = ''
  if (conversion.value.mode === 'create') {
    if (conversion.value.splitEnabled) {
      const units = Array.isArray(conversion.value.splitUnits) ? conversion.value.splitUnits : []
      if (units.length < 2 || units.some((unit: any) => !String(unit?.title || '').trim() || !String(unit?.itemKind || '').trim())) { conversionError.value = '创建多个独立 L3 时，至少保留 2 个，并补齐每个工作项的标题和工作类型'; return }
    } else if (!conversion.value.title) { conversionError.value = '请补充 L3 标题'; return }
    if (!conversion.value.projectId || (!conversion.value.splitEnabled && !conversion.value.itemKind) || !conversion.value.assignee || !conversion.value.expectedDeliveryTime) { conversionError.value = '请补充归属 L2、工作类型、开发负责人和预计交付时间'; return }
  } else if (conversion.value.mode === 'create_l2') {
    if (!conversion.value.projectName || !conversion.value.solutionType || !conversion.value.assignee || !conversion.value.expectedDeliveryTime) { conversionError.value = '请补充 L2 名称、L2 类型、项目负责人和目标结束时间'; return }
  } else if (!conversion.value.projectId || !conversion.value.requirementId) { conversionError.value = '请先选择归属 L2，再选择该 L2 下的已有 L3'; return }
  converting.value = true
  const payload = { ...conversion.value, parallelL3s: conversion.value.mode === 'create' && conversion.value.splitEnabled ? conversion.value.splitUnits.map((unit: any) => ({ ...unit })) : [], units: [], devOwner: conversion.value.assignee, projectOwner: conversion.value.assignee, projectEndDate: conversion.value.expectedDeliveryTime }
  const result: any = await api.convertDemandPool(selectedItem.value.id, payload)
  converting.value = false
  if (!result?.demand) { conversionError.value = result?.error || '正式创建或关联失败，请检查字段和权限'; return }
  const index = items.value.findIndex(item => item.id === result.demand.id)
  if (index >= 0) items.value[index] = result.demand
  selectedId.value = result.demand.id
  const createdLabel = result.requirementIds?.length > 1 ? `L2 下新建 ${result.requirementIds.length} 个 L3` : (conversion.value.mode === 'create_l2' ? 'L2 + 初始建设 L3 创建' : conversion.value.mode === 'create' ? 'L2 下新建 L3' : '关联已有 L3')
  alert(`已完成${createdLabel}：${result.requirementTitle || result.requirementId}`)
  if (result.requirementId) router.push('/requirements/' + result.requirementId)
}
async function load() {
  loading.value = true
  const [options, rows, projectRows, requirementRows, lifecycle] = await Promise.all([api.getDemandPoolOptions(), api.getDemandPool(), api.getProjects(), api.getRequirements({}), api.getProjectLifecycleOptions()])
  if (options) { statusOptions.value = options.statuses || []; decisionOptions.value = options.decisions || []; if (options.priorities?.length) priorityOptions.value = options.priorities; if (options.intakeLevels?.length) intakeLevelOptions.value = options.intakeLevels; solutionTypeOptions.value = options.solutionTypes || []; aiOptions.value = options.aiModes || []; pocOptions.value = options.pocRequirements || []; impactScopeOptions.value = options.impactScopes || []; complexityOptions.value = options.complexityLevels || []; nextActionOptions.value = options.nextActions || []; templates.value = options.templates || {} }
  if (Array.isArray(rows)) { items.value = rows; if (!selectedId.value && rows.length) selectedId.value = rows[0].id }
  if (Array.isArray(projectRows)) projects.value = projectRows
  if (Array.isArray(requirementRows)) requirements.value = requirementRows
  if (lifecycle) lifecycleOptions.value = lifecycle
  syncConversionPhases()
  void loadContacts(true)
  void loadNotifications()
  loading.value = false
}
function statusClass(status: string) {
  if (['converted', 'business_confirmed'].includes(status)) return 'rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-600'
  if (['poc', 'awaiting_confirmation', 'ready_for_l3'].includes(status)) return 'rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-semibold text-violet-600'
  if (['deferred', 'not_implemented'].includes(status)) return 'rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-semibold text-gray-500'
  if (['evaluating', 'business_review', 'review_complete', 'awaiting_supplement'].includes(status)) return 'rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600'
  return 'rounded bg-rose-50 px-1.5 py-0.5 text-[10px] font-semibold text-rose-600'
}
function valueCardStatusLabel(status: string) {
  return ({ draft: '草稿', baseline_ready: '已记录目标', day7_review: '3 天观察中', completed: '已完成' } as Record<string, string>)[status] || status || '草稿'
}
function reviewPriorityLabel(value: string) {
  return ({ P0: '现在处理', P1: '近期处理', P2: '计划内处理', P3: '暂缓' } as Record<string, string>)[value] || value || '未填写'
}
function shortDate(value: string) { return String(value || '').slice(0, 10) }
async function downloadAttachment(attachment: any) {
  const blob = await api.getBusinessAttachmentBlob(attachment.id)
  if (!blob) { alert('附件读取失败，请刷新后重试'); return }
  const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = attachment.originalName || 'attachment'; link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 30000)
}
onMounted(async () => { readUser(); await load() })
return { route, router, currentUser, items, projects, requirements, developerOptions, contactUsers, departmentOptions, contactsLoading, contactsLoaded, contactsRequest, statusOptions, decisionOptions, priorityOptions, businessReviewDecisionOptions, reviewPriorityOptions, intakeLevelOptions, solutionTypeOptions, impactScopeOptions, complexityOptions, aiOptions, pocOptions, nextActionOptions, templates, lifecycleOptions, activeStatus, selectedId, showForm, showNotify, loading, saving, savingEvaluation, triageSplitEnabled, triageBranches, branchDecisionDraft, assigningReviews, reusingBusinessReview, reuseBusinessReviewError, sendingNotify, creatingConfirmation, resendingConfirmation, confirmationDraft, converting, savingSupplement, creatingPoc, updatingPoc, savingValueCard, creatingOutcomeRequest, pocModalOpen, savingPocModal, formError, conversionError, uploadError, notifyError, pocModalError, files, pocModalFiles, form, evaluation, confirmationTemplateType, confirmationTemplateLabel, confirmationTemplateFields, confirmationMetricPresets, confirmationFieldsFor, canCreateConfirmation, supplementAnswers, pocForm, pocModalForm, valueCardForm, reviewAssignment, businessReviewReuse, notifyForm, demandNotifications, collectionManagerOpen, collectionConfigOpen, collectionLoading, collectionRetrying, collectionBatches, selectedCollectionBatch, selectedCollectionResponse, judgingCollection, collectionJudgment, conversion, filteredItems, selectedItem, collectionLinkCandidates, collectionJudgmentReady, canSubmit, canManage, branchDecisionsComplete, canAssignReviews, canReuseBusinessReview, demandEntryLink, pocEntryLink, templateQuestions, lifecycleSolutionTypeOptions, l3ItemKindOptions, solutionTypeAlias, normalizeLifecycleSolutionType, conversionProject, conversionSolutionType, conversionPhaseTemplates, conversionRequirements, conversionModeHelp, valuePolicy, outcomeStageOptions, summaryCards, lifecycleStages, lifecycleStageLabel, lifecycleStageClass, decisionLabelFor, solutionTypeLabelFor, readUser, addFiles, removeFile, handlePaste, uploadPending, submit, valueMetricRows, emptyConfirmationDraft, emptySplitUnit, emptyTriageBranch, toggleTriageBranches, addTriageBranch, removeTriageBranch, toggleSplitUnits, addSplitUnit, removeSplitUnit, confirmationMetricComplete, addConfirmationMetric, removeConfirmationMetric, addValueMetric, removeValueMetric, syncEvaluation, syncConfirmationDraft, defaultConversionAssignee, syncConversion, syncConversionPhases, setConversionMode, saveTriage, saveDecision, submitSupplement, createPoc, openPocModal, closePocModal, addPocModalFiles, removePocModalFile, submitPocModal, completePoc, saveValueCard, createOutcomeRequest, openMaterialsNotify, contactByName, samePersonName, contactById, loadContacts, assignReviews, reuseBusinessReview, sendNotify, openCollectionManager, closeCollectionManager, configureCollection, loadCollectionBatches, openCollectionBatch, retryCollectionFailures, selectCollectionResponse, openCollectionLinkedDemand, judgeCollectionResponse, loadNotifications, toggleNotification, createConfirmation, resendConfirmation, deleteDemand, copyConfirmationLink, convert, load, statusClass, valueCardStatusLabel, reviewPriorityLabel, shortDate, downloadAttachment }
}
