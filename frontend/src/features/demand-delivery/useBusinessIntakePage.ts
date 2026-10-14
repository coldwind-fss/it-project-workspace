import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/application-api'
import { CheckCircle2, Clock3, Inbox, ShieldCheck } from 'lucide-vue-next'
export function useBusinessIntakePage() {


type ViewKey = 'mine' | 'pending' | 'all'
type SummaryFocus = 'all' | 'active' | 'pending' | 'completed'
type ModalKey = '' | 'demand' | 'matter' | 'detail' | 'activity' | 'feedback'
const route = useRoute()
const currentUser = ref<any>({}), projects = ref<any[]>([]), requirements = ref<any[]>([]), demandPool = ref<any[]>([]), requests = ref<any[]>([]), collaborations = ref<any[]>([]), postlaunchRows = ref<any[]>([]), departments = ref<string[]>([]), activities = ref<any[]>([]), todos = ref<any[]>([])
const loading = ref(false), saving = ref(false), activeView = ref<ViewKey>('mine'), summaryFocus = ref<SummaryFocus>('all'), keyword = ref(''), stageFilter = ref('all'), modal = ref<ModalKey>(''), selectedItem = ref<any>(null), selectedLifecycleStep = ref(''), activityScopeType = ref<'project' | 'requirement'>('requirement'), activityScopeId = ref(''), feedbackDetail = ref<any>(null), pendingFiles = ref<File[]>([]), toast = ref(''), expandedGroups = ref<Record<string, boolean>>({})
const previewUrls = new Map<File, string>()
const demandForm = ref<any>({ title: '', projectId: '', department: '', businessUrgency: 'normal', expectedDeliveryTime: '', description: '', requesterName: '' })
const matterForm = ref<any>({ requirementId: '', kind: 'business_feedback', title: '', content: '', dueDate: '', recipientName: '', recipientUserId: '' })
const lifecycleSteps = ['需求池待评估', '业务确认', 'IT 综合决策', '正式立项', '开发中', '待业务验收', '已上线', '3 天回执', '30 天价值验证']
const lifecycleDescriptions: Record<string, string> = {
  '需求池待评估': '需求已登记，等待 IT 完成初筛、归类和范围判断。',
  '业务确认': '业务人员确认问题、目标和优先级，为 IT 综合决策提供依据。',
  'IT 综合决策': 'IT 汇总需求、资源和风险，决定实施、暂缓或不承接。',
  '正式立项': '已明确负责人、计划和交付边界，进入正式 L2/L3 建设。',
  '开发中': '开发工作台正在推进设计、开发、联调或测试工作。',
  '待业务验收': 'IT 已准备交付，等待业务确认上线前交付范围和验收标准。',
  '已上线': '交付已确认并完成上线登记，进入实际使用阶段。',
  '3 天回执': '上线后约 3 天收集使用情况和交付回执。',
  '30 天价值验证': '上线后约 30 天回看目标达成和实际业务价值。',
}
const viewTabs = [{ key: 'mine' as ViewKey, label: '我的需求' }, { key: 'pending' as ViewKey, label: '待我处理' }, { key: 'all' as ViewKey, label: '全部相关' }]
const stageOptions = lifecycleSteps

function readUser() { try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} }; demandForm.value.requesterName = currentUser.value.name || ''; demandForm.value.department = currentUser.value.department || '' }
function isLeader() { const role = String(currentUser.value.role || currentUser.value.accessRole || '').toLowerCase(); return ['admin', 'super_admin', 'editor', 'leader', 'business_leader', 'manager'].includes(role) || !!currentUser.value.isManager }
function samePerson(...names: any[]) { const mine = String(currentUser.value.name || currentUser.value.nickName || '').trim(); const mineId = String(currentUser.value.userId || currentUser.value.id || '').trim(); return names.some(value => { const text = String(value || '').trim(); return !!text && ((mine && text.includes(mine)) || (mineId && text === mineId)) }) }
function feedbackFor(item: any) { return postlaunchRows.value.find(row => (item.requirementId && String(row.requirementId) === String(item.requirementId)) || (item.projectId && String(row.projectId) === String(item.projectId))) }
function stageForDemand(item: any) { const status = String(item.status || ''); if (item.requirementId || status === 'converted') return '正式立项'; if (['business_confirmed', 'ready_for_l3'].includes(status)) return 'IT 综合决策'; if (['business_review', 'awaiting_confirmation'].includes(status)) return '业务确认'; return '需求池待评估' }
function stageForRequirement(item: any) { const status = String(item.status || ''); if (['已上线', '已交付', '维护中', '已关闭'].includes(status)) return '已上线'; if (['进行中', '开发中'].includes(status)) return '开发中'; if (['待验收', '业务验收'].includes(status)) return '待业务验收'; return '正式立项' }
function stageForProject(item: any) { const status = String(item.status || ''); if (['已上线', '维护中', '已交付'].includes(status)) return '已上线'; if (['进行中', '开发中'].includes(status)) return '开发中'; return '正式立项' }
function progressFor(stage: string, sourceType: string) { const index = lifecycleSteps.indexOf(stage); if (index < 0) return sourceType === 'demand' ? 8 : 25; return Math.round(((index + 1) / lifecycleSteps.length) * 100) }
function safeProgress(value: any, fallback: number) { const parsed = Number(value); return Number.isFinite(parsed) ? Math.min(100, Math.max(0, Math.round(parsed))) : fallback }
function activityTimestamp(row: any) { return row?.createdAt || row?.updatedAt || row?.activityCreatedAt || '' }
function latestActivityFor(item: any) {
  const candidates = activities.value.filter(row => {
    if (item.requirementId && String(row.requirementId || '') === String(item.requirementId)) return true
    return Boolean(item.projectId && String(row.projectId || '') === String(item.projectId))
  }).sort((a, b) => String(activityTimestamp(b)).localeCompare(String(activityTimestamp(a))))
  const row = candidates[0]
  if (row) {
    const field = row.fieldName || row.changeType || row.activityTypeLabel || row.activityType || '动态更新'
    const title = row.fieldName === 'status' ? `阶段变更为 ${row.newValue || row.status || item.stage}` : row.title || field
    const content = row.reason || row.content || row.newValue || row.message || ''
    return { title: String(title), content: String(content), at: activityTimestamp(row), actor: row.operator || row.actorName || '' }
  }
  return { title: `当前阶段：${item.stage}`, content: item.description || '暂无新的动态', at: item.updatedAt || '', actor: '' }
}
function latestActivityText(item: any) {
  const activity = item.latestActivity || latestActivityFor(item)
  const content = String(activity.content || '').trim().replace(/\s+/g, ' ')
  const text = content ? `${activity.title} · ${content}` : activity.title
  return activity.at ? `${text}（${formatDate(activity.at)}）` : text
}
function activeTodoFor(item: any) {
  return todos.value.find(todo => todo.status !== 'done' && ((item.requirementId && String(todo.requirementId || '') === String(item.requirementId)) || (item.projectId && String(todo.projectId || '') === String(item.projectId)))) || null
}
function todoActionFor(todo: any) {
  if (!todo) return { pendingAction: '', actionLabel: '' }
  if (todo.type === 'shared_activity') return { pendingAction: '有新的产品动态', actionLabel: '查看动态' }
  if (todo.type === 'business_collaboration') return { pendingAction: '待处理协作', actionLabel: '去处理' }
  return { pendingAction: '待处理事项', actionLabel: '去处理' }
}
function feedbackRecipient(entry: any, row: any) { const userId = String(currentUser.value.userId || currentUser.value.id || '').trim(); return Boolean((userId && entry.recipientUserId && String(entry.recipientUserId) === userId) || samePerson(entry.recipientName, row.businessOwnerName)) }
function itemMatchesPerson(item: any) { return samePerson(item?.requesterName, item?.ownerName, item?.raw?.businessOwner, item?.raw?.requester, item?.raw?.createdByName, item?.raw?.requesterUserId, item?.raw?.createdByUserId, item?.raw?.businessOwnerUserId, item?.raw?.assigneeUserId) }
function itemSubmittedByMe(item: any) { return samePerson(item?.requesterName, item?.raw?.requesterName, item?.raw?.requester, item?.raw?.requesterUserId, item?.raw?.createdByName, item?.raw?.createdByUserId) }
function itemHasRelatedRequest(item: any) { return requests.value.some(row => ((item.requirementId && String(row.requirementId || '') === String(item.requirementId)) || (item.projectId && String(row.projectId || '') === String(item.projectId))) && samePerson(row.requesterName, row.requesterUserId, row.assignee, row.assigneeUserId)) }
function itemHasRelatedCollaboration(item: any) { return collaborations.value.some(row => ((item.requirementId && String(row.requirementId || '') === String(item.requirementId)) || (item.projectId && String(row.projectId || '') === String(item.projectId))) && samePerson(row.requesterName, row.requesterUserId, row.recipientName, row.recipientUserId)) }
function feedbackMeta(item: any) { const row = feedbackFor(item); if (!row) return { summary: '', tone: '', actionLabel: '', actionLink: '', actionEntry: null }; const entries = row.outcomeRequests || []; const ownPending = entries.find((entry: any) => entry.status === 'pending' && (entry.sentAt || ['sent', 'success'].includes(entry.notificationStatus)) && feedbackRecipient(entry, row)); const ownSubmitted = entries.find((entry: any) => entry.status === 'submitted' && feedbackRecipient(entry, row)); const issue = Number(row.openIssueCount || 0) > 0; if (issue) return { summary: `反馈需处理 · ${row.openIssueCount} 条问题`, tone: 'danger', actionLabel: '', actionLink: '', actionEntry: null }; if (ownPending) return { summary: ownPending.stage === 'day7' ? '待填写3天回执' : '待填写30天价值验证', tone: 'warning', actionLabel: '填写回执', actionLink: ownPending.link || '', actionEntry: ownPending }; if (ownSubmitted) return { summary: ownSubmitted.stage === 'day7' ? '已提交3天回执' : '已提交30天价值验证', tone: 'success', actionLabel: '查看反馈', actionLink: '', actionEntry: ownSubmitted }; if (entries.some((entry: any) => entry.status === 'submitted')) return { summary: '已有业务反馈', tone: 'success', actionLabel: '查看反馈', actionLink: '', actionEntry: null }; if (entries.some((entry: any) => entry.status === 'pending')) return { summary: '回执已安排', tone: '', actionLabel: '', actionLink: '', actionEntry: null }; return { summary: '', tone: '', actionLabel: '', actionLink: '', actionEntry: null } }

const lifecycleItems = computed(() => {
  const items: any[] = []
  const formalRequirementIds = new Set(requirements.value.map(item => String(item.id)))
  for (const item of demandPool.value) {
    if (item.requirementId && formalRequirementIds.has(String(item.requirementId))) continue
    const stage = stageForDemand(item)
    const base: any = { key: `demand:${item.id}`, id: item.id, sourceType: 'demand', sourceLabel: '业务提报', title: item.title || '未命名需求', stage, progress: progressFor(stage, 'demand'), projectId: item.projectId || '', requirementId: item.requirementId || '', projectName: item.projectName || '', department: item.department || '', ownerName: item.assignee || item.requesterName || '', updatedAt: item.updatedAt || item.createdAt, expectedDeliveryTime: item.expectedDeliveryTime || '', description: item.description || item.originalFeedback || '', requesterName: item.requesterName || '', pendingAction: item.confirmation?.status === 'pending' ? '待业务确认' : '', actionLabel: item.confirmation?.status === 'pending' ? '去确认' : '', actionLink: item.confirmation?.link || '', raw: item }
    base.latestActivity = latestActivityFor(base)
    items.push(base)
  }
  for (const item of projects.value) {
    const stage = stageForProject(item)
    const meta = stage === '已上线' ? feedbackMeta({ projectId: item.id }) : { summary: '', tone: '', actionLabel: '', actionLink: '', actionEntry: null }
    const base: any = { key: `project:${item.id}`, id: item.id, sourceType: 'project', sourceLabel: '产品项目', title: item.name || '未命名项目', stage, progress: Math.max(safeProgress(item.progress, 0), progressFor(stage, 'project')), projectId: item.id, requirementId: '', projectName: item.name || '', department: item.department || '', ownerName: item.businessOwner || item.devOwner || '', updatedAt: item.updatedAt || item.createdAt, expectedDeliveryTime: item.targetEndDate || '', description: item.description || '', requesterName: item.businessOwner || '', feedbackSummary: meta.summary, feedbackTone: meta.tone, pendingAction: meta.actionLabel === '填写回执' ? meta.summary : '', actionLabel: meta.actionLabel || '', actionLink: meta.actionLink || '', raw: item }
    const todo = activeTodoFor(base); const todoAction = todoActionFor(todo)
    if (!base.pendingAction && todo) Object.assign(base, todoAction, { todo })
    base.latestActivity = latestActivityFor(base)
    items.push(base)
  }
  for (const item of requirements.value) {
    const stage = stageForRequirement(item)
    const meta = stage === '已上线' ? feedbackMeta({ requirementId: item.id, projectId: item.projectId }) : { summary: '', tone: '', actionLabel: '', actionLink: '', actionEntry: null }
    const collab = collaborations.value.find(row => String(row.requirementId || '') === String(item.id) && ['waiting_business', 'open'].includes(row.status))
    const request = requests.value.find(row => String(row.requirementId || '') === String(item.id) && !['resolved', 'closed', 'rejected'].includes(row.status))
    const base: any = { key: `requirement:${item.id}`, id: item.id, sourceType: 'requirement', sourceLabel: '业务需求', title: item.title || '未命名需求', stage, progress: Math.max(safeProgress(item.progress, 0), progressFor(stage, 'requirement')), projectId: item.projectId || '', requirementId: item.id, projectName: item.projectName || item.pname || '', department: item.department || '', ownerName: item.assignee || item.requester || '', updatedAt: item.updatedAt || item.createdAt, expectedDeliveryTime: item.expectedDeliveryTime || '', description: item.description || '', requesterName: item.requester || '', feedbackSummary: meta.summary, feedbackTone: meta.tone, pendingAction: collab ? '待业务处理' : meta.actionLabel === '填写回执' ? meta.summary : '', actionLabel: collab ? '去确认' : meta.actionLabel || '', actionLink: meta.actionLink || '', followupSummary: request ? '已提交，等待 IT 跟进' : '', raw: item }
    const todo = activeTodoFor(base); const todoAction = todoActionFor(todo)
    if (!base.pendingAction && todo) Object.assign(base, todoAction, { todo })
    base.latestActivity = latestActivityFor(base)
    items.push(base)
  }
  return items.sort((a, b) => String(b.updatedAt || '').localeCompare(String(a.updatedAt || '')))
})
const relatedItems = computed(() => lifecycleItems.value.filter(item => (isLeader() && activeView.value === 'all') || itemMatchesPerson(item) || itemHasRelatedRequest(item) || itemHasRelatedCollaboration(item) || (item.projectId && demandPool.value.some(row => String(row.projectId || '') === String(item.projectId) && samePerson(row.requesterName, row.createdByName, row.requesterUserId, row.createdByUserId)))))
const businessItems = computed(() => relatedItems.value.filter(item => item.sourceType !== 'project'))
const activeBusinessItems = computed(() => businessItems.value.filter(item => !['已上线', '3 天回执', '30 天价值验证'].includes(item.stage)))
function dateKey(value: string) { return String(value || '').slice(0, 10) }
function dateOffsetKey(offset: number) {
  const d = new Date(); d.setDate(d.getDate() + offset)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const recentCompletedItems = computed(() => businessItems.value.filter(item => ['已上线', '3 天回执', '30 天价值验证'].includes(item.stage) && dateKey(item.updatedAt || item.createdAt) >= dateOffsetKey(-7)))
const submittedBusinessItems = computed(() => businessItems.value.filter(item => itemSubmittedByMe(item)))
const viewItems = computed(() => activeView.value === 'all' && isLeader() ? relatedItems.value : businessItems.value)
const businessView = computed(() => activeView.value !== 'all' || !isLeader())
const visibleProjectOptions = computed(() => isLeader() ? projects.value : projects.value.filter(project => relatedItems.value.some(item => String(item.projectId || '') === String(project.id))))
const visibleRequirementOptions = computed(() => isLeader() ? requirements.value : requirements.value.filter(requirement => relatedItems.value.some(item => String(item.requirementId || '') === String(requirement.id))))
const visibleItems = computed(() => viewItems.value.filter(item => { if (summaryFocus.value === 'active') return !['已上线', '3 天回执', '30 天价值验证'].includes(item.stage); if (summaryFocus.value === 'pending') return !!item.pendingAction; if (summaryFocus.value === 'completed') return recentCompletedItems.value.some(completed => completed.key === item.key); return true }))
const pendingItems = computed(() => businessItems.value.filter(item => item.pendingAction))
const filteredItems = computed(() => visibleItems.value.filter(item => { if (activeView.value === 'pending' && !item.pendingAction) return false; if (stageFilter.value !== 'all' && item.stage !== stageFilter.value) return false; const activity = item.latestActivity || {}; const text = `${item.title} ${item.projectName} ${item.ownerName} ${item.description} ${activity.title || ''} ${activity.content || ''}`.toLowerCase(); return !keyword.value.trim() || text.includes(keyword.value.trim().toLowerCase()) }))
const displayGroups = computed(() => {
  const groups = new Map<string, any>()
  for (const item of filteredItems.value) {
    const key = item.projectId ? `project:${item.projectId}` : 'pool:unassigned'
    if (!groups.has(key)) groups.set(key, { key, header: null, children: [] })
    const group = groups.get(key)
    if (item.sourceType === 'project') group.header = item
    else group.children.push(item)
  }
  return Array.from(groups.values()).map(group => {
    if (!group.header) {
      const first = group.children[0]
      const isPool = group.key === 'pool:unassigned'
      group.header = { key: `group:${group.key}`, id: '', sourceType: isPool ? 'demand' : 'project', sourceLabel: isPool ? '需求池' : 'L2 项目', title: isPool ? '待立项需求' : (first?.projectName || '未命名项目'), stage: isPool ? '需求池待评估' : (first?.stage || '正式立项'), progress: isPool ? Math.max(...group.children.map((item: any) => item.progress || 0), 0) : (first?.progress || 0), latestActivity: first?.latestActivity || { title: '暂无新的动态', content: '', at: '' } }
    }
    group.children.sort((a: any, b: any) => String(b.updatedAt || '').localeCompare(String(a.updatedAt || '')))
    return group
  }).sort((a, b) => String(b.header.updatedAt || b.children[0]?.updatedAt || '').localeCompare(String(a.header.updatedAt || a.children[0]?.updatedAt || '')))
})
const summaryCards = computed(() => [{ key: 'pending', focus: 'pending' as SummaryFocus, label: '待我处理', value: pendingItems.value.length, desc: '需要业务确认、验收或填写回执', icon: ShieldCheck, className: 'border-amber-100 bg-amber-50/50', valueClass: 'text-amber-600' }, { key: 'mine', focus: 'all' as SummaryFocus, label: '我发起的需求', value: submittedBusinessItems.value.length, desc: '我提交并可持续跟进的业务需求', icon: Inbox, className: 'border-blue-100 bg-blue-50/50', valueClass: 'text-blue-600' }, { key: 'active', focus: 'active' as SummaryFocus, label: '进行中的需求', value: activeBusinessItems.value.length, desc: '正在推进的业务需求，不展示项目拆分', icon: Clock3, className: 'border-sky-100 bg-sky-50/50', valueClass: 'text-sky-600' }, { key: 'done', focus: 'completed' as SummaryFocus, label: '最近完成', value: recentCompletedItems.value.length, desc: '最近 7 天已上线或进入运营验证', icon: CheckCircle2, className: 'border-violet-100 bg-violet-50/50', valueClass: 'text-violet-600' }])

let toastTimer: number | undefined
function selectView(view: ViewKey) { activeView.value = view; summaryFocus.value = 'all' }
function selectSummary(card: { focus: SummaryFocus }) { summaryFocus.value = card.focus; activeView.value = card.focus === 'pending' ? 'pending' : 'mine' }
function isGroupExpanded(key: string) { return expandedGroups.value[key] ?? displayGroups.value.length === 1 }
function toggleGroup(key: string) { expandedGroups.value[key] = !isGroupExpanded(key) }
function notify(message: string) { toast.value = message; if (toastTimer) window.clearTimeout(toastTimer); toastTimer = window.setTimeout(() => { toast.value = '' }, 2800) }
function sourceClass(source: string) { return source === 'demand' ? 'rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-600' : source === 'project' ? 'rounded-full bg-teal-50 px-2 py-0.5 text-[10px] font-semibold text-teal-700' : 'rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-600' }
function stageClass(stage: string) { return ['已上线', '3 天回执', '30 天价值验证'].includes(stage) ? 'rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-600' : stage === '待业务验收' || stage === '业务确认' ? 'rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700' : 'rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600' }
function businessNextStep(item: any) { if (item.pendingAction) return item.pendingAction; return ({ '需求池待评估': '等待 IT 完成初筛', '业务确认': '等待业务确认结果', 'IT 综合决策': '等待 IT 决策', '正式立项': '等待进入开发', '开发中': '等待交付验收', '待业务验收': '需要业务完成验收', '已上线': '进入上线后使用验证', '3 天回执': '等待 30 天价值验证', '30 天价值验证': '完成价值复盘' } as Record<string, string>)[item.stage] || '等待后续更新' }
function formatDate(value: any) { return value ? String(value).replace('T', ' ').slice(0, 16) : '暂无' }
function lifecycleReached(current: string, step: string) { return lifecycleSteps.indexOf(step) < lifecycleSteps.indexOf(current) }
const selectedLifecycle = computed(() => {
  const item = selectedItem.value
  const step = selectedLifecycleStep.value
  if (!item || !step) return null
  const currentIndex = lifecycleSteps.indexOf(item.stage)
  const stepIndex = lifecycleSteps.indexOf(step)
  const status = step === item.stage ? '当前阶段' : stepIndex >= 0 && currentIndex >= 0 && stepIndex < currentIndex ? '已完成' : '待开始'
  const matches = activities.value.filter(row => {
    const sameScope = (item.requirementId && String(row.requirementId || '') === String(item.requirementId)) || (item.projectId && String(row.projectId || '') === String(item.projectId))
    if (!sameScope) return false
    return String(row.newValue || '').includes(step) || String(row.content || '').includes(step) || String(row.title || '').includes(step)
  }).sort((a, b) => String(activityTimestamp(b)).localeCompare(String(activityTimestamp(a))))
  const record = matches[0]
  return {
    step,
    status,
    description: lifecycleDescriptions[step] || '该阶段暂无补充说明。',
    record: record ? String(record.reason || record.content || record.newValue || record.title || '') : status === '当前阶段' ? latestActivityText(item) : '',
    at: record ? activityTimestamp(record) : status === '当前阶段' ? item.updatedAt : '',
  }
})
function selectLifecycleStep(step: string) { selectedLifecycleStep.value = step }
function activityTarget(item: any) { return item?.requirementId || item?.projectId ? item : null }
function resetDemand() { demandForm.value = { title: '', projectId: '', department: currentUser.value.department || '', businessUrgency: 'normal', expectedDeliveryTime: '', description: '', requesterName: currentUser.value.name || '' } }
function openDemandModal() { resetDemand(); modal.value = 'demand' }
function openMatterModal(item: any = null) { matterForm.value = { requirementId: item?.requirementId || '', kind: 'business_feedback', title: item ? `请协作确认：${item.title}` : '', content: '', dueDate: '', recipientName: '', recipientUserId: '' }; modal.value = 'matter' }
function openDetail(item: any) { selectedItem.value = item; selectedLifecycleStep.value = lifecycleSteps.includes(item?.stage) ? item.stage : lifecycleSteps[0]; modal.value = 'detail' }
function openActivity(item: any) { if (!activityTarget(item)) return; selectedItem.value = item; activityScopeType.value = item.requirementId ? 'requirement' : 'project'; activityScopeId.value = item.requirementId || item.projectId; modal.value = 'activity' }
function closeModal() { modal.value = ''; feedbackDetail.value = null; activityScopeId.value = '' }
function addFiles(files: File[]) { for (const file of files) { if (file.size > 50 * 1024 * 1024) { notify(`附件「${file.name}」超过50MB，未添加`); continue }; if (pendingFiles.value.some(item => item.name === file.name && item.size === file.size)) continue; pendingFiles.value.push(file); if (file.type.startsWith('image/')) previewUrls.set(file, URL.createObjectURL(file)) } }
function handleFileInput(event: Event) { addFiles(Array.from((event.target as HTMLInputElement).files || [])); (event.target as HTMLInputElement).value = '' }
function handlePaste(event: ClipboardEvent) { const images = Array.from(event.clipboardData?.items || []).filter(item => item.type.startsWith('image/')).map(item => item.getAsFile()).filter(Boolean) as File[]; if (!images.length) return; event.preventDefault(); addFiles(images.map((file, index) => new File([file], `clipboard-${Date.now()}-${index}.${file.type.split('/')[1] || 'png'}`, { type: file.type }))) }
function removePendingFile(index: number) { const file = pendingFiles.value[index]; if (file) { const url = previewUrls.get(file); if (url) URL.revokeObjectURL(url); previewUrls.delete(file) }; pendingFiles.value.splice(index, 1) }
function filePreview(file: File) { return previewUrls.get(file) || '' }
function fileExtension(file: File) { return file.name.split('.').pop() || '' }
function formatSize(size: number) { return size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))}KB` : `${(size / 1024 / 1024).toFixed(1)}MB` }
async function uploadPending(ownerType: string, ownerId: string) { const uploaded: any[] = []; for (const file of pendingFiles.value) { const result: any = await api.uploadBusinessAttachment(ownerType, ownerId, file); if (result) uploaded.push(result) }; return uploaded }
async function submitDemand() { if (!demandForm.value.department.trim() || !demandForm.value.description.trim()) { notify('请填写归属部门和当前问题与期望结果'); return }; saving.value = true; const result: any = await api.createDemandPoolItem({ title: demandForm.value.title, description: demandForm.value.description, projectId: demandForm.value.projectId, department: demandForm.value.department, businessPriority: demandForm.value.businessUrgency, expectedDeliveryTime: demandForm.value.expectedDeliveryTime, requesterName: demandForm.value.requesterName }); if (result?.id && pendingFiles.value.length) await uploadPending('demand_pool', result.id); saving.value = false; if (!result) { notify('提交失败，请检查登录状态后重试'); return }; clearFiles(); closeModal(); await load(); notify('新需求已提交并进入需求池待评估') }
async function submitMatter() { if (!matterForm.value.requirementId || !matterForm.value.title.trim() || !matterForm.value.content.trim()) { notify('请选择关联 L3，并填写事项标题和说明'); return }; const requirement = requirements.value.find(item => String(item.id) === String(matterForm.value.requirementId)); matterForm.value.recipientName = matterForm.value.recipientName || requirement?.assignee || ''; saving.value = true; const result = await api.createBusinessCollaboration({ ...matterForm.value }); saving.value = false; if (!result) { notify('事项提交失败，请检查关联需求和权限'); return }; closeModal(); await load(); notify('业务事项已提交，并已写入该 L3 的协作记录') }
function clearFiles() { for (const file of pendingFiles.value) { const url = previewUrls.get(file); if (url) URL.revokeObjectURL(url); previewUrls.delete(file) }; pendingFiles.value = [] }
async function acknowledgeTodo(item: any) {
  const todo = item?.todo
  if (!todo?.id || todo.status !== 'unread') return
  const saved: any = await api.markTodoRead(todo.id)
  if (saved) { todo.status = saved.status; todo.readAt = saved.readAt }
}
async function runItemAction(item: any) {
  await acknowledgeTodo(item)
  if (item.actionLabel === '查看动态') { openActivity(item); return }
  if (item.actionLabel === '去确认' && item.actionLink) { window.open(item.actionLink, '_blank', 'noopener'); return }
  if (item.actionLabel === '填写回执') { if (item.actionLink) window.open(item.actionLink, '_blank', 'noopener'); else await openFeedback(item); return }
  if (item.actionLabel === '查看反馈') { await openFeedback(item); return }
  if (item.actionLabel === '去确认') { openDetail(item); return }
  if (item.actionLabel === '去处理') { openDetail(item); return }
  if (!item.actionLabel) { openDetail(item); return }
  openMatterModal(item)
}
async function openFeedback(item: any) { const row = feedbackFor(item); if (!row?.id) { notify('尚未建立上线后运营记录'); return }; feedbackDetail.value = await api.getPostlaunchOperation(row.id); if (feedbackDetail.value) { selectedItem.value = item; modal.value = 'feedback' } }
function feedbackStatus(stage: string) { const entry = (feedbackDetail.value?.outcomeRequests || []).find((item: any) => item.stage === stage); if (!entry) return '未安排'; if (entry.status === 'pending' && !(entry.sentAt || ['sent', 'success'].includes(entry.notificationStatus))) return '已安排'; return entry.statusLabel || entry.status || '未安排' }
function isFeedbackRecipient(entry: any) { const detail = feedbackDetail.value || {}; const userId = String(currentUser.value.userId || currentUser.value.id || '').trim(); return Boolean((userId && entry.recipientUserId && String(entry.recipientUserId) === userId) || samePerson(entry.recipientName, detail.businessOwnerName)) }
async function load() { loading.value = true; const [projectRows, requirementRows, demandRows, requestRows, collaborationRows, postlaunch, contactOptions, activityRows, todoRows] = await Promise.all([api.getProjects(), api.getRequirements({}), api.getDemandPool(), api.getBusinessRequests(), api.getBusinessCollaborations(), api.getPostlaunchDashboard(), api.getDingTalkOptions(), api.getActivities(), api.getTodos()]); projects.value = projectRows || []; requirements.value = requirementRows || []; demandPool.value = demandRows || []; requests.value = requestRows || []; collaborations.value = collaborationRows || []; postlaunchRows.value = postlaunch?.rows || []; departments.value = contactOptions?.departments || []; activities.value = activityRows || []; todos.value = (todoRows || []).filter((item: any) => item.status !== 'done'); loading.value = false }
onMounted(async () => { readUser(); await load(); const requirementId = String(route.query.requirementId || '').trim(); const projectId = String(route.query.projectId || '').trim(); if (requirementId) { const item = lifecycleItems.value.find(row => String(row.requirementId) === requirementId); if (item) openDetail(item) } else if (projectId) { const item = lifecycleItems.value.find(row => String(row.projectId) === projectId); if (item) openDetail(item) } })
onUnmounted(clearFiles)
return { route, currentUser, projects, requirements, demandPool, requests, collaborations, postlaunchRows, departments, activities, todos, loading, saving, activeView, summaryFocus, keyword, stageFilter, modal, selectedItem, selectedLifecycleStep, activityScopeType, activityScopeId, feedbackDetail, pendingFiles, toast, expandedGroups, previewUrls, demandForm, matterForm, lifecycleSteps, lifecycleDescriptions, viewTabs, stageOptions, readUser, isLeader, samePerson, feedbackFor, stageForDemand, stageForRequirement, stageForProject, progressFor, safeProgress, activityTimestamp, latestActivityFor, latestActivityText, activeTodoFor, todoActionFor, feedbackRecipient, itemMatchesPerson, itemSubmittedByMe, itemHasRelatedRequest, itemHasRelatedCollaboration, feedbackMeta, lifecycleItems, relatedItems, businessItems, activeBusinessItems, dateKey, dateOffsetKey, recentCompletedItems, submittedBusinessItems, viewItems, businessView, visibleProjectOptions, visibleRequirementOptions, visibleItems, pendingItems, filteredItems, displayGroups, summaryCards, toastTimer, selectView, selectSummary, isGroupExpanded, toggleGroup, notify, sourceClass, stageClass, businessNextStep, formatDate, lifecycleReached, selectedLifecycle, selectLifecycleStep, activityTarget, resetDemand, openDemandModal, openMatterModal, openDetail, openActivity, closeModal, addFiles, handleFileInput, handlePaste, removePendingFile, filePreview, fileExtension, formatSize, uploadPending, submitDemand, submitMatter, clearFiles, acknowledgeTodo, runItemAction, openFeedback, feedbackStatus, isFeedbackRecipient, load }
}
