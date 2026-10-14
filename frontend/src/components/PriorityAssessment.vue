<template>
  <div class="rounded-lg border border-blue-100 bg-blue-50/40">
    <button type="button" class="flex w-full items-center justify-between px-3 py-2 text-left" @click="expanded = !expanded">
      <span class="text-xs font-semibold text-blue-700">智能评估优先级</span>
      <span class="text-[11px] text-blue-500">
        {{ complete ? `建议 ${result.recommendedPriority} · ${result.score}分` : '回答4个问题' }}
        <ChevronDown class="ml-1 inline h-3 w-3 transition-transform" :class="expanded ? 'rotate-180' : ''" />
      </span>
    </button>
    <div v-if="expanded" class="space-y-2 border-t border-blue-100 px-3 py-3">
      <div v-for="item in questions" :key="item.key" class="grid grid-cols-[72px_1fr] items-center gap-2">
        <span class="text-[11px] text-slate-500">{{ item.label }}</span>
        <div class="flex flex-wrap gap-1">
          <button v-for="option in item.options" :key="option.value" type="button"
            :class="['rounded-md border px-2 py-1 text-[11px] transition-colors', modelValue?.[item.key] === option.value ? 'border-blue-400 bg-blue-500 text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-blue-300']"
            @click="select(item.key, option.value)">{{ option.label }}</button>
        </div>
      </div>
      <div class="rounded-md bg-white px-3 py-2 text-xs text-slate-600">
        <template v-if="complete">
          系统建议 <strong class="text-blue-700">{{ result.recommendedPriority }}</strong>（{{ result.score }}分）
          <span class="ml-2 text-[11px] text-slate-400">项目 {{ projectPriority || 'P2' }} 系数 ×{{ result.projectCoefficient }}</span>
          <button v-if="priority !== result.recommendedPriority" type="button" class="ml-2 font-semibold text-blue-600 hover:text-blue-700" @click="adoptRecommendation">采用建议</button>
        </template>
        <span v-else class="text-slate-400">完成4项选择后自动计算建议优先级。</span>
      </div>
      <div v-if="complete && needsOverride" class="space-y-1">
        <label class="text-[11px] text-amber-700">当前优先级高于系统建议，请填写原因 *</label>
        <input :value="modelValue?.overrideReason || ''" class="feishu-input w-full bg-white" placeholder="例如：管理层确认需提前处理"
          @input="select('overrideReason', ($event.target as HTMLInputElement).value)" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { calculatePriorityAssessment, isPriorityAssessmentComplete, needsPriorityOverrideReason, type PriorityAssessment } from '../utils/priorityAssessment'

const props = defineProps<{ modelValue?: PriorityAssessment; priority: string; projectPriority?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: PriorityAssessment]; adopt: [priority: string] }>()
const expanded = ref(false)

const questions: Array<{ key: keyof PriorityAssessment; label: string; options: Array<{ label: string; value: string }> }> = [
  { key: 'scope', label: '影响范围', options: [{ label: '个人', value: 'personal' }, { label: '部门', value: 'department' }, { label: '多部门', value: 'multiple' }, { label: '全公司', value: 'company' }] },
  { key: 'urgency', label: '紧急程度', options: [{ label: '不紧急', value: 'normal' }, { label: '本月', value: 'month' }, { label: '本周', value: 'week' }, { label: '立即', value: 'immediate' }] },
  { key: 'impact', label: '业务影响', options: [{ label: '体验优化', value: 'experience' }, { label: '效率影响', value: 'efficiency' }, { label: '业务受阻', value: 'blocked' }, { label: '核心不可用', value: 'outage' }] },
  { key: 'blocking', label: '阻塞上线', options: [{ label: '否', value: 'no' }, { label: '是', value: 'yes' }] },
]

const result = computed(() => calculatePriorityAssessment(props.modelValue || {}, props.projectPriority || 'P2'))
const complete = computed(() => isPriorityAssessmentComplete(props.modelValue))
const needsOverride = computed(() => needsPriorityOverrideReason(props.priority, result.value))

function select(key: keyof PriorityAssessment, value: any) {
  emit('update:modelValue', calculatePriorityAssessment({ ...(props.modelValue || {}), [key]: value }, props.projectPriority || 'P2'))
}

function adoptRecommendation() {
  if (result.value.recommendedPriority) emit('adopt', result.value.recommendedPriority)
}

watch(() => props.projectPriority, () => {
  if (complete.value) emit('update:modelValue', calculatePriorityAssessment(props.modelValue || {}, props.projectPriority || 'P2'))
})
watch(() => props.priority, priority => {
  if ((priority === 'P0' || priority === 'P1') && !complete.value) expanded.value = true
}, { immediate: true })
</script>
