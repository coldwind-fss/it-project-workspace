<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="feishu-input mt-1 flex min-h-9 w-full items-center justify-between gap-2 text-left"
      :disabled="disabled"
      :class="disabled ? 'cursor-not-allowed bg-gray-50 text-gray-400' : ''"
      @click="!disabled && (open = !open)"
    >
      <span :class="selected.length ? 'text-gray-900' : 'text-gray-400'" class="min-w-0 flex-1 truncate">
        {{ selected.length ? selected.join('、') : placeholder }}
      </span>
      <span class="shrink-0 text-xs text-gray-400">{{ selected.length ? `${selected.length} 人` : '' }}</span>
      <ChevronDown class="h-3.5 w-3.5 shrink-0 text-accent-500" :class="open ? 'rotate-180' : ''" />
    </button>

    <div v-if="open" class="absolute z-[80] mt-1 w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-xl">
      <div class="border-b border-gray-100 p-2">
        <div class="relative">
          <Search class="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
          <input v-model="query" class="feishu-input w-full pl-7" :placeholder="searchPlaceholder" @click.stop @keydown.stop />
        </div>
      </div>
      <div class="max-h-56 overflow-auto py-1">
        <label v-for="option in filteredOptions" :key="option" class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm text-gray-800 hover:bg-accent-50">
          <input type="checkbox" class="rounded border-gray-300 text-accent-500 focus:ring-accent-400" :checked="selected.includes(option)" @change="toggle(option)" />
          <span class="truncate">{{ option }}</span>
        </label>
        <p v-if="filteredOptions.length === 0" class="px-3 py-4 text-center text-xs text-gray-400">未找到匹配人员</p>
      </div>
      <div class="flex items-center justify-between border-t border-gray-100 px-3 py-2">
        <button type="button" class="text-xs text-gray-400 hover:text-red-500" @click="clear">清空</button>
        <button type="button" class="text-xs font-medium text-accent-600 hover:text-accent-700" @click="open = false">完成</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ChevronDown, Search } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  modelValue?: string
  options?: string[]
  placeholder?: string
  searchPlaceholder?: string
  disabled?: boolean
}>(), {
  modelValue: '',
  options: () => [],
  disabled: false,
  placeholder: '搜索或选择人员',
  searchPlaceholder: '输入关键字检索',
})

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const root = ref<HTMLElement | null>(null)
const open = ref(false)
const query = ref('')

const selected = computed(() => Array.from(new Set(
  String(props.modelValue || '').split(/[,，]/).map(item => item.trim()).filter(Boolean)
)))
const normalizedOptions = computed(() => Array.from(new Set((props.options || []).filter(Boolean))))
const filteredOptions = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return keyword ? normalizedOptions.value.filter(item => item.toLowerCase().includes(keyword)) : normalizedOptions.value
})

function update(values: string[]) {
  emit('update:modelValue', Array.from(new Set(values)).join(', '))
}
function toggle(option: string) {
  if (props.disabled) return
  update(selected.value.includes(option) ? selected.value.filter(item => item !== option) : [...selected.value, option])
}
function clear() { if (!props.disabled) update([]) }
function onDocumentClick(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>
