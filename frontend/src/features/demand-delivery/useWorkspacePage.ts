import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
import type { Requirement } from '../../types'
export function useWorkspacePage() {


const router = useRouter()
const route = useRoute()
const activeMember = ref('')
const reqs = ref<Requirement[]>([])
const collaborationTodos = ref<any[]>([])
const pendingSection = ref<HTMLElement | null>(null)
const postlaunchRows = ref<any[]>([])
const sendingOutcomeId = ref('')
const sendState = ref<Record<string, string>>({})
async function refreshCollaborationTodos() {
  const [todos, latest, postlaunch] = await Promise.all([api.getTodos(), api.getRequirements({}), api.getPostlaunchDashboard()])
  if (todos) collaborationTodos.value = todos.filter((t: any) => t.status !== 'done')
  if (latest) reqs.value = latest
  if (postlaunch?.rows) postlaunchRows.value = postlaunch.rows
}

function todoTypeLabel(todo: any) {
  return ({
    business_collaboration: '业务协作',
    shared_activity: '共享动态',
    requirement_assigned: '需求分派',
    requirement_delivered: '交付确认',
  } as Record<string, string>)[todo?.type] || '待处理'
}

async function openTodo(todo: any) {
  if (!todo?.id) return
  await api.markTodoRead(todo.id)
  window.dispatchEvent(new Event('pm-todo-updated'))
  if (todo.requirementId) await router.push('/requirements/' + todo.requirementId)
  else await router.push({ path: '/workspace', query: { focus: 'pending', todoId: todo.id } })
}

async function completeTodo(todo: any) {
  if (!todo?.id) return
  const saved: any = await api.markTodoDone(todo.id)
  if (!saved) { alert('待处理事项更新失败，请刷新后重试'); return }
  collaborationTodos.value = collaborationTodos.value.filter(item => item.id !== todo.id)
  window.dispatchEvent(new Event('pm-todo-updated'))
}
const projects = ref<any[]>([])
const reportOpen = ref(false)
const reportLoading = ref(false)
const reportPeriod = ref<'week' | 'month'>('week')
const workReport = ref<any>(null)
const viewScope = ref<'mine' | 'team'>('mine')
const showProjectModal = ref(false)
const projectSaving = ref(false)
const developerOptions = ref<string[]>([])
const projectForm = ref<any>({})
const showRequirementModal = ref(false)
const requirementSaving = ref(false)
const quickRequirementForm = ref<any>({})
const showWorkLogModal = ref(false)
const workLogLoading = ref(false)
const workLogSaving = ref(false)
const activeRequirement = ref<any>(null)
const workLogs = ref<any[]>([])
const workLogForm = ref<any>({ logType: '工作进展', content: '' })
const showDeliveryModal = ref(false)
const deliveryLoading = ref(false)
const deliverySaving = ref(false)
const deliveryError = ref('')
const deliveryNotice = ref('')
const deliveryRequirement = ref<any>(null)
const deliveryLifecycle = ref<any>(null)
const deliveryPreparation = ref<any>({ actualResult: '', evidence: '', knownIssues: '' })
const deliveryCompletion = ref<any>({ deliveryKind: '上线', useStartDate: '', notes: '' })
const showFeedbackModal = ref(false)
const feedbackLoading = ref(false)
const feedbackError = ref('')
const feedbackRequirement = ref<any>(null)
const feedbackDetail = ref<any>(null)
const workFilter = ref<'all' | 'todo' | 'doing' | 'due' | 'done' | 'feedback_pending' | 'feedback_unread' | 'feedback_issue'>('all')

const scopeOptions = [
  { value: 'mine', label: '我的工作' },
  { value: 'team', label: '团队全览' },
]
const lifecycleStatuses = ['开发中', '待上线', '维护中', '暂停中']
const requirementStatuses = ['待处理', '进行中', '待交付', '已交付']
const quickTypeOptions = ['新增功能', '功能优化', '问题修复', '验证交付', '业务确认', '产品设计', '技术建设']
const workLogTypes = ['工作进展', '遇到问题', '交付说明', '下一步']
const workFilterOptions = [
  { key: 'all', label: '全部当前工作' },
  { key: 'todo', label: '待开始' },
  { key: 'doing', label: '进行中' },
  { key: 'due', label: '交付关注' },
  { key: 'done', label: '最近已完成' },
]
const currentUser = ref<any>({})
const canCreateProject = computed(() => ['super_admin', 'admin', 'editor'].includes(currentUser.value?.role || ''))
const deliveryBaseline = computed(() => (deliveryLifecycle.value?.baselines || []).find((item: any) => item.status === 'confirmed') || null)
const pendingDeliveryRound = computed(() => (deliveryLifecycle.value?.links || []).find((item: any) => item.kind === 'verification' && item.status === 'pending') || null)
const passedDeliveryRound = computed(() => (deliveryLifecycle.value?.links || []).find((item: any) => item.kind === 'verification' && item.status === 'submitted' && item.outcome === 'passed' && !(deliveryLifecycle.value?.operations || []).some((operation: any) => operation.acceptanceRequestId === item.id)) || null)
const latestDeliveryChangeRound = computed(() => {
  const rows = (deliveryLifecycle.value?.links || []).filter((item: any) => item.kind === 'verification' && item.status === 'submitted' && item.outcome === 'changes')
  return rows.sort((a: any, b: any) => String(a.submittedAt || a.createdAt || '').localeCompare(String(b.submittedAt || b.createdAt || ''))).at(-1) || null
})
const pendingFeedbackRoute = computed(() => latestDeliveryChangeRound.value?.feedback?.routeType === 'it_review')

const teamMembers = [
  { name: '十叶-冯硕硕', role: '前端/全栈开发', color: '#3b82f6', taskCount: 0 },
  { name: '星河-李子文', role: '后端开发', color: '#10b981', taskCount: 0 },
  { name: '惜君-吴旭骏', role: '全栈开发', color: '#8b5cf6', taskCount: 0 },
]

function selectMember(name: string) {
  viewScope.value = 'team'
  activeMember.value = activeMember.value === name ? '' : name
  workFilter.value = 'all'
}

async function copyOutcomeLink(link: string) {
  if (!link) return
  try { await navigator.clipboard.writeText(link); alert('业务反馈链接已复制') } catch { alert(link) }
}

async function sendOutcomeLink(item: any) {
  if (!item?.id || sendingOutcomeId.value) return null
  sendingOutcomeId.value = item.id
  const result: any = await api.sendDemandPoolOutcomeRequest(item.id)
  sendingOutcomeId.value = ''
  if (result?.notificationStatus === 'success') {
    sendState.value = { ...sendState.value, [item.id]: 'success' }
    Object.assign(item, result)
    alert('业务反馈链接已发送')
  } else {
    sendState.value = { ...sendState.value, [item.id]: 'failed' }
    alert(result?.notificationError || result?.error || '发送失败，可复制链接手动发送')
  }
  return result
}

async function openFeedbackPanel(requirement: any) {
  if (!requirement?.id) return
  feedbackRequirement.value = requirement
  feedbackDetail.value = null
  feedbackError.value = ''
  feedbackLoading.value = true
  showFeedbackModal.value = true
  try {
    let row = postlaunchRows.value.find(item => String(item.requirementId) === String(requirement.id))
    if (!row) {
      const useStartDate = dateKey(requirement.completedAt || requirement.updatedAt || requirement.createdAt) || deliveryToday()
      row = await api.createPostlaunchOperation({
        targetType: 'requirement', targetId: requirement.id, deliveryKind: '上线',
        deliveryDate: useStartDate, useStartDate, businessOwnerName: requirement.requester || requirement.requesterName || '',
      })
    } else {
      row = await api.getPostlaunchOperation(row.id) || row
    }
    if (!row) throw new Error('上线反馈记录读取失败，请刷新后重试')
    feedbackDetail.value = row
    const index = postlaunchRows.value.findIndex(item => String(item.id) === String(row.id))
    if (index >= 0) postlaunchRows.value[index] = row
    else postlaunchRows.value = [row, ...postlaunchRows.value]
  } catch (error: any) {
    feedbackError.value = error?.message || '上线反馈记录读取失败，请刷新后重试'
  } finally {
    feedbackLoading.value = false
  }
}

function closeFeedbackPanel() {
  if (sendingOutcomeId.value) return
  showFeedbackModal.value = false
  feedbackRequirement.value = null
  feedbackDetail.value = null
  feedbackError.value = ''
}

async function sendFeedbackLink(item: any) {
  const result: any = await sendOutcomeLink(item)
  if (result?.notificationStatus === 'success') {
    if (feedbackDetail.value?.outcomeRequests) {
      const target = feedbackDetail.value.outcomeRequests.find((entry: any) => entry.id === item.id)
      if (target) Object.assign(target, result)
    }
    await refreshCollaborationTodos()
  }
}

async function markFeedbackViewed(item: any) {
  if (!item?.id || item.status !== 'submitted') return
  const result: any = await api.markDemandPoolOutcomeViewed(item.id)
  if (!result) {
    alert('标记失败，请刷新后重试')
    return
  }
  Object.assign(item, result)
  await refreshCollaborationTodos()
}

function applyCurrentUser() {
  const raw = localStorage.getItem(SESSION_STORAGE_KEY)
  try { currentUser.value = raw ? JSON.parse(raw) : {} } catch { currentUser.value = {} }
  if (currentUser.value?.devOwnerName) activeMember.value = currentUser.value.devOwnerName
}

const searchName = computed(() => {
  if (!activeMember.value) return ''
  return activeMember.value.split('-')[1] || activeMember.value
})

const myReqs = computed(() => {
  if (viewScope.value === 'mine' && !searchName.value) return []
  if (!searchName.value) return reqs.value.filter(r => r.assignee !== '待分配')
  return reqs.value.filter(r => r.assignee.includes(searchName.value) || r.assignee.includes(activeMember.value))
})

const activeReqs = computed(() => {
  const active = new Set(['待处理', '进行中', '待交付'])
  return [...myReqs.value].filter(r => active.has(r.status)).sort((a, b) => {
    const focus = (r: any) => ({ 核心: 0, 重要: 1, 常规: 2 }[r.impactLevel as string] ?? 2)
    return focus(a) - focus(b) || String(a.expectedDeliveryTime || '9999').localeCompare(String(b.expectedDeliveryTime || '9999'))
  })
})

const recentDoneReqs = computed(() => {
  const minKey = dateOffsetKey(-7)
  return [...myReqs.value]
    .filter(r => ['已交付', '已关闭'].includes(r.status))
    .filter(r => dateKey(r.completedAt || r.updatedAt || r.createdAt) >= minKey)
    .sort((a, b) => String(b.completedAt || b.updatedAt || '').localeCompare(String(a.completedAt || a.updatedAt || '')))
})

const dueAttentionReqs = computed(() => activeReqs.value.filter(r => isDueWithin(r, 7)))

const feedbackRequests = computed(() => {
  const items: any[] = []
  for (const row of postlaunchRows.value) {
    for (const item of (row.outcomeRequests || []).filter((entry: any) => ['day7', 'day30'].includes(entry.stage))) {
      items.push({ ...item, operationId: row.id, requirementId: row.requirementId || '', projectId: row.projectId || '', title: row.title || '', openIssueCount: Number(row.openIssueCount || 0), dueDate: item.stage === 'day7' ? row.day7DueDate : row.day30DueDate })
    }
  }
  return items
})

const completedReqs = computed(() => [...myReqs.value].filter(r => ['已交付', '已关闭'].includes(r.status)))
const feedbackPendingReqs = computed(() => completedReqs.value.filter(r => feedbackRequests.value.some(item => String(item.requirementId) === String(r.id) && item.status === 'pending')))
const feedbackUnreadReqs = computed(() => completedReqs.value.filter(r => feedbackRequests.value.some(item => String(item.requirementId) === String(r.id) && item.status === 'submitted' && !item.viewedAt)))
const feedbackIssueReqs = computed(() => completedReqs.value.filter(r => feedbackRequests.value.some(item => String(item.requirementId) === String(r.id) && feedbackNeedsAttention(item))))

const feedbackStageItems = computed(() => {
  const detail = feedbackDetail.value
  if (!detail) return []
  const requests = detail.outcomeRequests || []
  return [
    { stage: 'day7', label: '上线 3 天回执', dueDate: detail.day7DueDate, item: requests.find((entry: any) => entry.stage === 'day7') },
    { stage: 'day30', label: '上线 30 天价值验证', dueDate: detail.day30DueDate, item: requests.find((entry: any) => entry.stage === 'day30') },
  ]
})

const workList = computed(() => {
  if (workFilter.value === 'todo') return activeReqs.value.filter(r => r.status === '待处理')
  if (workFilter.value === 'doing') return activeReqs.value.filter(r => r.status === '进行中')
  if (workFilter.value === 'due') return dueAttentionReqs.value
  if (workFilter.value === 'done') return recentDoneReqs.value
  if (workFilter.value === 'feedback_pending') return feedbackPendingReqs.value
  if (workFilter.value === 'feedback_unread') return feedbackUnreadReqs.value
  if (workFilter.value === 'feedback_issue') return feedbackIssueReqs.value
  return activeReqs.value
})

const workFilterTitle = computed(() => ({
  all: '我的今日工作',
  todo: '待开始的工作',
  doing: '正在进行的工作',
  due: '需要交付关注的工作',
  done: '最近 7 天已完成',
  feedback_pending: '待业务回执',
  feedback_unread: '已回执待查看',
  feedback_issue: '反馈需处理',
} as Record<string, string>)[workFilter.value])

const emptyWorkText = computed(() => {
  if (workFilter.value === 'done') return '最近 7 天没有已完成的工作记录'
  if (workFilter.value === 'feedback_pending') return '当前没有等待业务回执的已交付工作'
  if (workFilter.value === 'feedback_unread') return '当前没有待查看的业务回执'
  if (workFilter.value === 'feedback_issue') return '当前没有需要处理的反馈问题'
  return '当前没有符合条件的工作，可以直接登记一条 L3 工作'
})

const summaryCards = computed(() => {
  return [
    { key: 'feedback_pending', label: '待业务回执', value: feedbackPendingReqs.value.length, desc: '已交付但尚未收到 3 天或 30 天反馈', className: 'border-blue-100 bg-blue-50/60', valueClass: 'text-blue-600' },
    { key: 'feedback_unread', label: '已回执待查看', value: feedbackUnreadReqs.value.length, desc: '业务已提交，等待你查看处理', className: 'border-amber-100 bg-amber-50/60', valueClass: 'text-amber-600' },
    { key: 'feedback_issue', label: '反馈需处理', value: feedbackIssueReqs.value.length, desc: '回执中有问题或价值未达成', className: 'border-rose-100 bg-rose-50/60', valueClass: 'text-rose-600' },
    { key: 'done', label: '最近已完成', value: recentDoneReqs.value.length, desc: '最近 7 天已回写完成的工作', className: 'border-emerald-100 bg-emerald-50/60', valueClass: 'text-emerald-600' },
  ]
})

function setScope(scope: string) {
  viewScope.value = scope as 'mine' | 'team'
  if (viewScope.value === 'mine') applyCurrentUser()
  else activeMember.value = ''
  workFilter.value = 'all'
}

const myProjects = computed(() => {
  const rows = !searchName.value
    ? (projects.value || []).filter((p: any) => p.businessOwner || p.devOwner)
    : (projects.value || []).filter((p: any) =>
    (p.businessOwner || '').includes(searchName.value) ||
    (p.devOwner || '').includes(searchName.value) ||
    (p.businessOwner || '').includes(activeMember.value) ||
    (p.devOwner || '').includes(activeMember.value)
  )
  return [...rows].sort((a: any, b: any) => Number(projectNeedsAttention(b)) - Number(projectNeedsAttention(a)) || String(a.name || '').localeCompare(String(b.name || '')))
})

const focusProjects = computed(() => myProjects.value.filter((p: any) => projectNeedsAttention(p)).slice(0, 6))
const completedProjectCount = computed(() => myProjects.value.filter((p: any) => !projectNeedsAttention(p)).length)
const projectOptions = computed(() => myProjects.value.length ? myProjects.value : (projects.value || []))

function projectNeedsAttention(project: any) {
  return activeReqs.value.some(r => String(r.projectId) === String(project.id)) || projectProgressPercent(project) < 100
}

function setWorkFilter(filter: string) {
  workFilter.value = filter as typeof workFilter.value
}

function feedbackForRequirement(requirement: any) {
  return feedbackRequests.value.filter(item => String(item.requirementId) === String(requirement?.id))
}

function feedbackNeedsAttention(item: any) {
  if (Number(item?.openIssueCount || 0) > 0) return true
  const snapshot = item?.responseSnapshot || {}
  if (item?.stage === 'day7') return ['有问题', '严重'].includes(snapshot.issueLevel) || ['部分解决', '暂未解决'].includes(snapshot.goalStatus) || ['需要调整', '需要改进'].includes(snapshot.satisfaction)
  if (item?.stage === 'day30') return ['暂无明显改善', '暂时无法判断', '未达到', '否'].includes(snapshot.effectStatus)
  return false
}

function feedbackBadge(requirement: any) {
  const items = feedbackForRequirement(requirement)
  if (!items.length) return ''
  if (items.some(feedbackNeedsAttention)) return '反馈需处理'
  if (items.some(item => item.status === 'submitted' && !item.viewedAt)) return '有新回执'
  if (items.some(item => item.status === 'pending')) return '待回执'
  return ''
}

function outcomeStatusClass(item: any) {
  if (!item) return 'bg-gray-100 text-gray-500'
  if (item.status === 'submitted' && !item.viewedAt) return 'bg-amber-100 text-amber-700'
  if (item.status === 'submitted') return 'bg-emerald-100 text-emerald-700'
  if (item.status === 'pending' && item.notificationStatus === 'failed') return 'bg-rose-100 text-rose-700'
  if (item.status === 'pending' && item.notificationStatus === 'success') return 'bg-blue-100 text-blue-700'
  return 'bg-gray-100 text-gray-500'
}

function outcomeStatusText(item: any) {
  if (!item) return '未安排'
  if (item.status === 'submitted' && !item.viewedAt) return '已回执待查看'
  if (item.status === 'submitted') return '已查看'
  if (item.status === 'pending' && item.notificationStatus === 'failed') return '发送失败，可重试'
  if (item.status === 'pending' && item.notificationStatus === 'success') return '已发送待回执'
  if (item.status === 'pending') return '待发送'
  return item.statusLabel || item.status || '未安排'
}

function outcomeSummary(item: any) {
  const snapshot = item?.responseSnapshot || {}
  if (item?.stage === 'day7') return [snapshot.useStatus, snapshot.goalStatus, snapshot.satisfaction].filter(Boolean).join(' · ')
  if (item?.stage === 'day30') return [snapshot.effectStatus, Array.isArray(snapshot.changeTypes) ? snapshot.changeTypes.join('、') : snapshot.changeTypes].filter(Boolean).join(' · ')
  return ''
}

function statusDot(s: string) {
  return statusColor(s)
}
function priorityColor(p: string) { const m: Record<string, string> = { P0: '#ef4444', P1: '#f59e0b', P2: '#3b82f6', P3: '#9ca3af', P4: '#cbd5e1' }; return m[p] || '#9ca3af' }
function statusColor(s: string) {
  const m: Record<string, string> = {
    '待评估': '#9ca3af', '已排期': '#3b82f6', '已立项': '#3b82f6', '需求确认中': '#6366f1',
    '设计中': '#8b5cf6', '开发中': '#f59e0b', '联调中': '#06b6d4', '测试中': '#a855f7',
    '迭代中': '#0ea5e9', '待上线': '#14b8a6', '已上线': '#10b981', '维护中': '#64748b',
    '暂停中': '#f97316', '已关闭': '#6b7280', '已归档': '#94a3b8',
  }
  return m[s] || '#9ca3af'
}
function statusLabel(s: string) {
  return ({ '待处理': '待处理', '进行中': '进行中', '待交付': '待交付', '已交付': '已交付', '已关闭': '已关闭' } as any)[s] || s || '未设置'
}

function dateKey(value: any) {
  return String(value || '').slice(0, 10)
}

function dateOffsetKey(offset: number) {
  const date = new Date()
  date.setHours(0, 0, 0, 0)
  date.setDate(date.getDate() + offset)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function isDueWithin(req: any, days: number) {
  if (['已交付', '已上线', '已关闭', '已归档'].includes(req.status)) return false
  const due = dateKey(req.expectedDeliveryTime)
  return !!due && due <= dateOffsetKey(days)
}

function dueTone(req: any) {
  if (['已交付', '已上线', '已关闭', '已归档'].includes(req.status)) {
    return { label: '已完成', className: 'text-emerald-600' }
  }
  const due = dateKey(req.expectedDeliveryTime)
  if (!due) return { label: '未设置交付日', className: 'text-gray-400' }
  const today = dateOffsetKey(0)
  if (due < today) return { label: `已逾期 ${due.slice(5)}`, className: 'text-red-600' }
  if (due === today) return { label: '今天交付', className: 'text-rose-600' }
  return { label: `预计 ${due.slice(5)}`, className: 'text-gray-500' }
}

function dueLabel(req: any) { return dueTone(req).label }
function impactLabel(req: any) { return req.impactLevel || '常规' }
function workloadLabel(req: any) { return `${req.workloadLevel || '中'}工作量` }

function projectProgressPercent(p: any) {
  const val = p.progress?.progress ?? p.progress?.currentProgress ?? 0
  return Math.max(0, Math.min(100, Math.round(Number(val) || 0)))
}

function projectProgressColor(p: any) {
  if (p.progress?.mode === 'released' || projectProgressPercent(p) >= 100) return '#10b981'
  if (p.progress?.mode === 'empty') return '#d1d5db'
  if ((p.progress?.subLabel || '').includes('暂停')) return '#f97316'
  if (projectProgressPercent(p) >= 70) return '#14b8a6'
  return '#3b82f6'
}

async function updateWorkStatus(requirement: any, nextStatus: string) {
  const reason = nextStatus === '进行中'
    ? '从开发工作台开始工作'
    : nextStatus === '待交付'
      ? '从开发工作台提交交付'
      : '从开发工作台确认交付完成'
  const saved: any = await api.updateRequirement(requirement.id, { status: nextStatus, reason })
  if (!saved) {
    alert('状态更新失败，请打开需求详情检查权限或状态流转')
    return
  }
  const index = reqs.value.findIndex(item => item.id === requirement.id)
  if (index >= 0) reqs.value[index] = { ...reqs.value[index], ...saved, status: saved.status || nextStatus }
  alert(nextStatus === '已交付' ? '工作已交付，L3 底表已回写' : `已更新为「${nextStatus}」，L3 底表已回写`)
}

function deliveryToday() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function loadDeliveryCard(requirement: any) {
  if (!requirement?.id) return
  deliveryLoading.value = true
  deliveryError.value = ''
  try {
    const lifecycle = await api.getRequirementLifecycle(requirement.id)
    if (!lifecycle) throw new Error('交付信息读取失败，请刷新后重试')
    deliveryLifecycle.value = lifecycle
    deliveryRequirement.value = { ...requirement, status: requirement.status }
    if (passedDeliveryRound.value) deliveryCompletion.value = { deliveryKind: '上线', useStartDate: dateKey(passedDeliveryRound.value.submittedAt || requirement.completedAt || deliveryToday()), notes: '' }
  } catch (error: any) {
    deliveryError.value = error?.message || '交付信息读取失败，请刷新后重试'
  } finally {
    deliveryLoading.value = false
  }
}

async function openDeliveryCard(requirement: any) {
  deliveryRequirement.value = requirement
  deliveryLifecycle.value = null
  deliveryPreparation.value = { actualResult: '', evidence: '', knownIssues: '' }
  deliveryCompletion.value = { deliveryKind: '上线', useStartDate: deliveryToday(), notes: '' }
  deliveryNotice.value = ''
  deliveryError.value = ''
  showDeliveryModal.value = true
  await loadDeliveryCard(requirement)
}

function closeDeliveryCard() {
  if (deliverySaving.value) return
  showDeliveryModal.value = false
  deliveryLifecycle.value = null
  deliveryRequirement.value = null
}

async function sendDeliveryConfirmation() {
  if (deliverySaving.value || !deliveryRequirement.value) return
  const actualResult = String(deliveryPreparation.value.actualResult || '').trim()
  if (!actualResult) { deliveryError.value = '请填写实际交付结果'; return }
  if (!deliveryBaseline.value) { deliveryError.value = '当前 L3 没有已确认的上线前验收标准'; return }
  deliverySaving.value = true
  deliveryError.value = ''
  deliveryNotice.value = ''
  try {
    const content = [
      '实际交付结果：' + actualResult,
      deliveryPreparation.value.evidence ? '验证证据 / 截图说明：' + deliveryPreparation.value.evidence : '',
      deliveryPreparation.value.knownIssues ? '已知问题或交付限制：' + deliveryPreparation.value.knownIssues : '',
    ].filter(Boolean).join('\n\n')
    const result: any = await api.createCollaborationLink(deliveryRequirement.value.id, {
      clientKey: crypto.randomUUID(),
      kind: 'verification',
      title: `交付确认：${deliveryRequirement.value.title}`,
      content,
      recipientName: deliveryBaseline.value.recipientName || deliveryRequirement.value.requester || '',
      validDays: 14,
      attachmentIds: [],
      baselineId: deliveryBaseline.value.id,
    })
    if (!result) throw new Error('交付确认链接生成失败')
    deliveryNotice.value = '交付确认链接已生成并发送给业务，状态已进入“待交付”。'
    await refreshCollaborationTodos()
    await loadDeliveryCard({ ...deliveryRequirement.value, status: '待交付' })
  } catch (error: any) {
    deliveryError.value = error?.message || '交付确认链接生成失败'
  } finally {
    deliverySaving.value = false
  }
}

async function routeDeliveryFeedback(routeType: string) {
  const feedbackId = latestDeliveryChangeRound.value?.feedback?.id
  if (!feedbackId || deliverySaving.value) return
  deliverySaving.value = true
  deliveryError.value = ''
  deliveryNotice.value = ''
  try {
    await api.routeDeliveryFeedback(feedbackId, routeType)
    deliveryNotice.value = '反馈处理路由已保存，可继续准备本次交付。'
    await loadDeliveryCard({ ...deliveryRequirement.value, status: '进行中' })
  } catch (error: any) {
    deliveryError.value = error?.message || '反馈路由保存失败，请刷新后重试'
  } finally {
    deliverySaving.value = false
  }
}

async function completeDelivery() {
  if (deliverySaving.value || !deliveryRequirement.value || !passedDeliveryRound.value) return
  deliverySaving.value = true
  deliveryError.value = ''
  deliveryNotice.value = ''
  try {
    const result: any = await api.deliverRequirement(deliveryRequirement.value.id, {
      clientKey: crypto.randomUUID(),
      acceptanceRequestId: passedDeliveryRound.value.id,
      deliveryKind: deliveryCompletion.value.deliveryKind || '上线',
      deliveryDate: deliveryToday(),
      useStartDate: deliveryCompletion.value.useStartDate || deliveryToday(),
      businessOwnerName: deliveryBaseline.value?.recipientName || deliveryRequirement.value.requester || '',
      notes: deliveryCompletion.value.notes || '业务已确认交付，已完成上线。',
    })
    if (!result) throw new Error('交付登记失败')
    deliveryNotice.value = '交付已完成，L3 已回写并建立 3 天回执、30 天复盘。'
    await refreshCollaborationTodos()
    await loadDeliveryCard({ ...deliveryRequirement.value, status: '已交付' })
  } catch (error: any) {
    deliveryError.value = error?.message || '交付登记失败，请刷新后重试'
  } finally {
    deliverySaving.value = false
  }
}

async function copyDeliveryLink(link: string) {
  try { await navigator.clipboard.writeText(link); deliveryNotice.value = '业务确认链接已复制' } catch { deliveryNotice.value = link }
}

function openRequirementCreate() {
  const developer = currentUser.value?.devOwnerName || activeMember.value || ''
  const selectedProject = focusProjects.value[0] || projectOptions.value[0]
  quickRequirementForm.value = {
    title: '',
    projectId: selectedProject?.id || '',
    type: '新增功能',
    priority: 'P2',
    impactLevel: '重要',
    workloadLevel: '中',
    status: '进行中',
    expectedDeliveryTime: dateOffsetKey(0),
    description: '',
    acceptanceCriteria: '',
    assignee: developer,
  }
  showRequirementModal.value = true
}

async function saveQuickRequirement() {
  const form = quickRequirementForm.value
  const project = projectOptions.value.find((item: any) => String(item.id) === String(form.projectId))
  const developer = currentUser.value?.devOwnerName || activeMember.value || form.assignee || ''
  if (!form.title || !form.projectId || !form.expectedDeliveryTime || !form.acceptanceCriteria || !developer) {
    alert('标题、所属项目、验收标准、预计交付时间和开发负责人为必填项')
    return
  }
  if (!project) {
    alert('所属项目不存在，请刷新工作台后重试')
    return
  }
  requirementSaving.value = true
  const saved: any = await api.createRequirement({
    title: form.title,
    projectId: form.projectId,
    type: form.type,
    priority: form.priority,
    impactLevel: form.impactLevel,
    workloadLevel: form.workloadLevel,
    changeObject: form.type === '问题修复' ? '功能' : '功能',
    status: form.status,
    department: project.department || currentUser.value?.department || '信息技术部',
    assignee: developer,
    requester: currentUser.value?.name || developer,
    expectedDeliveryTime: form.expectedDeliveryTime,
    description: form.description || '',
    acceptanceCriteria: form.acceptanceCriteria || '',
    flowMode: 'quick_iteration',
    lifecycleVersion: 2,
    reportingEligible: true,
    relatedRequirementId: '',
    storyPoints: form.workloadLevel === '大' ? 3 : form.workloadLevel === '小' ? 1 : 2,
  })
  requirementSaving.value = false
  if (!saved) {
    alert('登记失败，请检查登录状态和所属项目')
    return
  }
  const fresh: any = saved.id ? await api.getRequirement(saved.id) : null
  reqs.value = [{ ...form, ...saved, ...fresh, projectName: project.name, assignee: developer }, ...reqs.value]
  showRequirementModal.value = false
  workFilter.value = 'all'
  alert('工作已登记，已进入你的今日工作')
}

async function openWorkLog(requirement: any) {
  activeRequirement.value = requirement
  workLogForm.value = { logType: '工作进展', content: '' }
  workLogs.value = []
  showWorkLogModal.value = true
  workLogLoading.value = true
  const rows: any = await api.getRequirementWorkLogs(requirement.id)
  workLogs.value = Array.isArray(rows) ? rows : []
  workLogLoading.value = false
}

async function saveWorkLog() {
  const requirement = activeRequirement.value
  const content = String(workLogForm.value.content || '').trim()
  if (!requirement || !content) {
    alert('请填写本次工作内容')
    return
  }
  workLogSaving.value = true
  const saved: any = await api.createRequirementWorkLog(requirement.id, { logType: workLogForm.value.logType, content, visibility: 'it_private' })
  workLogSaving.value = false
  if (!saved) {
    alert('工作动态保存失败，请检查登录状态或需求权限')
    return
  }
  workLogs.value.unshift({ ...saved, logType: saved.activityTypeLabel || workLogForm.value.logType })
  workLogForm.value.content = ''
  alert('工作动态已保存到 L3 底表，并纳入日报')
}

async function syncMine() {
  const developer = activeMember.value || JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}')?.devOwnerName || ''
  const r = await api.syncNotification({ scope: 'developer', developer })
  alert(r ? `已同步${developer ? '「' + developer + '」' : '开发者'}进度到钉钉群` : '同步失败，请先在通知配置中添加群机器人')
}

async function openProjectCreate() {
  projectForm.value = {
    name: '', description: '', priority: 'P2', status: '开发中', department: currentUser.value?.department || '',
    businessOwner: '', devOwner: currentUser.value?.devOwnerName || '', currentVersion: 'v1.0.0', startDate: '', targetEndDate: '', categoryId: '', images: [],
  }
  showProjectModal.value = true
  if (!developerOptions.value.length) {
    const opts: any = await api.getDingTalkOptions()
    developerOptions.value = Array.from(new Set((opts?.developers || []).map((d: any) => d.name || d.devOwnerName).filter(Boolean)))
  }
  const current = currentUser.value?.devOwnerName
  if (current && !developerOptions.value.includes(current)) developerOptions.value.unshift(current)
}

async function saveProject() {
  if (!projectForm.value.name || !projectForm.value.department || !projectForm.value.devOwner || !projectForm.value.targetEndDate) {
    alert('项目名称、归属部门、开发负责人、目标结束时间为必填项')
    return
  }
  projectSaving.value = true
  const saved: any = await api.createProject(projectForm.value)
  projectSaving.value = false
  if (!saved) { alert('项目创建失败，请检查权限和必填字段'); return }
  showProjectModal.value = false
  projects.value = [{ ...projectForm.value, ...saved }, ...projects.value]
  alert('项目已创建，可继续在工作台登记需求')
}

async function openWorkReport() {
  reportOpen.value = true
  await loadWorkReport(reportPeriod.value)
}

async function loadWorkReport(period: 'week' | 'month') {
  reportPeriod.value = period
  reportLoading.value = true
  const report = await api.getWorkReport(period)
  if (report) workReport.value = report
  reportLoading.value = false
}

async function copyWorkReport() {
  if (!workReport.value?.markdown) return
  try {
    await navigator.clipboard.writeText(workReport.value.markdown)
    alert('工作记录已复制，可直接粘贴到周报或月度汇报中')
  } catch {
    alert('复制失败，请手动选择内容复制')
  }
}

// Count tasks per member
onMounted(async () => {
  applyCurrentUser()
  refreshCollaborationTodos()
  if (route.query.focus === 'pending') {
    await nextTick()
    pendingSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  window.addEventListener('focus', refreshCollaborationTodos)
  if (!currentUser.value?.devOwnerName) viewScope.value = 'team'
  window.addEventListener('pm-user-login', ((e: any) => {
    currentUser.value = e.detail || {}
    viewScope.value = e.detail?.devOwnerName ? 'mine' : 'team'
    if (e.detail?.devOwnerName) activeMember.value = e.detail.devOwnerName
  }) as EventListener)
  const [r, p] = await Promise.all([api.getRequirements({}), api.getProjects()])
  if (r) {
    reqs.value = r
    // Count tasks per member
    for (const m of teamMembers) {
      const name = m.name.split('-')[1] || m.name
      m.taskCount = r.filter((req: Requirement) => req.assignee.includes(name)).length
    }
  }
  if (p) projects.value = p
})
onUnmounted(() => window.removeEventListener('focus', refreshCollaborationTodos))
return { router, route, activeMember, reqs, collaborationTodos, pendingSection, postlaunchRows, sendingOutcomeId, sendState, refreshCollaborationTodos, todoTypeLabel, openTodo, completeTodo, projects, reportOpen, reportLoading, reportPeriod, workReport, viewScope, showProjectModal, projectSaving, developerOptions, projectForm, showRequirementModal, requirementSaving, quickRequirementForm, showWorkLogModal, workLogLoading, workLogSaving, activeRequirement, workLogs, workLogForm, showDeliveryModal, deliveryLoading, deliverySaving, deliveryError, deliveryNotice, deliveryRequirement, deliveryLifecycle, deliveryPreparation, deliveryCompletion, showFeedbackModal, feedbackLoading, feedbackError, feedbackRequirement, feedbackDetail, workFilter, scopeOptions, lifecycleStatuses, requirementStatuses, quickTypeOptions, workLogTypes, workFilterOptions, currentUser, canCreateProject, deliveryBaseline, pendingDeliveryRound, passedDeliveryRound, latestDeliveryChangeRound, pendingFeedbackRoute, teamMembers, selectMember, copyOutcomeLink, sendOutcomeLink, openFeedbackPanel, closeFeedbackPanel, sendFeedbackLink, markFeedbackViewed, applyCurrentUser, searchName, myReqs, activeReqs, recentDoneReqs, dueAttentionReqs, feedbackRequests, completedReqs, feedbackPendingReqs, feedbackUnreadReqs, feedbackIssueReqs, feedbackStageItems, workList, workFilterTitle, emptyWorkText, summaryCards, setScope, myProjects, focusProjects, completedProjectCount, projectOptions, projectNeedsAttention, setWorkFilter, feedbackForRequirement, feedbackNeedsAttention, feedbackBadge, outcomeStatusClass, outcomeStatusText, outcomeSummary, statusDot, priorityColor, statusColor, statusLabel, dateKey, dateOffsetKey, isDueWithin, dueTone, dueLabel, impactLabel, workloadLabel, projectProgressPercent, projectProgressColor, updateWorkStatus, deliveryToday, loadDeliveryCard, openDeliveryCard, closeDeliveryCard, sendDeliveryConfirmation, routeDeliveryFeedback, completeDelivery, copyDeliveryLink, openRequirementCreate, saveQuickRequirement, openWorkLog, saveWorkLog, syncMine, openProjectCreate, saveProject, openWorkReport, loadWorkReport, copyWorkReport }
}
