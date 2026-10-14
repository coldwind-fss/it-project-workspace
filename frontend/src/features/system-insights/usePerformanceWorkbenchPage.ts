
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../api/application-api'
export function usePerformanceWorkbenchPage(){


const month = ref(new Date().toISOString().slice(0, 7))
const loading = ref(true)
const saving = ref(false)
const payload = ref<any>(null)
const form = reactive({ goals: '', plan: '', nextPlan: '', finalText: '' })

function percent(value: any) { return value == null ? '—' : `${Math.round(Number(value) * 100)}%` }
function displayScore(value: any, max: any) { return value == null || max == null || Number(max) === 0 ? '待补数据' : `${Number(value).toFixed(1).replace(/\.0$/, '')}/${Number(max).toFixed(1).replace(/\.0$/, '')}` }
function scoreText(score: any) { return score?.value == null ? (score?.autoValue != null ? `自动候选 ${Number(score.autoValue).toFixed(1).replace(/\.0$/, '')}/${score.autoMax || 0}` : '待结算') : `${score.value}/${score.max}` }
function statusLabel(status: string) { return ({ calculated: '已计算', partial: '部分数据', pending_manual: '待人工评分' } as any)[status] || '待补数据' }
function statusClass(status: string) { return status === 'calculated' ? 'bg-emerald-50 text-emerald-700' : status === 'pending_manual' ? 'bg-purple-50 text-purple-700' : 'bg-amber-50 text-amber-700' }

async function load() {
  loading.value = true
  const result = await api.getMyPerformance(month.value)
  payload.value = result
  const row = result?.record
  form.goals = row?.goals || ''
  form.plan = row?.plan || ''
  form.nextPlan = row?.nextPlan || ''
  form.finalText = row?.finalText || ''
  loading.value = false
}

async function save(final: boolean) {
  if (!payload.value) return
  saving.value = true
  try {
    await api.saveMyPerformance({ month: month.value, ...form, final })
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
return { month, loading, saving, payload, form, percent, displayScore, scoreText, statusLabel, statusClass, load, save }
}
