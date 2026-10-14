
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { changeTypeConfig } from '../../data/mockData'
import { api } from '../../api/application-api'
import type { Changelog } from '../../types'
export function useChangelogPage() {


const router = useRouter()
const loading = ref(true)
const changelogs = ref<Changelog[]>([])
const requirements = ref<any[]>([])
const projects = ref<any[]>([])
const projectFilter = ref('')
const expandedEvents = ref<Set<string>>(new Set())

const typeAliases: Record<string, string> = {
  '新功能': '新增功能', '优化改进': '功能优化', 'Bug修复': '问题修复', 'UI调整': '功能优化',
  '接口对接': '技术建设', '技术重构': '技术建设', '需求变更': '业务确认', '需求对接': '业务确认',
  '技术方案验证': '技术建设', '功能测试': '验证交付',
}
const typeColors: Record<string, string> = { 新增功能: '#2563eb', 功能优化: '#d97706', 技术建设: '#64748b', 问题修复: '#dc2626', 业务确认: '#0284c7', 产品设计: '#7c3aed', 验证交付: '#0f766e' }
const impactRank: Record<string, number> = { 核心: 3, 重要: 2, 常规: 1 }
const workloadRank: Record<string, number> = { 大: 3, 中: 2, 小: 1 }

const requirementMap = computed(() => new Map(requirements.value.map(row => [row.id, row])))
const productOptions = computed(() => [...projects.value].sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'zh-CN')))

function toTime(value: string) {
  const date = new Date(String(value || '').replace(/-/g, '/'))
  return Number.isNaN(date.getTime()) ? 0 : date.getTime()
}
function formatDate(value: string) { return String(value || '').split(' ')[0] || '未记录时间' }
function formatDateTime(value: string) { return String(value || '').split(' ')[1] || String(value || '') || '未记录时间' }
function normalizedType(type: string) { return typeAliases[String(type || '')] || String(type || '') }
function workTypeLabel(row: any) {
  const type = normalizedType(row.requirementType)
  if (type === '新增功能' && row.changeObject === '模块') return '新增模块'
  if (type === '技术建设') return '技术建设'
  return type || '工作记录'
}
function typeColor(type: string) { return typeColors[normalizedType(type)] || '#6b7280' }
function typeBadgeStyle(type: string) { const color = typeColor(type); return { backgroundColor: `${color}14`, color } }

const productGroups = computed(() => {
  const rows = changelogs.value
    .map(change => {
      const requirement = requirementMap.value.get(change.requirementId) || {}
      const project = projects.value.find(item => item.id === requirement.projectId)
      return {
        ...change,
        requirementType: requirement.type || '',
        changeObject: requirement.changeObject || '',
        impactLevel: requirement.impactLevel || '常规',
        workloadLevel: requirement.workloadLevel || '中',
        projectId: requirement.projectId || '',
        projectName: requirement.projectName || requirement.pname || project?.name || '未归属产品',
        categoryName: project?.categoryName || '未分类',
      }
    })
    .filter(row => !projectFilter.value || row.projectId === projectFilter.value)

  const byProduct = new Map<string, any>()
  rows.forEach(row => {
    const productKey = row.projectId || `unassigned:${row.projectName}`
    if (!byProduct.has(productKey)) byProduct.set(productKey, { key: productKey, projectId: row.projectId, name: row.projectName, categoryName: row.categoryName, rows: [] })
    byProduct.get(productKey).rows.push(row)
  })

  return Array.from(byProduct.values()).map(group => {
    const eventMap = new Map<string, any>()
    group.rows.forEach((row: any) => {
      const eventKey = row.requirementId || `change:${row.id}`
      if (!eventMap.has(eventKey)) eventMap.set(eventKey, { key: eventKey, requirementId: row.requirementId, requirementTitle: row.requirementTitle || '未命名需求', details: [] })
      eventMap.get(eventKey).details.push(row)
    })
    const events = Array.from(eventMap.values()).map(event => {
      const details = [...event.details].sort((a, b) => toTime(b.createdAt) - toTime(a.createdAt))
      const workTypes = [...new Set(details.map(workTypeLabel))]
      const impactLevel = [...details].sort((a, b) => (impactRank[b.impactLevel] || 0) - (impactRank[a.impactLevel] || 0))[0]?.impactLevel || '常规'
      const workloadLevel = [...details].sort((a, b) => (workloadRank[b.workloadLevel] || 0) - (workloadRank[a.workloadLevel] || 0))[0]?.workloadLevel || '中'
      return { ...event, details, workTypes, impactLevel, workloadLevel, changeCount: details.length, operators: [...new Set(details.map(row => row.operator).filter(Boolean))], latestAt: details[0]?.createdAt || '' }
    }).sort((a, b) => toTime(b.latestAt) - toTime(a.latestAt))
    const typeCount = new Map<string, number>()
    group.rows.forEach((row: any) => { const label = workTypeLabel(row); typeCount.set(label, (typeCount.get(label) || 0) + 1) })
    return {
      ...group,
      events,
      eventCount: events.length,
      operationCount: group.rows.length,
      latestAt: events[0]?.latestAt || '',
      typeSummary: Array.from(typeCount.entries()).map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count),
    }
  }).sort((a, b) => toTime(b.latestAt) - toTime(a.latestAt))
})

const summaryCards = computed(() => [
  { label: '涉及产品', value: productGroups.value.length, hint: '已发生历史变更的 L2 产品' },
  { label: '产品变化', value: productGroups.value.reduce((sum, group) => sum + group.eventCount, 0), hint: '按 L3 需求聚合后的变化' },
  { label: '操作明细', value: productGroups.value.reduce((sum, group) => sum + group.operationCount, 0), hint: '可展开查看字段级记录' },
])

function toggleEvent(key: string) {
  const next = new Set(expandedEvents.value)
  next.has(key) ? next.delete(key) : next.add(key)
  expandedEvents.value = next
}
function openRequirement(id: string) { if (id) router.push('/requirements/' + id) }
function openProduct(id: string) { if (id) router.push('/projects/' + id) }
function getConfig(type: string) { return changeTypeConfig[type] || { color: '#6b7280', bgColor: '#f3f4f6', icon: '📝', desc: '' } }

async function loadData() {
  loading.value = true
  const [logs, reqs, prods] = await Promise.all([api.getChangelogs(), api.getRequirements({}), api.getProjects()])
  if (logs) changelogs.value = logs
  if (reqs) requirements.value = reqs
  if (prods) projects.value = prods
  loading.value = false
}

onMounted(loadData)
return { router, loading, changelogs, requirements, projects, projectFilter, expandedEvents, typeAliases, typeColors, impactRank, workloadRank, requirementMap, productOptions, toTime, formatDate, formatDateTime, normalizedType, workTypeLabel, typeColor, typeBadgeStyle, productGroups, summaryCards, toggleEvent, openRequirement, openProduct, getConfig, loadData, changeTypeConfig }
}
