
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/application-api'
export function usePostLaunchOperationsPage() {


const loading = ref(true), saving = ref(false), showCreate = ref(false), showIssue = ref(false)
const route = useRoute()
const rows = ref<any[]>([]), detail = ref<any>(null), selectedId = ref(String(route.query.operationId || ''))
const requirements = ref<any[]>([]), projects = ref<any[]>([])
const createForm = reactive({ targetType: 'requirement', targetId: '', deliveryDate: new Date().toISOString().slice(0, 10), businessOwnerName: '' })
const issueForm = reactive({ title: '', description: '', severity: '一般' }), ownerName = ref('')
const summaryCards = [
  { key: 'operations', label: '交付记录', color: 'text-gray-900', border: 'border-gray-200' }, { key: 'trial', label: '试运行', color: 'text-blue-600', border: 'border-blue-100' }, { key: 'live', label: '已上线', color: 'text-green-600', border: 'border-green-100' }, { key: 'day7Pending', label: '待3天回执', color: 'text-orange-600', border: 'border-orange-100' }, { key: 'day30Pending', label: '待30天复盘', color: 'text-purple-600', border: 'border-purple-100' }, { key: 'openIssues', label: '开放问题', color: 'text-red-600', border: 'border-red-100' }, { key: 'proposals', label: '改善提案', color: 'text-indigo-600', border: 'border-indigo-100' }, { key: 'knowledge', label: '知识记录', color: 'text-emerald-600', border: 'border-emerald-100' },
]
const summary = reactive<Record<string, number>>({ operations: 0, trial: 0, live: 0, day7Pending: 0, day30Pending: 0, openIssues: 0, proposals: 0, knowledge: 0 })
const targetOptions = computed(() => (createForm.targetType === 'requirement' ? requirements.value : projects.value).filter(x => ['已交付', '已上线', '维护中', 'active'].includes(x.status)))

function outcomeStatus(row: any, stage: string) { const item = (row.outcomeRequests || []).find((x: any) => x.stage === stage); return item ? (item.status === 'submitted' ? '已提交' : item.statusLabel || '待填写') : '未安排' }
function calculateSummary(items: any[]) {
  const today = new Date().toISOString().slice(0, 10)
  Object.assign(summary, {
    operations: items.length,
    trial: items.filter(row => row.deliveryKind === '试运行').length,
    live: items.filter(row => ['上线', '已交付'].includes(row.deliveryKind)).length,
    day7Pending: items.filter(row => row.day7DueDate && row.day7DueDate <= today && !row.outcomeRequests?.some((item: any) => item.stage === 'day7' && item.status === 'submitted')).length,
    day30Pending: items.filter(row => row.day30DueDate && row.day30DueDate <= today && !row.outcomeRequests?.some((item: any) => item.stage === 'day30' && item.status === 'submitted')).length,
    openIssues: items.reduce((total, row) => total + Number(row.openIssueCount || 0), 0),
    proposals: items.reduce((total, row) => total + Number(row.proposalCount || 0), 0),
    knowledge: items.reduce((total, row) => total + Number(row.knowledgeCount || 0), 0),
  })
}
async function refresh() {
  loading.value = true
  const [operationRows, requirementRows, projectRows] = await Promise.all([api.getPostlaunchOperations(), api.getRequirements(), api.getProjects()])
  rows.value = Array.isArray(operationRows) ? operationRows : []
  requirements.value = requirementRows || []
  projects.value = projectRows || []
  calculateSummary(rows.value)
  if (selectedId.value && rows.value.some(row => row.id === selectedId.value)) await select(selectedId.value)
  else if (rows.value[0]) { selectedId.value = rows.value[0].id; await select(rows.value[0].id) }
  else detail.value = null
  loading.value = false
}
async function select(id: string) { selectedId.value = id; detail.value = await api.getPostlaunchOperation(id); ownerName.value = detail.value?.businessOwnerName || '' }
async function saveOwner() { if (!detail.value || !ownerName.value.trim()) return; await api.updatePostlaunchOperation(detail.value.id, { businessOwnerName: ownerName.value.trim() }); await select(detail.value.id); await refresh() }
async function createOperation() { if (!createForm.targetId) return; saving.value = true; const out = await api.createPostlaunchOperation({ targetType: createForm.targetType, targetId: createForm.targetId, deliveryDate: createForm.deliveryDate, useStartDate: createForm.deliveryDate, businessOwnerName: createForm.businessOwnerName }); saving.value = false; if (out?.id) { showCreate.value = false; selectedId.value = out.id; await refresh() } }
async function createIssue() { if (!detail.value || !issueForm.title) return; await api.createPostlaunchIssue({ operationId: detail.value.id, title: issueForm.title, description: issueForm.description, severity: issueForm.severity }); issueForm.title = ''; issueForm.description = ''; showIssue.value = false; await select(detail.value.id); await refresh() }
async function updateIssue(id: string, status: string) { await api.updatePostlaunchIssue(id, { status }); if (detail.value) await select(detail.value.id); await refresh() }
async function createProposal() { if (!detail.value) return; const title = window.prompt('改善提案标题'); if (!title) return; await api.createPostlaunchProposal({ operationId: detail.value.id, title }); await select(detail.value.id); await refresh() }
async function createKnowledge() { if (!detail.value) return; const title = window.prompt('知识标题'); if (!title) return; const content = window.prompt('经验内容（可粘贴文字、流程或结论）'); if (!content) return; await api.createPostlaunchKnowledge({ operationId: detail.value.id, title, content, status: 'draft' }); await select(detail.value.id); await refresh() }
async function copyOutcomeLink(link: string) { if (!link) return; try { await navigator.clipboard.writeText(link); window.alert('业务反馈链接已复制') } catch { window.alert(link) } }
onMounted(refresh)
return { loading, saving, showCreate, showIssue, route, rows, detail, selectedId, requirements, projects, createForm, issueForm, ownerName, summaryCards, summary, targetOptions, outcomeStatus, calculateSummary, refresh, select, saveOwner, createOperation, createIssue, updateIssue, createProposal, createKnowledge, copyOutcomeLink }
}
