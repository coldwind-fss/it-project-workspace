<template>
  <div class="page-transition max-w-4xl">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-bold text-gray-900">知识库</h1>
        <p class="text-sm text-gray-500 mt-1">项目文档、API文档、设计稿统一管理</p>
      </div>
      <button class="btn-primary"><Plus class="w-4 h-4" /> 上传文档</button>
    </div>

    <div class="space-y-4">
      <div v-for="group in grouped" :key="group.type" class="bg-white rounded-xl border border-gray-100 p-5">
        <h3 class="font-semibold text-gray-900 flex items-center gap-2 mb-4">
          <component :is="group.icon" class="w-4 h-4" :style="{ color: group.color }" />
          {{ group.label }}
          <span class="text-xs text-gray-400 font-normal">({{ group.docs.length }})</span>
        </h3>
        <div class="grid grid-cols-2 gap-3">
          <div v-for="doc in group.docs" :key="doc.id"
            class="flex items-center gap-3 p-3 rounded-lg border border-gray-50 hover:bg-gray-50/50 hover:border-gray-200 transition-all cursor-pointer"
          >
            <div class="w-9 h-9 rounded-lg flex items-center justify-center" :style="{ backgroundColor: group.color + '15' }">
              <component :is="group.icon" class="w-4 h-4" :style="{ color: group.color }" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">{{ doc.title }}</p>
              <p class="text-xs text-gray-400 truncate">{{ doc.description }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ doc.projectName }} · {{ doc.uploadedBy }} · {{ doc.createdAt }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus, FileText, BookOpen, Palette, Database } from 'lucide-vue-next'
import { useKnowledgeBasePage } from "../features/system-insights/useKnowledgeBasePage"
const { allDocs, configs, grouped }=useKnowledgeBasePage()
</script>
