import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircle2, Layers3, PackageOpen, Sparkles, Wrench } from 'lucide-vue-next'
import { api } from '../../api/application-api'
export function useProductOverviewPage(){


const route = useRoute()
const router = useRouter()
const loading = ref(true)
const projects = ref<any[]>([])
const requirements = ref<any[]>([])
const categoryFilter = ref('')
const focusedProjectId = ref('')

const impactWeights: Record<string, number> = { 核心: 30, 重要: 20, 常规: 10 }
const workloadWeights: Record<string, number> = { 大: 3, 中: 2, 小: 1 }
const typeColors: Record<string, string> = { 新增功能: '#2563eb', 功能优化: '#d97706', 技术建设: '#64748b', 问题修复: '#dc2626', 业务确认: '#0284c7', 产品设计: '#7c3aed', 验证交付: '#0f766e' }
const dashboardRanges = ['week', 'month', 'year']
const productViewOptions = [
  { value: 'mine', label: '我的产品' },
  { value: 'changed', label: '最近变动' },
  { value: 'focus', label: '重点变化' },
  { value: 'active', label: '进行中' },
  { value: 'work', label: '工作视图' },
  { value: 'all', label: '全部产品' },
]

const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { return {} }
})
const currentUserName = computed(() => currentUser.value?.devOwnerName || currentUser.value?.name || '')
const isManager = computed(() => ['admin', 'super_admin'].includes(currentUser.value?.role))

const routeRange = computed(() => {
  const value = String(route.query.range || '')
  return dashboardRanges.includes(value) ? value : ''
})
const routeCategory = computed(() => String(route.query.category || ''))
const routeProjectStatus = computed(() => String(route.query.projectStatus || ''))
const productView = computed(() => {
  const value = String(route.query.view || '')
  if (productViewOptions.some(option => option.value === value)) return value
  return currentUserName.value && !isManager.value ? 'mine' : 'changed'
})
const productViewLabel = computed(() => productViewOptions.find(option => option.value === productView.value)?.label || '最近变动')
const productViewDescription = computed(() => ({
  mine: '优先查看我负责或参与的产品',
  changed: '优先查看本期发生变化的产品',
  focus: '优先查看存在重点变化的产品',
  active: '查看当前仍在进行中的产品',
  work: '查看未完成 L3 的当前工作与共享讨论',
  all: '查看全部 L2 产品及其变化',
} as Record<string, string>)[productView.value] || '按 L2 产品查看产品变化')
const effectiveRange = computed(() => {
  if (routeRange.value) return routeRange.value
  return ['mine', 'changed', 'focus'].includes(productView.value) ? 'month' : ''
})
const routeRangeLabel = computed(() => ({ week: '本周', month: '本月', year: '本年' } as Record<string, string>)[effectiveRange.value] || '全部时间')

const routePeriodWindow = computed(() => {
  if (!effectiveRange.value) return null
  const end = new Date(); end.setHours(23, 59, 59, 999)
  const start = new Date(end); start.setHours(0, 0, 0, 0)
  if (effectiveRange.value === 'week') { const day = start.getDay() || 7; start.setDate(start.getDate() - day + 1) }
  else if (effectiveRange.value === 'month') start.setDate(1)
  else start.setMonth(0, 1)
  return { start, end }
})

function splitPeople(value: string) {
  return String(value || '').split(/[,，]/).map(item => item.trim()).filter(Boolean)
}
function hasPerson(value: string, person: string) {
  return !!person && (splitPeople(value).includes(person) || String(value || '').includes(person))
}
function setProductView(view: string) {
  const query: Record<string, any> = { ...route.query, view }
  if (!route.query.range && ['mine', 'changed', 'focus'].includes(view)) query.range = 'month'
  if (view === 'all' || view === 'active' || view === 'work') delete query.range
  router.push({ path: '/products', query })
}

function inRoutePeriod(value: string) {
  if (!routePeriodWindow.value) return true
  if (!value) return false
  const date = new Date(String(value).replace(/-/g, '/'))
  return !Number.isNaN(date.getTime()) && date >= routePeriodWindow.value.start && date <= routePeriodWindow.value.end
}

function isFocusChange(item: any) {
  return item.impactLevel !== '常规' || item.type === '新增功能' || item.type === '技术建设' || item.workloadLevel === '大' || (item.type === '问题修复' && ['P0', 'P1'].includes(item.priority))
}

const categoryOptions = computed(() => Array.from(new Set(projects.value.map(item => item.categoryName).filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b), 'zh-CN')))

function score(item: any) {
  return (impactWeights[item.impactLevel] || 10) + (workloadWeights[item.workloadLevel] || 2)
}
function impactColor(level: string) {
  return ({ 核心: '#dc2626', 重要: '#d97706', 常规: '#64748b' } as Record<string, string>)[level] || '#64748b'
}
function projectStatusLabel(status: string) {
  return ({ active: '进行中', paused: '暂停', archived: '已归档' } as Record<string, string>)[status] || status || '未设置状态'
}
function projectStatusBucket(status: string) {
  const value = String(status || '')
  if (['已归档', '已关闭', 'archived'].includes(value)) return 'archived'
  if (['已上线', '维护中', 'released'].includes(value)) return 'released'
  if (['暂停中', '暂停', 'paused'].includes(value)) return 'paused'
  return 'active'
}
function isActiveProject(project: any) { return projectStatusBucket(project?.status) === 'active' }
function projectStatusColor(status: string) {
  return status === 'paused' ? '#d97706' : status === 'archived' ? '#64748b' : '#2563eb'
}
function statusColor(status: string) {
  return ({ 待处理: '#64748b', 进行中: '#2563eb', 待交付: '#d97706', 已交付: '#059669', 已关闭: '#64748b' } as Record<string, string>)[status] || '#64748b'
}
function progressPercent(project: any) {
  return Math.max(0, Math.min(100, Math.round(Number(project.progress?.progress ?? project.progress?.currentProgress ?? 0) || 0)))
}

const productRows = computed(() => projects.value.map(project => {
  const rows = requirements.value.filter(req => req.projectId === project.id && (!routePeriodWindow.value || [req.createdAt, req.updatedAt, req.completedAt].some(inRoutePeriod)))
  const notable = [...rows].sort((a, b) => score(b) - score(a) || String(b.updatedAt || '').localeCompare(String(a.updatedAt || ''))).filter(isFocusChange).slice(0, 5)
  const mine = !!currentUserName.value && (hasPerson(project.devOwner, currentUserName.value) || hasPerson(project.businessOwner, currentUserName.value) || rows.some(row => hasPerson(row.assignee, currentUserName.value) || hasPerson(row.requester, currentUserName.value)))
  return {
    ...project, mine,
    total: rows.length,
    doneCount: rows.filter(item => ['已交付', '已关闭'].includes(item.status)).length,
    coreCount: rows.filter(item => item.impactLevel === '核心').length,
    addCount: rows.filter(item => item.type === '新增功能').length,
    notable,
    regularCount: Math.max(0, rows.length - notable.length),
  }
}))
const filteredProducts = computed(() => {
  let rows = productRows.value.filter(item => !categoryFilter.value || item.categoryName === categoryFilter.value)
  if (productView.value === 'mine') rows = rows.filter(item => item.mine)
  if (productView.value === 'changed') rows = rows.filter(item => item.total > 0)
  if (productView.value === 'focus') rows = rows.filter(item => item.notable.length > 0)
  if (productView.value === 'active') rows = rows.filter(isActiveProject)
  if (productView.value === 'work') rows = rows.filter(item => item.total > item.doneCount)
  if (routeCategory.value) rows = rows.filter(item => item.categoryName === routeCategory.value)
  if (routeProjectStatus.value) rows = rows.filter(item => projectStatusBucket(item.status) === routeProjectStatus.value)
  return rows
})
const workRequirements = computed(() => requirements.value.filter(item => !['已交付', '已关闭'].includes(item.status) && (!categoryFilter.value || projects.value.find(project => project.id === item.projectId)?.categoryName === categoryFilter.value) && (!routeProjectStatus.value || projectStatusBucket(projects.value.find(project => project.id === item.projectId)?.status) === routeProjectStatus.value)).sort((a, b) => String(b.updatedAt || '').localeCompare(String(a.updatedAt || ''))).slice(0, 24))
const workStatusCards = computed(() => [
  { status: '待处理', value: workRequirements.value.filter(item => item.status === '待处理').length, className: 'bg-slate-50 text-slate-700' },
  { status: '进行中', value: workRequirements.value.filter(item => item.status === '进行中').length, className: 'bg-blue-50 text-blue-700' },
  { status: '待交付', value: workRequirements.value.filter(item => item.status === '待交付').length, className: 'bg-amber-50 text-amber-700' },
  { status: '重点关注', value: workRequirements.value.filter(isFocusChange).length, className: 'bg-violet-50 text-violet-700' },
])
const allRows = computed(() => productRows.value.flatMap(item => item.notable.map((change: any) => ({ ...change, projectName: item.name }))))
const recentChanges = computed(() => [...allRows.value].sort((a, b) => String(b.updatedAt || '').localeCompare(String(a.updatedAt || ''))).slice(0, 6))
const summaryCards = computed(() => [
  { label: '产品总数', value: filteredProducts.value.length, hint: 'L2 产品/项目', icon: PackageOpen, iconClass: 'text-blue-500' },
  { label: '工作记录', value: filteredProducts.value.reduce((sum, item) => sum + item.total, 0), hint: 'L3 完整台账', icon: Wrench, iconClass: 'text-amber-500' },
  { label: '重点变化', value: filteredProducts.value.reduce((sum, item) => sum + item.notable.length, 0), hint: '核心/重要/大工作量', icon: Sparkles, iconClass: 'text-red-500' },
  { label: '已交付记录', value: filteredProducts.value.reduce((sum, item) => sum + item.doneCount, 0), hint: '已交付或已关闭', icon: CheckCircle2, iconClass: 'text-emerald-500' },
])

async function loadData() {
  loading.value = true
  const [p, r] = await Promise.all([api.getProjects(), api.getRequirements({})])
  if (p) projects.value = p
  if (r) requirements.value = r
  loading.value = false
}

onMounted(loadData)
return { route, router, loading, projects, requirements, categoryFilter, focusedProjectId, impactWeights, workloadWeights, typeColors, dashboardRanges, productViewOptions, currentUser, currentUserName, isManager, routeRange, routeCategory, routeProjectStatus, productView, productViewLabel, productViewDescription, effectiveRange, routeRangeLabel, routePeriodWindow, splitPeople, hasPerson, setProductView, inRoutePeriod, isFocusChange, categoryOptions, score, impactColor, projectStatusLabel, projectStatusBucket, isActiveProject, projectStatusColor, statusColor, progressPercent, productRows, filteredProducts, workRequirements, workStatusCards, allRows, recentChanges, summaryCards, loadData }
}
