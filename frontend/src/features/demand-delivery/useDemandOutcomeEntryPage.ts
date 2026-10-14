
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api/application-api'
export function useDemandOutcomeEntryPage() {


const token = ref('')
const context = ref<any>(null)
const request = computed(() => context.value?.request || null)
const stage = computed(() => context.value?.stage || null)
const form = ref<any>({ currentState: '', desiredChange: '', summary: '', targetMet: '', useStatus: '', goalStatus: '', satisfaction: '', issueLevel: '', effectStatus: '', changeTypes: [], metricResults: [], noGoal: false })
const files = ref<File[]>([])
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const uploadError = ref('')
const successMessage = ref('')
const changeTypeOptions = ['节省时间', '减少人工操作', '减少错误', '提高处理效率', '暂无明显变化', '其他']
const day30NeedsDetail = computed(() => request.value?.stage === 'day30' && ['暂无明显改善', '暂时无法判断'].includes(form.value.effectStatus))
const structuredMetricRows = computed(() => {
  const baseline = Array.isArray(context.value?.valueCard?.baseline?.metrics) ? context.value.valueCard.baseline.metrics : []
  const expected = Array.isArray(context.value?.valueCard?.expected?.metrics) ? context.value.valueCard.expected.metrics : []
  const actual = Array.isArray(context.value?.valueCard?.day30?.metricResults) ? context.value.valueCard.day30.metricResults : []
  const keys = Array.from(new Set([...baseline, ...expected, ...actual].map(item => item?.key).filter(Boolean)))
  return keys.map(key => {
    const item = { ...(baseline.find((entry: any) => entry.key === key) || {}), ...(expected.find((entry: any) => entry.key === key) || {}), ...(actual.find((entry: any) => entry.key === key) || {}) }
    return { key, label: item.label || key, unit: item.unit || '', baselineValue: item.baselineValue, targetValue: item.targetValue, source: item.source || '' }
  })
})
const canSubmit = computed(() => {
  if (request.value?.stage === 'goal') return !!form.value.noGoal || !!String(form.value.desiredChange || '').trim()
  if (request.value?.stage === 'day7') return !!form.value.useStatus && !!form.value.goalStatus && !!form.value.satisfaction
  return !!form.value.effectStatus && (!day30NeedsDetail.value || !!String(form.value.summary || '').trim())
})

function addFiles(incoming: File[]) {
  for (const file of incoming) {
    if (file.size > 50 * 1024 * 1024) { uploadError.value = `附件「${file.name}」超过 50MB，未添加。`; continue }
    if (!files.value.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) files.value.push(file)
  }
}
function removeFile(index: number) { files.value.splice(index, 1) }
function displayValue(value: any) { return value === null || value === undefined || String(value).trim() === '' ? '—' : String(value) }
function hydrateMetricResults(payload: any) {
  const existing = Array.isArray(payload?.request?.responseSnapshot?.metricResults) ? payload.request.responseSnapshot.metricResults : []
  form.value.metricResults = structuredMetricRows.value.map(metric => {
    const current = existing.find((entry: any) => entry.key === metric.key) || {}
    return { ...metric, actualValue: current.actualValue ?? '', targetMet: typeof current.targetMet === 'boolean' ? current.targetMet : '', source: current.source || metric.source || '业务负责人填写' }
  })
}

function readToken() {
  const hash = window.location.hash || ''
  const query = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : window.location.search.slice(1)
  return new URLSearchParams(query).get('token') || ''
}
async function submit() {
  if (!canSubmit.value || saving.value || !token.value) return
  saving.value = true; errorMessage.value = ''; uploadError.value = ''
  const result: any = await api.submitDemandPoolOutcome({ token: token.value, ...form.value, actualResult: form.value.summary })
  saving.value = false
  if (!result?.request) { errorMessage.value = result?.error || '反馈提交失败，请重新打开链接。'; return }
  const failed: string[] = []
  for (const file of files.value) if (!await api.uploadBusinessAttachment('demand_pool_value_request', result.request.id, file, token.value)) failed.push(file.name)
  if (failed.length) uploadError.value = `反馈已提交，但以下附件上传失败：${failed.join('、')}`
  files.value = []
  successMessage.value = request.value?.stage === 'goal' ? '上线前目标已确认' : request.value?.stage === 'day7' ? '上线 3 天回执已提交' : '上线 30 天价值验证已提交'
  context.value = { ...context.value, request: result.request }
}
onMounted(async () => {
  token.value = readToken()
  if (!token.value) { errorMessage.value = '成果回访链接无效。'; loading.value = false; return }
  const result: any = await api.getDemandPoolOutcomeContext(token.value)
  if (result) { context.value = result; hydrateMetricResults(result) }
  else errorMessage.value = '成果回访链接已失效或不存在。'
  loading.value = false
})
return { token, context, request, stage, form, files, loading, saving, errorMessage, uploadError, successMessage, changeTypeOptions, day30NeedsDetail, structuredMetricRows, canSubmit, addFiles, removeFile, displayValue, hydrateMetricResults, readToken, submit }
}
