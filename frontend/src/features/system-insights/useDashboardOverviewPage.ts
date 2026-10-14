
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FolderKanban, PackageCheck, PlusCircle, Send, Sparkles, Users } from 'lucide-vue-next'
import { api } from '../../api/application-api'
export function useDashboardOverviewPage(){


const route = useRoute()
const router = useRouter()
const loading = ref(true)
const projects = ref<any[]>([])
const requirements = ref<any[]>([])
const selectedDeveloper = ref('')
const hoveredCard = ref('')

type DashboardRange = 'week' | 'month' | 'year'
const validRanges: DashboardRange[] = ['week', 'month', 'year']
const initialRange = String(route.query.range || 'month') as DashboardRange
const dashboardRange = ref<DashboardRange>(validRanges.includes(initialRange) ? initialRange : 'month')
const periodOptions = [{ label: '本周', value: 'week' as DashboardRange }, { label: '本月', value: 'month' as DashboardRange }, { label: '本年', value: 'year' as DashboardRange }]
const terminalStatuses = new Set(['已交付', '已关闭', '已上线', '已归档'])
const workloadWeights: Record<string, number> = { 大: 3, 中: 2, 小: 1 }
const impactWeights: Record<string, number> = { 核心: 30, 重要: 20, 常规: 10 }
const preferredDevelopers = ['十叶-冯硕硕', '星河-李子文', '惜君-吴旭骏']
const visibleWorkTypes = ['业务确认', '产品设计', '技术建设', '新增功能', '功能优化', '问题修复', '验证交付']
const legacyTypeAliases: Record<string, string> = {
  '新功能': '新增功能', '优化改进': '功能优化', 'Bug修复': '问题修复', 'UI调整': '功能优化',
  '接口对接': '技术建设', '技术重构': '技术建设', '需求变更': '业务确认', '需求对接': '业务确认',
  '技术方案验证': '技术建设', '功能测试': '验证交付',
}

watch(() => route.query.range, value => {
  const next = String(value || '') as DashboardRange
  if (validRanges.includes(next) && next !== dashboardRange.value) dashboardRange.value = next
})

function setDashboardRange(value: DashboardRange) {
  dashboardRange.value = value
  router.replace({ path: '/dashboard', query: { range: value } })
}

function dashboardQuery(extra: Record<string, string> = {}) { return { range: dashboardRange.value, from: 'dashboard', ...extra } }
function monthQuery(extra: Record<string, string> = {}) { return { range: 'month', from: 'dashboard', ...extra } }
function openProduct(id: string) { if (id) router.push({ path: '/projects/' + id, query: dashboardQuery() }) }
function openProductLedger(id: string) { if (id) router.push({ path: '/requirements', query: dashboardQuery({ projectId: id }) }) }
function openRequirement(id: string) { if (id) router.push({ path: '/requirements/' + id, query: dashboardQuery() }) }
function openWorkspace(view = 'workload') { router.push({ path: '/workspace', query: dashboardQuery({ view }) }) }

function openCardRoute(key: string) {
  if (key === 'activeProjects') return router.push({ path: '/products', query: { from: 'dashboard', view: 'active' } })
  if (key === 'monthlyNewRequirements') return router.push({ path: '/requirements', query: dashboardQuery({ created: 'period' }) })
  if (key === 'focusChanges') return router.push({ path: '/requirements', query: dashboardQuery({ focus: 'true' }) })
  if (key === 'productUpdates') return router.push({ path: '/products', query: dashboardQuery({ view: 'changed' }) })
}

function openPopoverRow(row: any) {
  if (row.type === 'product') return openProduct(row.id)
  if (row.type === 'requirement') return openRequirement(row.id)
  if (row.type === 'developer') return openWorkspace('workload')
  if (row.type === 'release') return router.push({ path: '/sprints', query: monthQuery() })
}

function parseDate(value: string) {
  if (!value) return null
  const date = new Date(String(value).replace(/-/g, '/'))
  return Number.isNaN(date.getTime()) ? null : date
}

const periodWindow = computed(() => {
  const end = new Date(); end.setHours(23, 59, 59, 999)
  const start = new Date(end); start.setHours(0, 0, 0, 0)
  if (dashboardRange.value === 'week') { const day = start.getDay() || 7; start.setDate(start.getDate() - day + 1) }
  else if (dashboardRange.value === 'month') start.setDate(1)
  else start.setMonth(0, 1)
  return { start, end }
})

const periodLabel = computed(() => {
  const format = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  return `${format(periodWindow.value.start)} 至 ${format(periodWindow.value.end)}`
})

function inPeriod(value: string) { const date = parseDate(value); return !!date && date >= periodWindow.value.start && date <= periodWindow.value.end }
function requirementInPeriod(row: any) { return [row.createdAt, row.updatedAt, row.completedAt].some(value => inPeriod(value)) }
const periodRequirements = computed(() => requirements.value.filter(requirementInPeriod))

function isActiveProject(project: any) { return !['已归档', '已关闭', 'archived'].includes(String(project?.status || '')) }
const activeProjectList = computed(() => projects.value.filter(isActiveProject))
const periodNewRequirementList = computed(() => requirements.value.filter(row => inPeriod(row.createdAt)))

function splitPeople(value: string) { return String(value || '').split(/[,，]/).map(item => item.trim()).filter(Boolean) }
function matchesPerson(row: any, name: string) { return splitPeople(row.assignee).includes(name) || String(row.assignee || '').includes(name) }
function normalizedType(value: string) { return legacyTypeAliases[String(value || '')] || String(value || '') }

// Product importance is derived from L3 fields for the projection only; the ledger itself is unchanged.
function displayTier(row: any) {
  const type = normalizedType(row.type)
  const object = String(row.changeObject || '')
  const title = String(row.title || '')
  const highObject = ['模块', '功能', '系统基础'].includes(object)
  const structuralChange = /重构|改造|架构|模块/.test(title)
  if ((type === '新增功能' && highObject) || type === '技术建设' || structuralChange || row.impactLevel === '核心' || row.workloadLevel === '大' || (type === '问题修复' && ['P0', 'P1'].includes(row.priority))) return 3
  if (type === '新增功能' || type === '功能优化' || type === '问题修复' || row.impactLevel === '重要' || row.workloadLevel === '中') return 2
  return 1
}

function changeScore(row: any) { return (impactWeights[row.impactLevel] || 10) + (workloadWeights[row.workloadLevel] || 2) + displayTier(row) * 5 + (normalizedType(row.type) === '新增功能' ? 4 : 0) }
function isFocusChange(row: any) { return displayTier(row) === 3 }
const changedProductIds = computed(() => new Set(periodRequirements.value.map(row => row.projectId).filter(Boolean)))
const changedProductCount = computed(() => changedProductIds.value.size)
const totalWorkloadScore = computed(() => periodRequirements.value.reduce((sum, row) => sum + (workloadWeights[row.workloadLevel] || 2), 0))
const doneCount = computed(() => periodRequirements.value.filter(row => terminalStatuses.has(row.status)).length)
function projectForRow(row: any) { return projects.value.find(item => item.id === row.projectId) }
function rowProjectName(row: any, project: any) { return row.projectName || row.pname || project?.name || '未归属产品' }
function sortedRows(rows: any[]) { return [...rows].sort((a, b) => displayTier(b) - displayTier(a) || changeScore(b) - changeScore(a) || String(b.updatedAt || '').localeCompare(String(a.updatedAt || ''))) }

const productChangeGroups = computed(() => {
  const map = new Map<string, any>()
  periodRequirements.value.forEach(row => {
    const project = projectForRow(row)
    const key = row.projectId || row.projectName || row.pname || 'unassigned'
    if (!map.has(key)) map.set(key, { key, projectId: row.projectId, name: rowProjectName(row, project), categoryName: project?.categoryName || row.cname || '', project, rows: [] })
    map.get(key).rows.push(row)
  })
  return Array.from(map.values()).map(group => {
    const rows = sortedRows(group.rows)
    const highlights = rows.filter(row => displayTier(row) === 3)
    const supporting = rows.filter(row => displayTier(row) === 2)
    const ordinary = rows.filter(row => displayTier(row) === 1)
    const displayChanges = highlights.length
      ? [...highlights.slice(0, 3), ...supporting.slice(0, 2)]
      : [...supporting.slice(0, 3), ...ordinary.slice(0, 2)]
    const count = (type: string) => rows.filter(row => normalizedType(row.type) === type).length
    return {
      ...group, rows, totalCount: rows.length, workloadScore: rows.reduce((sum, row) => sum + (workloadWeights[row.workloadLevel] || 2), 0), focusCount: highlights.length, highlights, supporting, ordinary, displayChanges,
      otherCount: Math.max(0, rows.length - displayChanges.length), deliveredCount: rows.filter(row => terminalStatuses.has(row.status)).length,
      changeSummary: [
        { label: '新增功能', value: count('新增功能'), color: '#2563eb' },
        { label: '功能优化', value: count('功能优化'), color: '#d97706' },
        { label: '技术建设', value: count('技术建设'), color: '#64748b' },
        { label: '问题修复', value: count('问题修复'), color: '#dc2626' },
        { label: '交付', value: count('验证交付'), color: '#0f766e' },
      ],
      lifecycleStages: [
        { label: '确认', value: count('业务确认') }, { label: '设计', value: count('产品设计') },
        { label: '建设', value: count('技术建设') }, { label: '能力变化', value: count('新增功能') + count('功能优化') + count('问题修复') }, { label: '交付', value: count('验证交付') },
      ],
    }
  }).sort((a, b) => b.focusCount - a.focusCount || changeScore(b.rows[0]) - changeScore(a.rows[0]) || a.name.localeCompare(b.name, 'zh-CN'))
})

const focusProductCount = computed(() => productChangeGroups.value.filter(group => group.focusCount > 0).length)
const deliveredProductGroups = computed(() => productChangeGroups.value.filter(group => group.deliveredCount > 0).sort((a, b) => b.deliveredCount - a.deliveredCount))
const focusChangeList = computed(() => sortedRows(periodRequirements.value.filter(isFocusChange)))

const overviewStats = computed(() => [
  { key: 'activeProjects', label: '进行中项目', value: activeProjectList.value.length, desc: '全系统活跃 L2 项目', popoverTitle: '进行中项目', icon: FolderKanban, bg: 'bg-blue-50', iconClass: 'text-blue-500' },
  { key: 'monthlyNewRequirements', label: '本期新增需求', value: periodNewRequirementList.value.length, desc: '当前统计周期创建的 L3 需求', popoverTitle: '本期新增需求', icon: PlusCircle, bg: 'bg-violet-50', iconClass: 'text-violet-500' },
  { key: 'focusChanges', label: '本期重点变化', value: focusChangeList.value.length, desc: '核心、重要或大工作量 L3', popoverTitle: '本期重点变化', icon: Sparkles, bg: 'bg-red-50', iconClass: 'text-red-500' },
  { key: 'productUpdates', label: '本期产品更新', value: changedProductCount.value, desc: '发生 L3 变化的 L2 产品', popoverTitle: '本期产品更新', icon: PackageCheck, bg: 'bg-emerald-50', iconClass: 'text-emerald-500' },
])

const preferredDeveloperNames = computed(() => {
  const names = new Set<string>()
  requirements.value.forEach(row => splitPeople(row.assignee).forEach(name => { if (name && name !== '待分配') names.add(name) }))
  projects.value.forEach(row => splitPeople(row.devOwner).forEach(name => { if (name && name !== '待分配') names.add(name) }))
  return [...preferredDevelopers, ...Array.from(names)].filter((name, index, list) => list.indexOf(name) === index).slice(0, 3)
})
const developerRows = computed(() => preferredDeveloperNames.value.map(name => {
  const rows = periodRequirements.value.filter(row => matchesPerson(row, name))
  const focusRows = sortedRows(rows.filter(isFocusChange))
  return { name, recordCount: rows.length, doneCount: rows.filter(row => terminalStatuses.has(row.status)).length, focusCount: focusRows.length, productCount: new Set(rows.map(row => row.projectId).filter(Boolean)).size, workloadScore: rows.reduce((sum, row) => sum + (workloadWeights[row.workloadLevel] || 2), 0), largeCount: rows.filter(row => row.workloadLevel === '大').length, mediumCount: rows.filter(row => row.workloadLevel === '中').length, smallCount: rows.filter(row => row.workloadLevel === '小').length, focusRows, workRows: sortedRows(rows).slice(0, 3), otherWorkCount: Math.max(0, rows.length - 3) }
}))
const selectedDeveloperDetails = computed(() => selectedDeveloper.value ? sortedRows(periodRequirements.value.filter(row => matchesPerson(row, selectedDeveloper.value))).slice(0, 30) : [])

function cardPopoverRows(key: string) {
  if (key === 'activeProjects') return activeProjectList.value.map(row => ({ key: row.id, type: 'product', id: row.id, label: row.name, meta: projectStatusLabel(row.status) }))
  if (key === 'monthlyNewRequirements') return periodNewRequirementList.value.map(row => ({ key: row.id, type: 'requirement', id: row.id, label: row.title, meta: `${row.projectName || row.pname || '未归属产品'} · ${displayType(row)}` }))
  if (key === 'focusChanges') return focusChangeList.value.map(row => ({ key: row.id, type: 'requirement', id: row.id, label: row.title, meta: `${row.projectName || row.pname || '未归属产品'} · ${displayType(row)}` }))
  if (key === 'productUpdates') return productChangeGroups.value.map(row => ({ key: row.projectId || row.key, type: 'product', id: row.projectId, label: row.name, meta: `${row.focusCount} 项重点 · ${row.totalCount} 条记录` }))
  return []
}

function selectDeveloper(name: string) { selectedDeveloper.value = selectedDeveloper.value === name ? '' : name }
function workloadPercent(row: any, level: string) { return row.recordCount ? Math.round((row[level === '大' ? 'largeCount' : level === '中' ? 'mediumCount' : 'smallCount'] / row.recordCount) * 100) : 0 }
function typeColor(type: string) { return ({ '新增功能': '#2563eb', '功能优化': '#d97706', '技术建设': '#64748b', '问题修复': '#dc2626', '业务确认': '#0284c7', '产品设计': '#7c3aed', '验证交付': '#0f766e' } as Record<string, string>)[normalizedType(type)] || '#6b7280' }
function typeLabel(type: string) { return ({ '技术建设': '技术建设 / 重构', '问题修复': '问题修复 / Bug' } as Record<string, string>)[normalizedType(type)] || normalizedType(type) || '工作记录' }
function typeBadgeStyle(type: string) { const color = typeColor(type); return { backgroundColor: `${color}14`, color, borderColor: `${color}45` } }
function displayType(row: any) {
  const type = normalizedType(row.type)
  if (type === '新增功能' && row.changeObject === '模块') return '新增模块'
  if (type === '新增功能') return '新增功能'
  if (type === '技术建设') return '重构建设'
  if (type === '功能优化' && ['页面交互', '字段'].includes(row.changeObject)) return '使用优化'
  return type || '工作记录'
}
function displayTierLabel(row: any) { return displayTier(row) === 3 ? '核心变化' : displayTier(row) === 2 ? '配套变化' : '细节变化' }
function tierColor(row: any) { return displayTier(row) === 3 ? '#dc2626' : displayTier(row) === 2 ? '#d97706' : '#64748b' }
function productHeadline(group: any) {
  const parts = group.changeSummary.filter((item: any) => item.value).map((item: any) => `${item.label}${item.value}项`)
  return parts.length ? `本期${parts.join('、')}` : '本期有工作记录更新'
}
function impactColor(level: string) { return ({ 核心: '#dc2626', 重要: '#d97706', 常规: '#64748b' } as Record<string, string>)[level] || '#64748b' }
function projectProgressPercent(project: any) { return Math.max(0, Math.min(100, Math.round(Number(project?.progress?.progress ?? project?.progress?.currentProgress ?? 0) || 0))) }
function projectProgressColor(project: any) { if (project?.progress?.mode === 'released' || projectProgressPercent(project) >= 100) return '#10b981'; if (project?.progress?.mode === 'empty') return '#d1d5db'; if ((project?.progress?.subLabel || '').includes('暂停')) return '#f97316'; return projectProgressPercent(project) >= 70 ? '#14b8a6' : '#3b82f6' }
function projectStatusLabel(status: string) { return ({ active: '进行中', paused: '暂停', archived: '已归档' } as Record<string, string>)[status] || status || '未设置状态' }
async function syncDashboard() {
  const result = await api.syncNotification({ scope: 'dashboard' })
  alert(result ? '已同步成果总览到钉钉群' : '同步失败，请先在通知配置中添加大盘机器人')
}

onMounted(async () => {
  const [projectRows, requirementRows] = await Promise.all([api.getProjects(), api.getRequirements({})])
  if (projectRows) projects.value = projectRows
  if (requirementRows) requirements.value = requirementRows
  loading.value = false
})
return { route, router, loading, projects, requirements, selectedDeveloper, hoveredCard, validRanges, initialRange, dashboardRange, periodOptions, terminalStatuses, workloadWeights, impactWeights, preferredDevelopers, visibleWorkTypes, legacyTypeAliases, setDashboardRange, dashboardQuery, monthQuery, openProduct, openProductLedger, openRequirement, openWorkspace, openCardRoute, openPopoverRow, parseDate, periodWindow, periodLabel, inPeriod, requirementInPeriod, periodRequirements, isActiveProject, activeProjectList, periodNewRequirementList, splitPeople, matchesPerson, normalizedType, displayTier, changeScore, isFocusChange, changedProductIds, changedProductCount, totalWorkloadScore, doneCount, projectForRow, rowProjectName, sortedRows, productChangeGroups, focusProductCount, deliveredProductGroups, focusChangeList, overviewStats, preferredDeveloperNames, developerRows, selectedDeveloperDetails, cardPopoverRows, selectDeveloper, workloadPercent, typeColor, typeLabel, typeBadgeStyle, displayType, displayTierLabel, tierColor, productHeadline, impactColor, projectProgressPercent, projectProgressColor, projectStatusLabel, syncDashboard }
}
