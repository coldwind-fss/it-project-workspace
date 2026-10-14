import { SESSION_STORAGE_KEY } from '@/api/session-storage'
import { statusLabel, statusColors, pColor, normalizeStatus, sColor, rColor, tColor, impactColor, badgePalette, hashText, stableBadgeStyle, personBadgeStyle, versionBadgeStyle, splitPeople, hasPerson, samePeople, shortDateTime, parseTextField, guessOption, normalizeDateValue, progressPercent, progressLabel, progressSubLabel, progressCountText, progressBoxClass, progressTooltip } from './view'

import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
import { hasAction } from '../access/session-access'
import type { Category } from '../../types'
import { calculatePriorityAssessment, isPriorityAssessmentComplete, needsPriorityOverrideReason } from '../../utils/priorityAssessment'
import { showConfirm, showPrompt } from '../../utils/feedback'
export function useRequirementsListPage() {


const route = useRoute()
const router = useRouter()
const categories = ref<Category[]>([])
const allProjects = ref<any[]>([])
const allReqs = ref<any[]>([])
const searchText = ref('')
const sortKey = ref('')
const sortDir = ref(1)
const filterPanelOpen = ref(false)
const filters = ref({
  categoryIds: [] as string[],
  priorities: [] as string[],
  statuses: [] as string[],
  departments: [] as string[],
  devOwners: [] as string[],
})
const activeTab = ref('all')
const expandedL2s = ref<Set<string>>(new Set())
const deptDropdownOpen = ref(false)
const expandedDeptIds = ref<Set<string>>(new Set())
const contactsLoading = ref(false)
const showQuickImport = ref(false)
const quickForm = ref({ level: 'project', text: '' })
const quickDraft = ref<any>(null)
const quickDefaults = ref<any>({ priority: 'P2', status: '开发中', devOwner: '', date: '' })
const quickTarget = ref({ categoryId: '', projectId: '' })
const quickAssessmentProjectPriority = computed(() => allProjects.value.find(p => p.id === quickDraft.value?.projectId)?.priority || 'P2')
const batchMode = ref(false)
const selectedProjectIds = ref<Set<string>>(new Set())
const selectedRequirementIds = ref<Set<string>>(new Set())
const showBatchBackfill = ref(false)
const batchForm = ref({ type: '', status: '', changeObject: '', impactLevel: '', workloadLevel: '', reason: '批量补录/校正 L3 分类字段' })
const isLoading = ref(false)
const loadError = ref('')
const tableShell = ref<HTMLElement | null>(null)
const tableLayoutMode = ref<'wide' | 'compact' | 'scroll'>('compact')
let tableResizeObserver: ResizeObserver | null = null
let tableResizeFallback: (() => void) | null = null

const typeOpts = ['业务确认', '产品设计', '技术建设', '新增功能', '功能优化', '问题修复', '验证交付']
const changeObjectOptions = ['模块', '功能', '字段', '流程', '页面交互', '接口数据', '系统基础', '其他']
const impactOptions = ['核心', '重要', '常规']
const workloadOptions = ['大', '中', '小']
const priorityOptions = ['P0', 'P1', 'P2', 'P3', 'P4']
const deptTree = ref<any[]>([])
const contactUsers = ref<any[]>([])
const devOpts = ref<string[]>([])
const bizOwnerOpts = ref(['桑葚-於思旭', '玖杉-周荣', '安妮-宗艳琪'])
const lifecycleStatuses = ['待评估', '已立项', '需求确认中', '设计中', '开发中', '联调中', '测试中', '迭代中', '待上线', '已上线', '维护中', '暂停中', '已关闭', '已归档']
const requirementStatuses = ['待处理', '进行中', '待交付', '已交付', '已关闭']

const sortOptions = [
  { key: 'name', label: '名称' },
  { key: 'categoryName', label: '所属大类' },
  { key: 'priority', label: '优先级' },
  { key: 'status', label: '状态' },
  { key: 'department', label: '部门' },
  { key: 'businessOwner', label: '业务对接' },
  { key: 'devOwner', label: '开发负责人' },
  { key: 'currentVersion', label: '版本' },
  { key: 'createdAt', label: '创建时间' },
  { key: 'progress', label: '进度' },
]



















function isCrossOwnerRequirement(r: any) {
  const completedStatuses = ['已交付', '已上线', '已关闭', '已归档']
  const project = allProjects.value.find(p => p.id === r?.projectId)
  return !!(
    r?.requester && r?.assignee && !samePeople(r.requester, r.assignee) &&
    !completedStatuses.includes(r.status) &&
    !completedStatuses.includes(project?.status)
  )
}





// Tab items
const tabItems = computed(() => {
  const tabs: { id: string; label: string; count: number; color?: string }[] = [
    { id: 'all', label: '总表', count: allProjects.value.length }
  ]
  categories.value.forEach(c => {
    const cnt = allProjects.value.filter(p => p.categoryId === c.id).length
    tabs.push({ id: c.id, label: c.name, count: cnt, color: c.color })
  })
  return tabs
})

const filterOptions = computed(() => ({
  departments: Array.from(new Set(allProjects.value.map(p => p.department).filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b), 'zh-CN')),
  devOwners: Array.from(new Set(allProjects.value.flatMap(p => splitPeople(p.devOwner)))).sort((a, b) => String(a).localeCompare(String(b), 'zh-CN')),
}))

const activeFilterCount = computed(() => Object.values(filters.value).reduce((total, values) => total + values.length, 0))

const dashboardRange = computed(() => {
  const value = String(route.query.range || '')
  return ['week', 'month', 'year'].includes(value) ? value : ''
})

const dashboardPeriodWindow = computed(() => {
  if (!dashboardRange.value) return null
  const end = new Date(); end.setHours(23, 59, 59, 999)
  const start = new Date(end); start.setHours(0, 0, 0, 0)
  if (dashboardRange.value === 'week') { const day = start.getDay() || 7; start.setDate(start.getDate() - day + 1) }
  else if (dashboardRange.value === 'month') start.setDate(1)
  else start.setMonth(0, 1)
  return { start, end }
})

const dashboardProjectId = computed(() => String(route.query.projectId || ''))
const dashboardStatus = computed(() => String(route.query.status || ''))
const dashboardType = computed(() => String(route.query.type || ''))
const dashboardCreated = computed(() => String(route.query.created || ''))
const dashboardFocus = computed(() => String(route.query.focus || '') === 'true')

function dashboardDateInPeriod(value: string) {
  if (!dashboardPeriodWindow.value) return true
  if (!value) return false
  const date = new Date(String(value).replace(/-/g, '/'))
  return !Number.isNaN(date.getTime()) && date >= dashboardPeriodWindow.value.start && date <= dashboardPeriodWindow.value.end
}

function isDashboardFocusChange(row: any) {
  const aliases: Record<string, string> = { '新功能': '新增功能', '优化改进': '功能优化', 'Bug修复': '问题修复', 'UI调整': '功能优化', '技术重构': '技术建设' }
  const type = aliases[String(row.type || '')] || String(row.type || '')
  return row.impactLevel === '核心' || row.impactLevel === '重要' || row.workloadLevel === '大' || row.changeObject === '模块' || type === '新增功能' || type === '技术建设' || /重构|改造|架构|模块/.test(String(row.title || '')) || (type === '问题修复' && ['P0', 'P1'].includes(row.priority))
}

function dashboardRequirementRows(projectId = '') {
  let rows = allReqs.value.filter(row => !projectId || row.projectId === projectId)
  if (dashboardPeriodWindow.value) rows = rows.filter(row => [row.createdAt, row.updatedAt, row.completedAt].some(dashboardDateInPeriod))
  if (dashboardCreated.value === 'month' || dashboardCreated.value === 'period') {
    const now = new Date()
    const start = new Date(now.getFullYear(), now.getMonth(), 1)
    rows = rows.filter(row => {
      if (!row.createdAt) return false
      const date = new Date(String(row.createdAt).replace(/-/g, '/'))
      return !Number.isNaN(date.getTime()) && date >= start
    })
  }
  if (dashboardType.value) rows = rows.filter(row => row.type === dashboardType.value)
  if (dashboardFocus.value) rows = rows.filter(isDashboardFocusChange)
  if (dashboardStatus.value === 'delivered') rows = rows.filter(row => ['已交付', '已关闭'].includes(row.status))
  if (dashboardStatus.value === 'pending') rows = rows.filter(row => !['已交付', '已上线', '已关闭', '已归档'].includes(row.status))
  return rows
}

function categoryName(project: any) {
  return project?.categoryName || categories.value.find(c => c.id === project?.categoryId)?.name || '未分类'
}

function clearFilters() {
  filters.value = { categoryIds: [], priorities: [], statuses: [], departments: [], devOwners: [] }
}

function sortValue(project: any, key: string) {
  if (key === 'categoryName') return categoryName(project).toLocaleLowerCase()
  if (key === 'priority') return ({ P0: 0, P1: 1, P2: 2, P3: 3, P4: 4 } as Record<string, number>)[project.priority] ?? 99
  if (key === 'status') return lifecycleStatuses.indexOf(normalizeStatus(project.status)) === -1 ? 99 : lifecycleStatuses.indexOf(normalizeStatus(project.status))
  if (key === 'progress') return progressPercent(project)
  const value = project?.[key]
  return typeof value === 'string' ? value.toLocaleLowerCase() : (value ?? '')
}

// Filter projects by active tab
const displayProjects = computed(() => {
  let items = allProjects.value
  if (dashboardProjectId.value) items = items.filter(project => project.id === dashboardProjectId.value)
  if (dashboardRange.value || dashboardProjectId.value || dashboardCreated.value || dashboardType.value || dashboardFocus.value || ['delivered', 'pending'].includes(dashboardStatus.value)) items = items.filter(project => dashboardRequirementRows(project.id).length > 0)
  if (activeTab.value !== 'all') {
    items = items.filter(p => p.categoryId === activeTab.value)
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    items = items.filter(p =>
      p.name.toLowerCase().includes(q) ||
      categoryName(p).toLowerCase().includes(q) ||
      (p.department || '').toLowerCase().includes(q) ||
      (p.devOwner || '').toLowerCase().includes(q) ||
      (p.businessOwner || '').toLowerCase().includes(q)
    )
  }
  if (filters.value.categoryIds.length) items = items.filter(p => filters.value.categoryIds.includes(p.categoryId))
  if (filters.value.priorities.length) items = items.filter(p => filters.value.priorities.includes(p.priority))
  if (filters.value.statuses.length) items = items.filter(p => filters.value.statuses.includes(normalizeStatus(p.status)))
  if (filters.value.departments.length) items = items.filter(p => filters.value.departments.includes(p.department))
  if (filters.value.devOwners.length) items = items.filter(p => filters.value.devOwners.some(owner => hasPerson(p.devOwner, owner)))
  if (sortKey.value) {
    items = [...items].sort((a, b) => {
      const va = sortValue(a, sortKey.value), vb = sortValue(b, sortKey.value)
      return va > vb ? sortDir.value : va < vb ? -sortDir.value : 0
    })
  }
  return items
})

const visibleDeptOptions = computed(() => {
  const rows: any[] = []
  const walk = (nodes: any[], level: number) => {
    ;(nodes || []).forEach(node => {
      rows.push({
        id: node.id || node.name,
        name: node.name,
        level,
        hasChildren: !!node.children?.length,
      })
      if (node.children?.length && expandedDeptIds.value.has(node.id || node.name)) {
        walk(node.children, level + 1)
      }
    })
  }
  walk(deptTree.value, 0)
  return rows
})

const deptFlatOptions = computed(() => {
  const names: string[] = ['集团中台']
  const walk = (nodes: any[]) => {
    ;(nodes || []).forEach(node => {
      if (node.name && !names.includes(node.name)) names.push(node.name)
      if (node.children?.length) walk(node.children)
    })
  }
  walk(deptTree.value)
  allProjects.value.forEach(p => {
    if (p.department && !names.includes(p.department)) names.push(p.department)
  })
  return names
})

const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { return {} }
})

const currentDeveloper = computed(() => {
  const dev = currentUser.value?.devOwnerName || currentUser.value?.name || ''
  return devOpts.value.includes(dev) ? dev : ''
})
const currentUserName = computed(() => currentUser.value?.name || currentUser.value?.devOwnerName || '')

function localToday() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function findDepartmentName(departmentId: string): string {
  const find = (nodes: any[]): string => {
    for (const node of nodes || []) {
      if (String(node.id || '') === String(departmentId)) return node.name || ''
      const child = find(node.children || [])
      if (child) return child
    }
    return ''
  }
  return find(deptTree.value)
}

function currentUserDepartment() {
  const userId = currentUser.value?.dingUserId || currentUser.value?.userid || ''
  const contact = contactUsers.value.find(item => (item.userid || item.userId || item.dingUserId) === userId)
  const ids = [contact?.departmentId, ...String(currentUser.value?.department || '').split(',')].map(item => String(item || '').trim()).filter(Boolean)
  for (const id of ids) {
    const name = findDepartmentName(id)
    if (name) return name
  }
  return ''
}
const isManager = computed(() => ['admin', 'super_admin'].includes(currentUser.value?.role))
const canDelete = computed(() => isManager.value)
const canManageCategories = computed(() => hasAction('category.manage'))
const canCreate = computed(() => hasAction('requirement.create'))
const canCreateProject = computed(() => hasAction('project.create'))

function isCreatedByCurrentUser(row: any) {
  const userId = currentUser.value?.dingUserId || currentUser.value?.userid || currentUser.value?.userId || ''
  const name = currentUser.value?.name || currentUser.value?.devOwnerName || ''
  return (!!userId && row?.createdByUserId === userId) || (!!name && row?.createdByName === name)
}

function canDeleteProject(project: any) {
  return isManager.value || (hasAction('project.delete.own') && isCreatedByCurrentUser(project))
}

function canDeleteRequirement(requirement: any, _project?: any) {
  return isManager.value || (hasAction('requirement.delete.own') && isCreatedByCurrentUser(requirement))
}

function canEditProject(project: any) {
  if (isManager.value) return true
  if (!hasAction('project.update.own')) return false
  const userId = currentUser.value?.dingUserId || currentUser.value?.userid || ''
  const name = currentUser.value?.name || ''
  return (!!userId && project.createdByUserId === userId) || project.createdByName === name || hasPerson(project.businessOwner, name) || hasPerson(project.devOwner, name)
}

function canEditRequirement(requirement: any, project: any) {
  if (isManager.value) return true
  if (!hasAction('requirement.update.own')) return false
  const userId = currentUser.value?.dingUserId || currentUser.value?.userid || ''
  const name = currentUser.value?.name || ''
  return (!!userId && requirement.createdByUserId === userId) || requirement.createdByName === name || hasPerson(requirement.assignee, name) || hasPerson(requirement.requester, name) || canEditProject(project)
}

const quickMissing = computed(() => {
  if (!quickDraft.value) return []
  const missing: string[] = []
  if (!quickDraft.value.name) missing.push(quickForm.value.level === 'project' ? '项目名称' : '需求标题')
  if (quickForm.value.level === 'requirement' && !quickDraft.value.projectId && !quickDraft.value.projectName) missing.push('所属项目')
  if (!quickDraft.value.department) missing.push('部门')
  if (!quickDraft.value.devOwner) missing.push('开发负责人')
  if (!quickDraft.value.date) missing.push(quickForm.value.level === 'project' ? '目标结束时间' : '预计交付时间')
  return missing
})

function getL3Reqs(projectId: string) {
  return dashboardRequirementRows(projectId)
}

function toggleL2(id: string) {
  const s = new Set(expandedL2s.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedL2s.value = s
}

function toggleProjectSelection(id: string) {
  const s = new Set(selectedProjectIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedProjectIds.value = s
}

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedProjectIds.value = new Set()
    selectedRequirementIds.value = new Set()
  }
}

function toggleRequirementSelection(id: string) {
  const s = new Set(selectedRequirementIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedRequirementIds.value = s
}

function toggleAllProjects(event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  selectedProjectIds.value = checked ? new Set(displayProjects.value.map(p => p.id)) : new Set()
}

async function bulkDeleteRequirements() {
  if (!currentUserIsDeveloper()) { alert('只有系统管理中的开发者或管理员可以删除'); return }
  const ids = Array.from(selectedRequirementIds.value)
  if (!ids.length) return
  if (!await showConfirm(`确定批量删除 ${ids.length} 个需求？此操作会同步清理相关待办和变更记录。`)) return
  const result: any = await api.bulkDeleteRequirements(ids)
  if (!result) { alert('批量删除失败'); return }
  selectedRequirementIds.value = new Set()
  alert(`已删除 ${result.deleted?.length || 0} 个需求`)
  loadData()
}

async function bulkDeleteProjects() {
  if (!currentUserIsDeveloper()) { alert('只有系统管理中的开发者或管理员可以删除'); return }
  const ids = Array.from(selectedProjectIds.value)
  if (!ids.length) return
  if (!await showConfirm(`确定批量删除 ${ids.length} 个项目？项目下仍有需求的项目会自动跳过。`)) return
  const result: any = await api.bulkDeleteProjects(ids)
  if (!result) { alert('批量删除失败'); return }
  selectedProjectIds.value = new Set()
  const skipped = result.skipped?.length ? `，跳过 ${result.skipped.length} 个仍有需求的项目` : ''
  alert(`已删除 ${result.deleted?.length || 0} 个项目${skipped}`)
  loadData()
}

function toggleDeptNode(id: string) {
  const s = new Set(expandedDeptIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedDeptIds.value = s
}

function selectDepartment(name: string) {
  projForm.value.department = name
  deptDropdownOpen.value = false
}

function handleDepartmentClick(node: any) {
  if (node.hasChildren) {
    toggleDeptNode(node.id)
    return
  }
  selectDepartment(node.name)
}

function sortIcon(key: string) { return sortKey.value === key ? (sortDir.value > 0 ? '↑' : '↓') : '' }
function toggleSort(key: string) {
  if (sortKey.value === key) sortDir.value *= -1
  else { sortKey.value = key; sortDir.value = 1 }
}

// Navigation
function goProject(id: string) { router.push('/projects/' + id) }
function goRequirement(id: string) { router.push('/requirements/' + id) }



function quickModeClass(mode: string) {
  return ['px-3 py-1 rounded-md text-xs font-medium transition-colors', quickForm.value.level === mode ? 'bg-white text-accent-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']
}

function openQuickImport() {
  loadQuickDefaults()
  quickForm.value = { level: 'project', text: '' }
  quickTarget.value = { categoryId: activeTab.value === 'all' ? '' : activeTab.value, projectId: '' }
  quickDraft.value = null
  showQuickImport.value = true
}

function loadQuickDefaults() {
  try {
    const saved = JSON.parse(localStorage.getItem('pm-quick-defaults') || '{}')
    quickDefaults.value = { priority: 'P2', status: '开发中', devOwner: '', date: '', ...saved }
  } catch {}
}

function saveQuickDefaults() {
  localStorage.setItem('pm-quick-defaults', JSON.stringify(quickDefaults.value))
  alert('默认值已保存')
}







function parseQuickImport() {
  const text = quickForm.value.text || ''
  const categoryName = parseTextField(text, ['大类', '所属大类', '分类'])
  const projectName = parseTextField(text, ['项目名称', '项目'])
  const requirementName = parseTextField(text, ['需求标题', '需求名称', '需求', '标题', '名称'])
  const name = (quickForm.value.level === 'project' ? projectName : requirementName) || text.split(/\n/).map(x => x.trim()).find(Boolean) || ''
  const dept = parseTextField(text, ['部门', '归属部门', '业务部门', '对接部门']) || guessOption(text, deptFlatOptions.value)
  const owner = parseTextField(text, ['业务负责人', '业务对接', '提出方', '负责人']) || guessOption(text, bizOwnerOpts.value)
  const dev = parseTextField(text, ['开发负责人', '开发']) || guessOption(text, devOpts.value) || quickDefaults.value.devOwner || currentDeveloper.value
  const date = normalizeDateValue(parseTextField(text, ['预计交付', '目标结束时间', '交付时间', '日期']) || text) || quickDefaults.value.date
  quickDraft.value = {
    name,
    department: dept,
    businessOwner: owner,
    devOwner: dev,
    date,
    projectId: quickTarget.value.projectId,
    categoryId: quickTarget.value.categoryId || (activeTab.value === 'all' ? '' : activeTab.value),
    categoryName,
    projectName: projectName || '',
    description: parseTextField(text, ['描述', '需求描述', '项目描述', '内容']) || text,
    priorityEvaluation: {},
  }
  if (quickForm.value.level === 'requirement' && quickDraft.value.projectId) fillQuickProjectDefaults()
}

function readQuickImportFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { quickForm.value.text = String(reader.result || '') }
  reader.readAsText(file, 'utf-8')
  input.value = ''
}

function fillQuickProjectDefaults() {
  const p = allProjects.value.find(item => item.id === quickDraft.value?.projectId)
  if (!p || !quickDraft.value) return
  if (!quickDraft.value.department) quickDraft.value.department = p.department || ''
}

async function saveQuickImport() {
  if (quickMissing.value.length) {
    alert('请先补齐必填字段：' + quickMissing.value.join('、'))
    return
  }
  if (quickForm.value.level === 'project') {
    let categoryId = quickDraft.value.categoryId
    if (quickDraft.value.categoryName) categoryId = await ensureQuickCategory(quickDraft.value.categoryName)
    const saved = await api.createProject({
      name: quickDraft.value.name,
      description: quickDraft.value.description,
      priority: quickDefaults.value.priority || 'P2',
      status: quickDefaults.value.status || '开发中',
      department: quickDraft.value.department,
      businessOwner: quickDraft.value.businessOwner,
      devOwner: quickDraft.value.devOwner,
      currentVersion: 'v1.0.0',
      startDate: '',
      targetEndDate: quickDraft.value.date,
      categoryId, solutionType: 'unknown', lifecycleTemplate: '', complexityLevel: 'medium', createInitialL3: false,
      images: [],
    })
    if (!saved) { alert('导入失败，请检查字段'); return }
  } else {
    if (['P0', 'P1'].includes(quickDefaults.value.priority)) {
      if (!isPriorityAssessmentComplete(quickDraft.value.priorityEvaluation)) {
        alert('快速导入P0或P1需求时，请先完成4项优先级智能评估')
        return
      }
      quickDraft.value.priorityEvaluation = calculatePriorityAssessment(quickDraft.value.priorityEvaluation, quickAssessmentProjectPriority.value)
      if (needsPriorityOverrideReason(quickDefaults.value.priority, quickDraft.value.priorityEvaluation) && !String(quickDraft.value.priorityEvaluation.overrideReason || '').trim()) {
        alert('当前优先级高于系统建议，请填写调整原因')
        return
      }
    } else if (isPriorityAssessmentComplete(quickDraft.value.priorityEvaluation)) {
      quickDraft.value.priorityEvaluation = calculatePriorityAssessment(quickDraft.value.priorityEvaluation, quickAssessmentProjectPriority.value)
    }
    let projectId = quickDraft.value.projectId
    if (quickDraft.value.projectName) {
      let categoryId = quickDraft.value.categoryId
      if (quickDraft.value.categoryName) categoryId = await ensureQuickCategory(quickDraft.value.categoryName)
      projectId = await ensureQuickProject(quickDraft.value.projectName, categoryId)
    }
    if (!projectId) { alert('请先选择所属项目，或在文本中写明“项目：项目名称”'); return }
    const saved = await api.createRequirement({
      title: quickDraft.value.name,
      type: '新增功能', itemKind: 'feature',
      priority: quickDefaults.value.priority || 'P2',
      status: requirementStatuses.includes(quickDefaults.value.status) ? quickDefaults.value.status : '待处理',
      projectId,
      assignee: quickDraft.value.devOwner,
      requester: quickDraft.value.businessOwner,
      department: quickDraft.value.department,
      expectedDeliveryTime: quickDraft.value.date,
      description: quickDraft.value.description,
      acceptanceCriteria: '',
      changeObject: '功能',
      impactLevel: '常规',
      workloadLevel: '中',
      priorityEvaluation: quickDraft.value.priorityEvaluation || {},
      images: [],
    })
    if (!saved) { alert('导入失败，请检查字段'); return }
  }
  showQuickImport.value = false
  loadData()
}

async function ensureQuickCategory(name: string) {
  const existing = categories.value.find(c => c.name.trim() === name.trim())
  if (existing) return existing.id
  const created: any = await api.createCategory({ name: name.trim(), icon: '', color: '#3b82f6', description: '由快速导入自动创建', owner: [], sortOrder: categories.value.length + 1 })
  if (!created?.id) throw new Error('大类自动创建失败')
  categories.value.push({ ...created, name: name.trim(), color: '#3b82f6' } as any)
  return created.id
}

async function ensureQuickProject(name: string, categoryId: string) {
  const existing = allProjects.value.find(p => p.name.trim() === name.trim() && (!categoryId || p.categoryId === categoryId))
  if (existing) return existing.id
  const created: any = await api.createProject({
    name: name.trim(), description: '由快速导入自动创建，用于承接导入需求',
    priority: quickDefaults.value.priority || 'P2', status: quickDefaults.value.status || '开发中',
    department: quickDraft.value.department, businessOwner: quickDraft.value.businessOwner,
    devOwner: quickDraft.value.devOwner, currentVersion: 'v1.0.0', startDate: '',
    targetEndDate: quickDraft.value.date, categoryId, images: [], solutionType: 'unknown', createInitialL3: false,
  })
  if (!created?.id) throw new Error('项目自动创建失败')
  allProjects.value.unshift({ ...created, name: name.trim(), categoryId, department: quickDraft.value.department })
  return created.id
}

function downloadCsv(filename: string, rows: string[][]) {
  const csv = '\ufeff' + rows.map(row => row.map(value => `"${String(value ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

function exportProjects() {
  const rows = [['项目名称', '所属大类', '状态', '优先级', '归属部门', '业务负责人', '开发负责人', '版本', '目标结束时间', '创建时间', '需求描述']]
  displayProjects.value.forEach(p => rows.push([p.name, p.categoryName || '', p.status, p.priority, p.department, p.businessOwner, p.devOwner, p.currentVersion, p.targetEndDate, p.createdAt, p.description]))
  downloadCsv(`项目导出_${new Date().toISOString().slice(0, 10)}.csv`, rows)
}

function exportRequirements() {
  const visibleProjectIds = new Set(displayProjects.value.map(p => p.id))
  const rows = [['需求标题', '所属项目', '类型', '状态', '优先级', '归属部门', '提出方', '开发负责人', '预计交付时间', '创建时间', '需求描述']]
  allReqs.value.filter(r => activeTab.value === 'all' || visibleProjectIds.has(r.projectId)).forEach(r => rows.push([r.title, r.pname || r.projectName || '', r.type, r.status, r.priority, r.department, r.requester, r.assignee, r.expectedDeliveryTime, r.createdAt, r.description]))
  downloadCsv(`需求导出_${new Date().toISOString().slice(0, 10)}.csv`, rows)
}

// Get category color
function getCatColor(catId: string) {
  return categories.value.find(c => c.id === catId)?.color || '#3b82f6'
}









function progressColor(p: any) {
  const pg = p.progress || {}
  if (pg.mode === 'empty') return '#d1d5db'
  if (pg.mode === 'released' || progressPercent(p) >= 100) return '#10b981'
  if ((pg.subLabel || '').includes('暂停')) return '#f97316'
  if (progressPercent(p) >= 70) return '#14b8a6'
  if (progressPercent(p) >= 30) return '#3b82f6'
  return getCatColor(p.categoryId)
}





// CRUD: Category
const showCreateCategory = ref(false)
const editingCategory = ref<Category | null>(null)
const catForm = ref<any>({ name: '', icon: '', description: '', color: '#3b82f6', owner: [], sortOrder: 0 })

function editCategory(c: Category) {
  editingCategory.value = c
  catForm.value = { name: c.name, icon: c.icon, description: c.description, color: c.color, owner: c.owner || [], sortOrder: c.sortOrder }
}
function closeCategoryModal() { showCreateCategory.value = false; editingCategory.value = null; catForm.value = { name: '', icon: '', description: '', color: '#3b82f6', owner: [], sortOrder: 0 } }
async function saveCategory() {
  const data = { ...catForm.value, owner: [...(catForm.value.owner || [])] }
  const saved = editingCategory.value ? await api.updateCategory(editingCategory.value.id, data) : await api.createCategory(data)
  if (!saved) { alert('保存失败，请检查名称是否填写完整'); return }
  closeCategoryModal(); loadData()
}
async function deleteCategory(c: Category) {
  if (!currentUserIsDeveloper()) { alert('只有系统管理中的开发者或管理员可以删除'); return }
  if (!await showConfirm(`确定删除大类「${c.name}」？`)) return
  const r = await api.deleteCategory(c.id)
  if (!r) alert('删除失败，请先删除该大类下的项目')
  else loadData()
}
function deleteCategoryById(id: string) {
  const c = categories.value.find(item => item.id === id)
  if (c) deleteCategory(c)
}

// CRUD: Project
const showCreateProject = ref(false)
const editingProject = ref<any>(null)
const projForm = ref<any>({})
const solutionTypeOptions = ref<any[]>([])
const itemKindOptions = ref<any[]>([
  { key: 'initial_build', label: '初始建设' }, { key: 'feature', label: '新功能 / 模块' },
  { key: 'bugfix', label: '问题修复' }, { key: 'enhancement', label: '功能优化' },
  { key: 'integration', label: '接口 / 数据集成' }, { key: 'design', label: '产品设计' },
  { key: 'operation', label: '运营维护' },
])
const lifecycleTemplates = ref<Record<string, any[]>>({})
const phaseTemplatesForForm = computed(() => lifecycleTemplates.value[projForm.value.solutionType] || [])

function onProjectSolutionTypeChange() {
  const phases = phaseTemplatesForForm.value
  if (projForm.value.solutionType === 'unknown') {
    projForm.value.createInitialL3 = false
    projForm.value.phaseTemplateKeys = []
    return
  }
  if (!editingProject.value && phases.length) {
    projForm.value.createInitialL3 = true
    projForm.value.phaseTemplateKeys = phases.map(item => item.phaseKey)
  }
}

async function createProject() {
  showCreateProject.value = true
  const defaultCategoryId = activeTab.value === 'all' ? '' : activeTab.value
  projForm.value = {
    name: '', description: '', priority: 'P2', status: '开发中',
    department: '', businessOwner: '', devOwner: currentDeveloper.value, categoryId: defaultCategoryId,
    currentVersion: 'v1.0.0', startDate: '', targetEndDate: '', images: [], solutionType: 'unknown',
    lifecycleTemplate: '', complexityLevel: 'medium', createInitialL3: false, phaseTemplateKeys: []
  }
  if (deptTree.value.length === 0 || bizOwnerOpts.value.length <= 3) loadContactOptions()
}
function editProject(p: any) { editingProject.value = p; projForm.value = { ...p, images: p.images || [], phaseTemplateKeys: [], createInitialL3: false, solutionType: p.solutionType || 'unknown' } }
function closeProjectModal() { showCreateProject.value = false; editingProject.value = null }
async function saveProject() {
  if (!projForm.value.department || !projForm.value.devOwner || !projForm.value.targetEndDate) {
    alert('部门、开发负责人、目标结束时间为必填项')
    return
  }
  const saved = editingProject.value
    ? await api.updateProject(editingProject.value.id, projForm.value)
    : await api.createProject(projForm.value)
  if (!saved) {
    alert('保存失败，请检查必填字段')
    return
  }
  closeProjectModal(); loadData()
}
async function updateProjectField(p: any, field: string) { await api.updateProject(p.id, { [field]: p[field] }) }
async function deleteProject(p: any) {
  if (!canDeleteProject(p)) { alert('只能删除自己创建的项目'); return }
  if (!await showConfirm(`确定删除项目「${p.name}」？该项目下必须没有需求才能删除。`)) return
  const result: any = await api.deleteProject(p.id)
  if (!result) { alert('删除失败，请确认项目下没有未删除的需求'); return }
  loadData()
}

// CRUD: Requirement
const showCreateReq = ref(false)
const editingReq = ref<any>(null)
const reqForm = ref<any>({})
const reqAssessmentProjectPriority = computed(() => allProjects.value.find(p => p.id === reqForm.value.projectId)?.priority || 'P2')

function createRequirement(projId: string) {
  showCreateReq.value = true
  const project = allProjects.value.find(p => p.id === projId)
  reqForm.value = {
    title: '', type: '新增功能', itemKind: 'feature', priority: 'P2', status: '待处理',
    projectId: projId, assignee: currentDeveloper.value || project?.devOwner || '', requester: currentUserName.value,
    department: currentUserDepartment() || project?.department || '',
    description: '', acceptanceCriteria: '', expectedDeliveryTime: localToday(), storyPoints: 0, labels: '', images: [],
    changeObject: '功能', impactLevel: '常规', workloadLevel: '中',
    priorityEvaluation: {},
  }
  if (deptTree.value.length === 0 || contactUsers.value.length === 0) loadContactOptions()
}
async function editRequirement(r: any) {
  // The list response omits Base64 attachments. Fetching the detail before an
  // edit ensures saving an unrelated field never clears existing attachments.
  const detail = await api.getRequirement(r.id)
  if (!detail) {
    alert('需求详情加载失败，请稍后重试')
    return
  }
  editingReq.value = detail
  const project = allProjects.value.find(p => p.id === detail.projectId)
  reqForm.value = {
    ...detail,
    department: detail.department || detail.projectDepartment || project?.department || '',
    assignee: detail.assignee || currentDeveloper.value || project?.devOwner || '',
    expectedDeliveryTime: detail.expectedDeliveryTime || project?.targetEndDate || '',
    images: detail.images || [],
    priorityEvaluation: detail.priorityEvaluation || {},
  }
}
function closeReqModal() { showCreateReq.value = false; editingReq.value = null }
function syncReqProjectDefaults() {
  const project = allProjects.value.find(p => p.id === reqForm.value.projectId)
  if (!project) return
  if (!reqForm.value.department) reqForm.value.department = project.department || ''
  if (!reqForm.value.assignee) reqForm.value.assignee = project.devOwner || ''
  if (!reqForm.value.expectedDeliveryTime) reqForm.value.expectedDeliveryTime = project.targetEndDate || ''
}
function isStatusOnlyRequirementEdit() {
  if (!editingReq.value) return false
  const changedKeys = ['title', 'type', 'itemKind', 'parentRequirementId', 'versionTarget', 'priority', 'projectId', 'assignee', 'requester', 'department', 'description', 'acceptanceCriteria', 'expectedDeliveryTime', 'changeObject', 'impactLevel', 'workloadLevel']
    .filter(key => String(reqForm.value[key] || '') !== String(editingReq.value[key] || ''))
  const imagesChanged = JSON.stringify(reqForm.value.images || []) !== JSON.stringify(editingReq.value.images || [])
  const assessmentChanged = JSON.stringify(reqForm.value.priorityEvaluation || {}) !== JSON.stringify(editingReq.value.priorityEvaluation || {})
  return reqForm.value.status !== editingReq.value.status && changedKeys.length === 0 && !imagesChanged && !assessmentChanged
}
async function saveRequirement() {
  const statusOnly = isStatusOnlyRequirementEdit()
  const priorityChanged = !editingReq.value || reqForm.value.priority !== editingReq.value.priority
  if (priorityChanged && ['P0', 'P1'].includes(reqForm.value.priority)) {
    if (!isPriorityAssessmentComplete(reqForm.value.priorityEvaluation)) {
      alert('选择P0或P1时，请先完成4项优先级智能评估')
      return
    }
    reqForm.value.priorityEvaluation = calculatePriorityAssessment(reqForm.value.priorityEvaluation, reqAssessmentProjectPriority.value)
    if (needsPriorityOverrideReason(reqForm.value.priority, reqForm.value.priorityEvaluation) && !String(reqForm.value.priorityEvaluation.overrideReason || '').trim()) {
      alert('当前优先级高于系统建议，请填写调整原因')
      return
    }
  } else if (isPriorityAssessmentComplete(reqForm.value.priorityEvaluation)) {
    reqForm.value.priorityEvaluation = calculatePriorityAssessment(reqForm.value.priorityEvaluation, reqAssessmentProjectPriority.value)
  }
  if (!statusOnly && (!reqForm.value.department || !reqForm.value.assignee || !reqForm.value.expectedDeliveryTime)) {
    alert('归属部门、开发负责人、预计交付时间为必填项')
    return
  }
  if (editingReq.value) {
    let payload: any = statusOnly ? { status: reqForm.value.status } : { ...reqForm.value }
    if (!statusOnly && reqForm.value.priority !== editingReq.value.priority && !payload.reason) {
      const evaluation = reqForm.value.priorityEvaluation || {}
      payload.reason = evaluation.overrideReason || (evaluation.recommendedPriority ? `智能评估建议${evaluation.recommendedPriority}（${evaluation.score}分）` : '调整需求优先级')
    }
    if (reqForm.value.status !== editingReq.value.status) {
      const reason = await showPrompt(`状态将从「${editingReq.value.status}」变更为「${payload.status}」，请填写调整说明`, { title: '填写状态调整说明', placeholder: '请输入本次状态变更原因' })
      if (!reason?.trim()) {
        alert('状态变更需要填写调整说明')
        return
      }
      payload.reason = reason.trim()
    }
    const saved = await api.updateRequirement(editingReq.value.id, payload)
    if (!saved) { alert('保存失败，请检查必填字段'); return }
  } else {
    const saved = await api.createRequirement(reqForm.value)
    if (!saved) { alert('创建失败，请检查必填字段'); return }
  }
  closeReqModal(); loadData()
}
async function deleteRequirement(r: any) {
  if (!canDeleteRequirement(r)) { alert('只能删除自己创建的需求'); return }
  if (!await showConfirm(`确定删除需求「${r.title}」？`)) return
  const result: any = await api.deleteRequirement(r.id)
  if (!result) { alert('删除失败，请稍后重试'); return }
  loadData()
}

function openBatchBackfill() {
  batchForm.value = { type: '', status: '', changeObject: '', impactLevel: '', workloadLevel: '', reason: '批量补录/校正 L3 分类字段' }
  showBatchBackfill.value = true
}

function closeBatchBackfill() {
  showBatchBackfill.value = false
}

async function saveBatchBackfill() {
  const payload: any = { reason: String(batchForm.value.reason || '').trim() || '批量补录/校正 L3 分类字段' }
  for (const field of ['type', 'status', 'changeObject', 'impactLevel', 'workloadLevel']) {
    const value = (batchForm.value as any)[field]
    if (value) payload[field] = value
  }
  if (Object.keys(payload).length === 1) {
    alert('请至少选择一个需要补录的字段')
    return
  }
  const result: any = await api.bulkUpdateRequirementClassification(Array.from(selectedRequirementIds.value), payload)
  if (!result) {
    alert('批量补录失败，请检查登录状态和编辑权限')
    return
  }
  const updated = result.updated?.length || 0
  const skipped = result.skipped?.length || 0
  closeBatchBackfill()
  selectedRequirementIds.value = new Set()
  await loadData()
  alert(`批量补录完成：成功 ${updated} 条，跳过 ${skipped} 条`)
}

function currentUserIsDeveloper() {
  return canDelete.value
}

// Image preview
const previewModal = ref({ images: [] as any[], index: 0, open: false })
function previewImages(imgs: any[], index = 0) { previewModal.value = { images: imgs || [], index, open: true } }
async function previewRequirementImages(r: any) {
  const detail = await api.getRequirement(r.id)
  if (!detail) {
    alert('附件加载失败，请稍后重试')
    return
  }
  previewImages(detail.images || [])
}
function imageSrc(img: any) { return img?.data || img?.url || img }

function handleImageUpload(event: Event, target: any) {
  const input = event.target as HTMLInputElement
  appendImageFiles(Array.from(input.files || []), target)
  input.value = ''
}

function handleImagePaste(event: ClipboardEvent, target: any) {
  if (event.defaultPrevented) return
  const files = Array.from(event.clipboardData?.files || [])
  if (!files.some(file => file.type.startsWith('image/'))) return
  event.preventDefault()
  appendImageFiles(files, target)
}

function appendImageFiles(files: File[], target: any) {
  const imageFiles = files.filter(file => file.type.startsWith('image/'))
  if (!imageFiles.length) return
  if (!target.images) target.images = []
  imageFiles.forEach(file => {
    const reader = new FileReader()
    reader.onload = () => {
      target.images.push({
        id: 'img' + Date.now() + Math.random().toString(16).slice(2),
        name: file.name,
        type: file.type,
        data: String(reader.result || ''),
      })
    }
    reader.readAsDataURL(file)
  })
}

function handleWindowImagePaste(event: ClipboardEvent) {
  if (event.defaultPrevented) return
  if (showCreateProject.value || editingProject.value) {
    handleImagePaste(event, projForm.value)
  } else if (showCreateReq.value || editingReq.value) {
    handleImagePaste(event, reqForm.value)
  }
}

function removeImage(target: any, index: number) {
  target.images = [...(target.images || [])]
  target.images.splice(index, 1)
}

async function loadData() {
  if (isLoading.value) return
  isLoading.value = true
  loadError.value = ''
  try {
    const [cats, projects, reqs, lifecycle] = await Promise.all([
      api.getCategories(), api.getProjects(), api.getRequirements({}), api.getProjectLifecycleOptions()
    ])
    if (!cats || !projects || !reqs) {
      loadError.value = '项目数据加载失败，数据未被清空，请检查网络后重新加载。'
      return
    }
    categories.value = cats
    allProjects.value = projects
    allReqs.value = reqs
    if (lifecycle) {
      solutionTypeOptions.value = lifecycle.solutionTypes || solutionTypeOptions.value
      itemKindOptions.value = lifecycle.itemKinds || itemKindOptions.value
      lifecycleTemplates.value = lifecycle.templates || lifecycleTemplates.value
    }
    selectedProjectIds.value = new Set([...selectedProjectIds.value].filter(id => allProjects.value.some(p => p.id === id)))
    selectedRequirementIds.value = new Set([...selectedRequirementIds.value].filter(id => allReqs.value.some(r => r.id === id)))
  } finally {
    isLoading.value = false
  }
}

async function loadContactOptions() {
  if (contactsLoading.value) return
  contactsLoading.value = true
  const opts = await api.getDingTalkOptions()
  if (opts) {
    if (opts.source === 'dingtalk' && opts.departmentTree?.length) {
      deptTree.value = opts.departmentTree
      if (expandedDeptIds.value.size === 0) {
        expandedDeptIds.value = new Set(opts.departmentTree.map((n: any) => n.id || n.name))
      }
    }
    contactUsers.value = opts.users || []
    if (opts.developers?.length) devOpts.value = Array.from(new Set(opts.developers.map((d: any) => d.name || d.devOwnerName).filter(Boolean)))
    const people = [
      ...(opts.businessOwners || []),
      ...((opts.users || []).map((u: any) => u.name).filter(Boolean)),
    ]
    if (people.length) bizOwnerOpts.value = Array.from(new Set(people))
    // The dialog can be opened before the DingTalk organization response
    // returns. Fill only blank values so a user's manual selection is kept.
    if (showCreateReq.value && !editingReq.value) {
      if (!reqForm.value.requester) reqForm.value.requester = currentUserName.value
      if (!reqForm.value.department) reqForm.value.department = currentUserDepartment()
    }
  }
  contactsLoading.value = false
}

function syncTableLayout(width: number) {
  const shell = tableShell.value
  if (!shell || !Number.isFinite(width) || width <= 0) return

  const mode = width >= 1580 ? 'wide' : width >= 1320 ? 'compact' : 'scroll'
  tableLayoutMode.value = mode

  // Continuously tighten cell gutters as the embedded DingTalk canvas narrows.
  const paddingPx = Math.max(4, Math.min(10, Math.round(width / 180)))
  shell.style.setProperty('--l2-cell-x-padding', `${paddingPx}px`)
  shell.style.setProperty('--l2-table-width', `${mode === 'scroll' ? 1480 : Math.round(width)}px`)
}

function observeTableLayout() {
  const shell = tableShell.value
  if (!shell) return

  const measure = () => syncTableLayout(shell.clientWidth)
  measure()
  if (typeof ResizeObserver !== 'undefined') {
    tableResizeObserver = new ResizeObserver(entries => {
      const width = entries[0]?.contentRect.width || shell.clientWidth
      syncTableLayout(width)
    })
    tableResizeObserver.observe(shell)
  } else {
    tableResizeFallback = measure
    window.addEventListener('resize', measure)
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('paste', handleWindowImagePaste)
  nextTick(observeTableLayout)
})

onUnmounted(() => {
  window.removeEventListener('paste', handleWindowImagePaste)
  if (tableResizeObserver) tableResizeObserver.disconnect()
  if (tableResizeFallback) window.removeEventListener('resize', tableResizeFallback)
})
return { route, router, categories, allProjects, allReqs, searchText, sortKey, sortDir, filterPanelOpen, filters, activeTab, expandedL2s, deptDropdownOpen, expandedDeptIds, contactsLoading, showQuickImport, quickForm, quickDraft, quickDefaults, quickTarget, quickAssessmentProjectPriority, batchMode, selectedProjectIds, selectedRequirementIds, showBatchBackfill, batchForm, isLoading, loadError, tableShell, tableLayoutMode, tableResizeObserver, tableResizeFallback, typeOpts, changeObjectOptions, impactOptions, workloadOptions, priorityOptions, deptTree, contactUsers, devOpts, bizOwnerOpts, lifecycleStatuses, requirementStatuses, statusLabel, sortOptions, statusColors, pColor, normalizeStatus, sColor, rColor, tColor, impactColor, badgePalette, hashText, stableBadgeStyle, personBadgeStyle, versionBadgeStyle, isCrossOwnerRequirement, splitPeople, hasPerson, samePeople, tabItems, filterOptions, activeFilterCount, dashboardRange, dashboardPeriodWindow, dashboardProjectId, dashboardStatus, dashboardType, dashboardCreated, dashboardFocus, dashboardDateInPeriod, isDashboardFocusChange, dashboardRequirementRows, categoryName, clearFilters, sortValue, displayProjects, visibleDeptOptions, deptFlatOptions, currentUser, currentDeveloper, currentUserName, localToday, findDepartmentName, currentUserDepartment, isManager, canDelete, canManageCategories, canCreate, canCreateProject, isCreatedByCurrentUser, canDeleteProject, canDeleteRequirement, canEditProject, canEditRequirement, quickMissing, getL3Reqs, toggleL2, toggleProjectSelection, toggleBatchMode, toggleRequirementSelection, toggleAllProjects, bulkDeleteRequirements, bulkDeleteProjects, toggleDeptNode, selectDepartment, handleDepartmentClick, sortIcon, toggleSort, goProject, goRequirement, shortDateTime, quickModeClass, openQuickImport, loadQuickDefaults, saveQuickDefaults, parseTextField, guessOption, normalizeDateValue, parseQuickImport, readQuickImportFile, fillQuickProjectDefaults, saveQuickImport, ensureQuickCategory, ensureQuickProject, downloadCsv, exportProjects, exportRequirements, getCatColor, progressPercent, progressLabel, progressSubLabel, progressCountText, progressColor, progressBoxClass, progressTooltip, showCreateCategory, editingCategory, catForm, editCategory, closeCategoryModal, saveCategory, deleteCategory, deleteCategoryById, showCreateProject, editingProject, projForm, solutionTypeOptions, itemKindOptions, lifecycleTemplates, phaseTemplatesForForm, onProjectSolutionTypeChange, createProject, editProject, closeProjectModal, saveProject, updateProjectField, deleteProject, showCreateReq, editingReq, reqForm, reqAssessmentProjectPriority, createRequirement, editRequirement, closeReqModal, syncReqProjectDefaults, isStatusOnlyRequirementEdit, saveRequirement, deleteRequirement, openBatchBackfill, closeBatchBackfill, saveBatchBackfill, currentUserIsDeveloper, previewModal, previewImages, previewRequirementImages, imageSrc, handleImageUpload, handleImagePaste, appendImageFiles, handleWindowImagePaste, removeImage, loadData, loadContactOptions, syncTableLayout, observeTableLayout }
}
