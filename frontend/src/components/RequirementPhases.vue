<template>
  <section v-if="phases.length || canEdit" class="border-b border-gray-100 p-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="flex items-center gap-2 font-semibold text-gray-900"><Layers class="h-4 w-4 text-accent-500" />建设阶段卡 <span class="text-[10px] font-normal text-slate-400">{{ requirement.itemKindLabel || 'L3 工作单元' }}</span></h3>
        <p class="mt-1 text-xs leading-5 text-gray-500">按项目类型记录业务边界、设计、开发、测试和上线阶段；阶段可调整、跳过或补充，不改变共享动态历史。</p>
      </div>
      <button v-if="canEdit" type="button" class="feishu-btn-ghost text-xs text-accent-600" @click="showAdd = !showAdd">{{ showAdd ? '取消新增' : '新增阶段' }}</button>
    </div>

    <div v-if="error" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">{{ error }}</div>
    <div v-if="showAdd && canEdit" class="mt-4 rounded-lg border border-accent-100 bg-accent-50/40 p-3">
      <div class="grid gap-2 sm:grid-cols-[130px_minmax(0,1fr)_auto]">
        <input v-model="newPhase.phaseKey" class="feishu-input text-xs" placeholder="阶段编号" />
        <input v-model="newPhase.phaseLabel" class="feishu-input text-xs" placeholder="阶段名称，例如：权限设计" />
        <button type="button" class="feishu-btn-primary text-xs" :disabled="saving" @click="addPhase">保存阶段</button>
      </div>
      <textarea v-model="newPhase.description" rows="2" class="feishu-input mt-2 w-full text-xs" placeholder="阶段目的或交付物（可选）" />
    </div>

    <div v-if="loading" class="py-6 text-center text-xs text-gray-400">正在读取阶段卡…</div>
    <div v-else-if="!phases.length" class="mt-4 rounded-lg border border-dashed border-slate-200 px-3 py-5 text-center text-xs text-slate-400">当前 L3 未配置阶段卡，可按需新增。</div>
    <div v-else class="mt-4 grid gap-3 sm:grid-cols-2">
      <article v-for="phase in phases" :key="phase.id" role="button" tabindex="0" :aria-pressed="selectedPhaseId === phase.id" :class="['cursor-pointer rounded-xl border p-3 text-left transition focus:outline-none focus:ring-2 focus:ring-accent-200', selectedPhaseId === phase.id ? 'border-accent-300 bg-accent-50/50 shadow-sm' : 'border-slate-200 bg-slate-50/60 hover:border-accent-200 hover:bg-white']" @click="selectPhase(phase)" @keydown.enter.prevent="selectPhase(phase)" @keydown.space.prevent="selectPhase(phase)">
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0"><p class="truncate text-sm font-semibold text-slate-800">{{ phase.phaseLabel }}</p><p class="mt-0.5 text-[10px] text-slate-400">{{ phase.description || phase.phaseKey }}</p></div>
          <select v-if="canEdit" v-model="phase.status" class="rounded border border-slate-200 bg-white px-2 py-1 text-[11px]" @click.stop @change="savePhase(phase)"><option v-for="item in statusOptions" :key="item.key" :value="item.key">{{ item.label }}</option></select>
          <span v-else class="rounded bg-white px-2 py-1 text-[10px] text-slate-500">{{ phaseStatusLabel(phase) }}</span>
        </div>
        <div class="mt-3 flex items-center justify-between gap-2 text-[10px] text-slate-400"><span>{{ phase.required ? '建议完成' : '按需阶段' }}</span><span v-if="phase.completedAt">完成于 {{ phase.completedAt }}</span></div>
        <textarea v-if="canEdit" v-model="phase.note" rows="2" class="feishu-input mt-2 w-full resize-y text-xs" placeholder="阶段备注、验证证据或待确认事项" @click.stop @keydown.stop @blur="savePhase(phase)" />
        <p v-else-if="phase.note" class="mt-2 whitespace-pre-wrap text-xs leading-5 text-slate-600">{{ phase.note }}</p>
      </article>
    </div>

    <div v-if="selectedPhase" class="mt-4 rounded-xl border border-accent-100 bg-white p-4 shadow-sm">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="text-[10px] font-semibold uppercase tracking-wide text-accent-600">已选阶段</p>
          <h4 class="mt-1 text-base font-semibold text-slate-900">{{ selectedPhase.phaseLabel }}</h4>
          <p class="mt-1 text-xs text-slate-500">{{ selectedPhase.description || selectedPhase.phaseKey || '暂无阶段说明' }}</p>
        </div>
        <span :class="['rounded-full px-2.5 py-1 text-[11px] font-medium', selectedPhase.status === 'done' ? 'bg-emerald-50 text-emerald-700' : selectedPhase.status === 'blocked' ? 'bg-rose-50 text-rose-700' : selectedPhase.status === 'in_progress' ? 'bg-accent-50 text-accent-700' : 'bg-slate-100 text-slate-600']">{{ phaseStatusLabel(selectedPhase) }}</span>
      </div>
      <div class="mt-4 grid gap-3 sm:grid-cols-3">
        <div class="rounded-lg bg-slate-50 px-3 py-2"><p class="text-[10px] text-slate-400">阶段属性</p><p class="mt-1 text-xs font-medium text-slate-700">{{ selectedPhase.required ? '建议完成' : '按需阶段' }}</p></div>
        <div class="rounded-lg bg-slate-50 px-3 py-2"><p class="text-[10px] text-slate-400">计划时间</p><p class="mt-1 text-xs font-medium text-slate-700">{{ selectedPhase.plannedAt || '未设置' }}</p></div>
        <div class="rounded-lg bg-slate-50 px-3 py-2"><p class="text-[10px] text-slate-400">完成时间</p><p class="mt-1 text-xs font-medium text-slate-700">{{ selectedPhase.completedAt || '未完成' }}</p></div>
      </div>
      <div v-if="selectedPhase.note || phaseEvidence(selectedPhase)" class="mt-3 rounded-lg border border-slate-100 bg-slate-50/70 px-3 py-2">
        <p class="text-[10px] font-semibold text-slate-500">阶段备注与证据</p>
        <p class="mt-1 whitespace-pre-wrap text-xs leading-5 text-slate-700">{{ selectedPhase.note || phaseEvidence(selectedPhase) }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { SESSION_STORAGE_KEY } from '@/api/session-storage'
import { computed, ref, watch } from 'vue'
import { Layers } from 'lucide-vue-next'
import { api } from '../api/application-api'

const props = defineProps<{ requirement: any; revision?: number }>()
const phases = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showAdd = ref(false)
const selectedPhaseId = ref('')
const newPhase = ref({ phaseKey: '', phaseLabel: '', description: '' })
const statusOptions = [
  { key: 'todo', label: '待开始' }, { key: 'in_progress', label: '进行中' },
  { key: 'blocked', label: '已阻塞' }, { key: 'done', label: '已完成' }, { key: 'skipped', label: '已跳过' },
]
const selectedPhase = computed(() => phases.value.find(phase => String(phase.id) === String(selectedPhaseId.value)) || null)
function phaseStatusLabel(phase: any) {
  return phase?.statusLabel || statusOptions.find(item => item.key === phase?.status)?.label || phase?.status || '待开始'
}
function phaseEvidence(phase: any) {
  const raw = phase?.evidence
  if (!raw) return ''
  if (typeof raw === 'string') {
    try { const parsed = JSON.parse(raw); return parsed && typeof parsed === 'object' && Object.keys(parsed).length ? JSON.stringify(parsed, null, 2) : '' } catch { return raw }
  }
  return typeof raw === 'object' && Object.keys(raw).length ? JSON.stringify(raw, null, 2) : ''
}
function selectPhase(phase: any) { selectedPhaseId.value = String(phase?.id || '') }
function pickDefaultPhase() {
  const preferred = phases.value.find(phase => phase.status === 'in_progress')
    || [...phases.value].reverse().find(phase => phase.status === 'done')
    || phases.value[0]
  selectedPhaseId.value = preferred ? String(preferred.id) : ''
}
const canEdit = computed(() => {
  let user: any = {}
  try { user = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch {}
  if (['admin', 'super_admin'].includes(String(user.role || ''))) return true
  const name = String(user.name || user.devOwnerName || '')
  if (String(user.role || '') === 'editor') return true
  return !!name && [props.requirement?.assignee, props.requirement?.requester].some(value => String(value || '').split(/[,，]/).map(item => item.trim()).includes(name))
})

async function load() {
  if (!props.requirement?.id) return
  loading.value = true; error.value = ''
  const result: any = await api.getRequirementPhases(props.requirement.id)
  if (Array.isArray(result)) { phases.value = result; pickDefaultPhase() }
  else if (result === null) error.value = '阶段卡读取失败，请刷新重试'
  loading.value = false
}
async function savePhase(phase: any) {
  if (!canEdit.value || saving.value) return
  saving.value = true; error.value = ''
  const result: any = await api.updateRequirementPhase(props.requirement.id, phase.id, { status: phase.status, note: phase.note || '', description: phase.description || '', required: phase.required, sortOrder: phase.sortOrder })
  if (result) Object.assign(phase, result)
  else error.value = '阶段保存失败，请重试'
  saving.value = false
}
async function addPhase() {
  const key = newPhase.value.phaseKey.trim(), label = newPhase.value.phaseLabel.trim()
  if (!key || !label || saving.value) { error.value = '请填写阶段编号和名称'; return }
  saving.value = true; error.value = ''
  const result: any = await api.createRequirementPhase(props.requirement.id, { phaseKey: key, phaseLabel: label, description: newPhase.value.description, sortOrder: phases.value.length + 1 })
  if (result?.id) { phases.value.push(result); selectPhase(result); newPhase.value = { phaseKey: '', phaseLabel: '', description: '' }; showAdd.value = false }
  else error.value = '阶段保存失败，请重试'
  saving.value = false
}
watch(() => [props.requirement?.id, props.revision], load, { immediate: true })
</script>
