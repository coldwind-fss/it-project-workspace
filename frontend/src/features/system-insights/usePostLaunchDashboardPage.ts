
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
export function usePostLaunchDashboardPage(){


const route = useRoute(), router = useRouter()
const loading = ref(true), dashboard = ref<any>(null), rows = ref<any[]>([]), projects = ref<any[]>([]), selectedProject = ref<any>(null)
const filters = reactive({ department: '', solutionType: '', deliveryMonth: String(route.query.deliveryMonth || ''), valueStatus: '' })
const valueStatusOptions = ['未开始', '3天回执待处理', '价值验证中', '已完成', '待整改']
const metricDefinitions = [
  { key: 'responseRate', label: '回访响应率', note: '已提交回访 ÷ 已到期且已发送回访' },
  { key: 'onTimeDeliveryRate', label: '按期交付率', note: '按计划日期完成交付 ÷ 有计划日期的交付' },
  { key: 'acceptancePassRate', label: '验收通过率', note: '验收通过轮次 ÷ 已提交验收轮次' },
  { key: 'satisfactionRate', label: '满意率', note: '满意 / 基本满意 ÷ 有效 3 天回执' },
  { key: 'usageRate', label: '使用率', note: '已开始使用 ÷ 有效 3 天回执' },
  { key: 'efficiencyRate', label: '提效比例', note: '有基线、目标和实际值的指标中达到目标的比例' },
]
const metricCards = computed(() => metricDefinitions.map(definition => ({ ...definition, ...(dashboard.value?.metrics || []).find((item: any) => item.key === definition.key) })))
const l2Rows = computed(() => dashboard.value?.l2Rows || [])
const projectTypeOptions = computed(() => {
  const values = new Map<string, string>()
  projects.value.forEach(item => { if (item.solutionType) values.set(item.solutionType, item.solutionTypeLabel || item.solutionType) })
  return Array.from(values.entries()).map(([value, label]) => ({ value, label }))
})
const projectRows = computed(() => l2Rows.value.map((project: any) => {
  const sourceRows = rows.value.filter(row => project.l3Rows?.some((item: any) => item.operationId === row.id))
  const missing = Array.from(new Set(sourceRows.flatMap(row => row.metricDataStatus?.missing || [])))
  return {
    ...project,
    sourceRows,
    delivery: deliverySummary(sourceRows),
    acceptance: acceptanceSummary(sourceRows),
    day7: projectStageSummary(sourceRows, 'day7'),
    day30: projectStageSummary(sourceRows, 'day30'),
    satisfaction: formatRate(rateForRows(sourceRows, 'satisfaction')),
    usage: formatRate(rateForRows(sourceRows, 'usage')),
    efficiency: formatRate(efficiencyForRows(sourceRows)),
    missing,
  }
}))
const missingDataRows = computed(() => rows.value.filter(row => row.metricDataStatus?.missing?.length))
const selectedProjectRows = computed(() => selectedProject.value?.sourceRows || [])

function deliverySummary(items: any[]) { const dates = items.map(row => row.deliveryDate).filter(Boolean).sort(); return dates.length ? (dates[dates.length - 1] + (dates.length > 1 ? `（${dates.length} 次）` : '')) : '未记录' }
function acceptanceSummary(items: any[]) { const values = items.map(row => row.acceptanceOutcome).filter(Boolean); if (!values.length) return '待确认'; if (values.every(value => value === 'passed')) return '全部通过'; const passed = values.filter(value => value === 'passed').length; return `通过 ${passed}/${values.length}` }
function projectStageSummary(items: any[], stage: string) { const requests = items.map(row => row.outcomeRequests?.find((item: any) => item.stage === stage)).filter(Boolean); if (!requests.length) return '未安排'; const submitted = requests.filter(item => item.status === 'submitted').length; if (submitted === requests.length) return '已提交'; return submitted ? `已提交 ${submitted}/${requests.length}` : '待回访' }
function stageStatus(row: any, stage: string) { const request = row.outcomeRequests?.find((item: any) => item.stage === stage); return request ? (request.status === 'submitted' ? '已提交' : '待回访') : '未安排' }
function rateForRows(items: any[], type: 'satisfaction' | 'usage') {
  const valid = items.map(row => row.day7Request?.responseSnapshot || {}).filter(snapshot => snapshot.useStatus && snapshot.satisfaction)
  const numerator = type === 'satisfaction' ? valid.filter(snapshot => ['满意', '基本满意'].includes(snapshot.satisfaction)).length : valid.filter(snapshot => ['已正常使用', '正常使用', '已开始使用但有问题'].includes(snapshot.useStatus)).length
  return { numerator, denominator: valid.length, value: valid.length ? Math.round(numerator / valid.length * 1000) / 10 : null }
}
function efficiencyForRows(items: any[]) { const numerator = items.reduce((sum, row) => sum + Number(row.metricDataStatus?.efficiencyAchieved || 0), 0); const denominator = items.reduce((sum, row) => sum + Number(row.metricDataStatus?.efficiencyTotal || 0), 0); return { numerator, denominator, value: denominator ? Math.round(numerator / denominator * 1000) / 10 : null } }
function formatRate(metric: any) { return metric.value == null ? '暂无数据' : `${metric.value}%` }
function displayValue(value: any) { return value === null || value === undefined || String(value).trim() === '' ? '—' : String(value) }
function metricResultsForRow(row: any) { const snapshotResults = row.day30Request?.responseSnapshot?.metricResults; if (Array.isArray(snapshotResults)) return snapshotResults; const cardResults = row.valueCard?.day30?.metricResults; return Array.isArray(cardResults) ? cardResults : [] }
function structuredMetricRows(row: any) {
  const baseline = Array.isArray(row.valueCard?.baseline?.metrics) ? row.valueCard.baseline.metrics : []
  const expected = Array.isArray(row.valueCard?.expected?.metrics) ? row.valueCard.expected.metrics : []
  const actual = metricResultsForRow(row)
  const keys = Array.from(new Set([...baseline, ...expected, ...actual].map(item => item?.key).filter(Boolean)))
  return keys.map(key => {
    const item = { ...(baseline.find((entry: any) => entry.key === key) || {}), ...(expected.find((entry: any) => entry.key === key) || {}), ...(actual.find((entry: any) => entry.key === key) || {}) }
    const baselineValue = numericValue(item.baselineValue)
    const targetValue = numericValue(item.targetValue)
    const actualValue = numericValue(item.actualValue)
    const direction = String(item.direction || (targetValue != null && baselineValue != null && targetValue < baselineValue ? 'lower' : 'higher'))
    const targetMet = typeof item.targetMet === 'boolean' ? item.targetMet : actualValue == null || targetValue == null ? null : direction === 'lower' ? actualValue <= targetValue : actualValue >= targetValue
    const change = baselineValue == null || actualValue == null || baselineValue === 0 ? null : (direction === 'lower' ? baselineValue - actualValue : actualValue - baselineValue) / Math.abs(baselineValue) * 100
    return { key, label: item.label || key, unit: item.unit || '', baselineValue: item.baselineValue, targetValue: item.targetValue, actualValue: item.actualValue, targetMet, changeText: change == null ? '—' : `${Math.round(change * 10) / 10}%` }
  })
}
function numericValue(value: any) { const number = Number(value); return value === null || value === undefined || String(value).trim() === '' || !Number.isFinite(number) ? null : number }
function rawOutcome(row: any, stage: string) { const snapshot = row[stage === 'day7' ? 'day7Request' : 'day30Request']?.responseSnapshot || {}; if (!Object.keys(snapshot).length) return stage === 'day7' ? '待填写' : '待验证'; return stage === 'day7' ? [snapshot.useStatus, snapshot.goalStatus, snapshot.satisfaction, snapshot.summary].filter(Boolean).join(' · ') : [snapshot.effectStatus, Array.isArray(snapshot.changeTypes) ? snapshot.changeTypes.join('、') : snapshot.changeTypes, snapshot.summary].filter(Boolean).join(' · ') }
function openProject(project: any) { selectedProject.value = project }
function clearFilters() { filters.department = ''; filters.solutionType = ''; filters.deliveryMonth = ''; filters.valueStatus = ''; void refresh() }
async function refresh() {
  loading.value = true
  selectedProject.value = null
  const [result, projectRowsResult] = await Promise.all([api.getPostlaunchDashboard(filters), api.getProjects()])
  dashboard.value = result
  rows.value = result?.rows || []
  projects.value = projectRowsResult || []
  const nextQuery = { ...route.query } as Record<string, any>
  if (filters.deliveryMonth) nextQuery.deliveryMonth = filters.deliveryMonth
  else delete nextQuery.deliveryMonth
  await router.replace({ query: nextQuery })
  loading.value = false
}
onMounted(refresh)
return { route, router, loading, dashboard, rows, projects, selectedProject, filters, valueStatusOptions, metricDefinitions, metricCards, l2Rows, projectTypeOptions, projectRows, missingDataRows, selectedProjectRows, deliverySummary, acceptanceSummary, projectStageSummary, stageStatus, rateForRows, efficiencyForRows, formatRate, displayValue, metricResultsForRow, structuredMetricRows, numericValue, rawOutcome, openProject, clearFilters, refresh }
}
