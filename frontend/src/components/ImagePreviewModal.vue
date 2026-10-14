<template>
  <div v-if="modelValue && images.length" class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/80 p-4" @click.self="close">
    <div class="flex h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
      <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold text-gray-800">{{ currentName }}</p>
          <p class="text-xs text-gray-400">{{ index + 1 }} / {{ images.length }} · 原图可缩放查看</p>
        </div>
        <div class="flex items-center gap-1">
          <button class="feishu-icon-btn" title="缩小" @click="zoomOut"><Minus class="h-4 w-4" /></button>
          <button class="min-w-12 text-xs font-semibold text-gray-600" title="重置缩放" @click="resetZoom">{{ Math.round(zoom * 100) }}%</button>
          <button class="feishu-icon-btn" title="放大" @click="zoomIn"><Plus class="h-4 w-4" /></button>
          <button class="ml-2 feishu-icon-btn" title="关闭" @click="close"><X class="h-4 w-4" /></button>
        </div>
      </div>
      <div class="relative flex min-h-0 flex-1 items-center justify-center overflow-auto bg-slate-100 p-6" @wheel.prevent="onWheel">
        <img :src="imageSrc(images[index])" :style="{ transform: `scale(${zoom})` }"
          class="max-h-[72vh] max-w-full origin-center rounded-md bg-white shadow-lg transition-transform duration-150" />
        <button v-if="images.length > 1" class="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white/90 p-2 text-accent-600 shadow hover:bg-white" title="上一张" @click="previous">
          <ChevronLeft class="h-5 w-5" />
        </button>
        <button v-if="images.length > 1" class="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-white/90 p-2 text-accent-600 shadow hover:bg-white" title="下一张" @click="next">
          <ChevronRight class="h-5 w-5" />
        </button>
      </div>
      <div v-if="images.length > 1" class="flex gap-2 overflow-x-auto border-t border-gray-100 px-4 py-3">
        <button v-for="(img, i) in images" :key="img?.id || i" :class="['h-12 w-12 shrink-0 overflow-hidden rounded border-2', i === index ? 'border-accent-500' : 'border-transparent']" @click="select(i)">
          <img :src="imageSrc(img)" class="h-full w-full object-cover" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, Minus, Plus, X } from 'lucide-vue-next'

const props = defineProps<{ modelValue: boolean; images: any[]; startIndex?: number }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()
const index = ref(0)
const zoom = ref(1)

watch(() => [props.modelValue, props.startIndex, props.images.length], () => {
  if (props.modelValue) {
    index.value = Math.min(Math.max(props.startIndex || 0, 0), Math.max(props.images.length - 1, 0))
    zoom.value = 1
  }
})

const currentName = computed(() => props.images[index.value]?.name || '交付进度反馈截图')
function imageSrc(img: any) { return img?.data || img?.url || img }
function close() { emit('update:modelValue', false) }
function resetZoom() { zoom.value = 1 }
function zoomIn() { zoom.value = Math.min(3, Number((zoom.value + 0.25).toFixed(2))) }
function zoomOut() { zoom.value = Math.max(0.5, Number((zoom.value - 0.25).toFixed(2))) }
function select(nextIndex: number) { index.value = nextIndex; resetZoom() }
function previous() { select((index.value - 1 + props.images.length) % props.images.length) }
function next() { select((index.value + 1) % props.images.length) }
function onWheel(event: WheelEvent) { event.deltaY < 0 ? zoomIn() : zoomOut() }
</script>
