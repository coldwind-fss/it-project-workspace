<template>
  <div class="page-transition space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">操作记录</h1>
        <p class="text-sm text-gray-500 mt-1">记录 L1 大类、L2 项目、L3 需求的新增、修改和删除操作。</p>
      </div>
    </div>

    <div class="bg-white rounded-lg border border-gray-200 p-3 flex items-center gap-3">
      <select v-model="filters.entityType" @change="loadData" class="feishu-input w-32">
        <option value="">全部层级</option>
        <option value="L1">L1 大类</option>
        <option value="L2">L2 项目</option>
        <option value="L3">L3 需求</option>
      </select>
      <select v-model="filters.action" @change="loadData" class="feishu-input w-32">
        <option value="">全部动作</option>
        <option value="create">新增</option>
        <option value="update">修改</option>
        <option value="delete">删除</option>
      </select>
      <div class="relative flex-1 max-w-sm">
        <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
        <input v-model="filters.keyword" @keyup.enter="loadData" placeholder="搜索对象、操作人、摘要" class="feishu-input pl-8 w-full" />
      </div>
      <button @click="loadData" class="feishu-btn-primary">查询</button>
    </div>

    <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <table class="feishu-table">
        <thead>
          <tr>
            <th class="w-28">时间</th>
            <th class="w-20">层级</th>
            <th class="w-20">动作</th>
            <th>对象</th>
            <th class="w-28">操作人</th>
            <th>摘要</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" class="feishu-row">
            <td class="text-xs text-gray-400">{{ row.createdAt }}</td>
            <td><span class="feishu-badge bg-gray-100 text-gray-600">{{ row.entityType }}</span></td>
            <td><span class="feishu-badge" :class="actionClass(row.action)">{{ actionText(row.action) }}</span></td>
            <td class="font-medium text-gray-900">{{ row.entityName }} <span class="text-xs text-gray-400">{{ row.entityId }}</span></td>
            <td class="text-xs text-gray-500">{{ row.operator || '系统' }}</td>
            <td class="text-xs text-gray-500">{{ row.summary }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="rows.length === 0" class="text-center text-sm text-gray-400 py-12">暂无操作记录</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import { useOperationRecordsPage } from "../features/system-insights/useOperationRecordsPage"
const { rows, filters, actionText, actionClass, loadData }=useOperationRecordsPage()
</script>
