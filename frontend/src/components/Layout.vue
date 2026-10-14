<template>
  <div class="app-shell">
    <Sidebar />
    <div class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <Header />
      <div v-if="PREVIEW_ENTRY" role="note" class="shrink-0 border-b border-blue-100 bg-blue-50 px-4 py-2 text-xs leading-5 text-blue-800">项目展示：当前使用演示数据；钉钉身份与通知使用模拟集成，未向钉钉实际发送消息。</div>
      <main class="app-main-scroll min-h-0 min-w-0 flex-1 overflow-auto p-2 md:p-3">
        <div v-if="entranceProblem" role="alert" class="mx-auto mt-12 max-w-lg rounded-xl border border-amber-200 bg-white p-6 text-center">
          <h3 class="font-semibold text-gray-900">暂时无法进入系统</h3>
          <p class="my-4 text-sm text-gray-600">{{ entranceProblem }}</p>
          <button type="button" class="feishu-btn-primary" @click="retryEntrance">重新进入</button>
        </div>
        <div v-else class="mx-auto h-full min-h-0 w-full max-w-none min-w-0 page-transition">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import { PREVIEW_ENTRY,entranceProblem,retryEntrance } from '../features/access/preview-entry'
</script>
