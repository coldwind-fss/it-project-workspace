<template>
  <div class="mt-3 rounded-lg border border-dashed border-gray-200 bg-gray-50/70 p-2.5" @paste="handlePaste">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-1.5 text-[11px] text-gray-500">
        <Paperclip class="h-3.5 w-3.5 text-violet-500" />
        <span>附件 · 支持粘贴图片，单文件最大50MB</span>
      </div>
      <label class="cursor-pointer text-[11px] font-medium text-violet-600 hover:text-violet-700">
        添加附件
        <input type="file" multiple class="hidden" accept="image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.zip,.rar,.7z" @change="handleInput" />
      </label>
    </div>
    <div v-if="files.length" class="mt-2 flex flex-wrap gap-1.5">
      <span v-for="(file, index) in files" :key="file.name + file.size + index" class="inline-flex max-w-[240px] items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-600">
        <span class="max-w-[190px] truncate" :title="file.name">{{ file.name }}</span>
        <span class="text-gray-400">{{ formatSize(file.size) }}</span>
        <button type="button" class="ml-1 text-gray-400 hover:text-red-500" @click="emit('remove', index)">×</button>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Paperclip } from 'lucide-vue-next'

defineProps<{ files: File[] }>()
const emit = defineEmits<{ (event: 'add', files: File[]): void; (event: 'remove', index: number): void }>()

function handleInput(event: Event) {
  const input = event.target as HTMLInputElement
  emit('add', Array.from(input.files || []))
  input.value = ''
}
function handlePaste(event: ClipboardEvent) {
  const items = Array.from(event.clipboardData?.items || [])
  const files = items.filter(item => item.kind === 'file').map(item => item.getAsFile()).filter(Boolean) as File[]
  if (!files.length) return
  event.preventDefault()
  emit('add', files.map((file, index) => {
    if (file.name && file.name !== 'image.png') return file
    const extension = file.type.split('/')[1] || 'bin'
    return new File([file], `clipboard-${Date.now()}-${index}.${extension}`, { type: file.type })
  }))
}
function formatSize(size: number) {
  return size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))}KB` : `${(size / 1024 / 1024).toFixed(1)}MB`
}
</script>
