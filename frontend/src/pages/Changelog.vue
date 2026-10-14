<template>
  <div class="page-transition">
    <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-gray-900">变更日志</h1>
        <p class="mt-1 text-sm text-gray-500">按产品聚合查看变化，原始操作明细按需展开。</p>
      </div>
      <div class="flex items-center gap-2">
        <select v-model="projectFilter" class="feishu-input h-9 text-xs">
          <option value="">全部产品</option>
          <option v-for="item in productOptions" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <button type="button" class="feishu-btn-ghost text-xs" @click="loadData">刷新</button>
      </div>
    </div>

    <div v-if="!loading" class="mb-4 grid grid-cols-3 gap-3">
      <div v-for="item in summaryCards" :key="item.label" class="feishu-card">
        <p class="text-xs text-gray-500">{{ item.label }}</p>
        <p class="mt-2 text-2xl font-bold text-gray-900">{{ item.value }}</p>
        <p class="mt-1 text-[11px] text-gray-400">{{ item.hint }}</p>
      </div>
    </div>

    <div v-if="loading" class="flex h-64 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
    </div>

    <div v-else-if="productGroups.length" class="space-y-4">
      <section v-for="group in productGroups" :key="group.key" class="feishu-card">
        <div class="flex flex-wrap items-start justify-between gap-3 border-b border-gray-100 pb-3">
          <div class="min-w-0">
            <button type="button" class="truncate text-base font-bold text-gray-900 hover:text-accent-600" @click="openProduct(group.projectId)">{{ group.name }}</button>
            <p class="mt-1 text-[11px] text-gray-400">{{ group.categoryName }} · 最近变化 {{ formatDate(group.latestAt) }}</p>
          </div>
          <div class="text-right text-[11px] text-gray-400">
            <p><span class="font-semibold text-accent-600">{{ group.eventCount }}</span> 项产品变化</p>
            <p class="mt-1">{{ group.operationCount }} 次操作明细</p>
          </div>
        </div>

        <div class="mt-3 flex flex-wrap gap-1.5">
          <span v-for="item in group.typeSummary" :key="item.label" class="rounded-full px-2 py-1 text-[10px] font-medium" :style="typeBadgeStyle(item.label)">{{ item.label }} {{ item.count }}</span>
        </div>

        <div class="mt-3 space-y-2">
          <article v-for="event in group.events" :key="event.key" class="rounded-lg border border-gray-100 bg-gray-50/60 p-3">
            <div class="flex flex-wrap items-start justify-between gap-2">
              <button type="button" class="min-w-0 text-left" @click="openRequirement(event.requirementId)">
                <p class="truncate text-sm font-semibold text-gray-900 hover:text-accent-600">{{ event.requirementTitle }}</p>
                <p class="mt-1 text-[11px] text-gray-400">{{ event.workTypes.join('、') || '字段变更' }} · {{ event.impactLevel }} · {{ event.workloadLevel }}工作量</p>
              </button>
              <span class="shrink-0 text-[10px] text-gray-400">{{ formatDateTime(event.latestAt) }}</span>
            </div>

            <div class="mt-2 flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-2 text-[10px] text-gray-400">
              <span>{{ event.changeCount }} 项字段变化 · {{ event.operators.join('、') || '未知操作人' }}</span>
              <button type="button" class="text-accent-600 hover:text-accent-700" @click="toggleEvent(event.key)">{{ expandedEvents.has(event.key) ? '收起操作明细 ↑' : '查看操作明细 ↓' }}</button>
            </div>

            <div v-if="expandedEvents.has(event.key)" class="mt-2 space-y-1.5 border-t border-gray-100 pt-2">
              <div v-for="change in event.details" :key="change.id" class="rounded-md bg-white px-2.5 py-2 text-[11px]">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <span class="font-medium text-gray-700"><span class="mr-1 rounded px-1 py-0.5 text-[10px] text-white" :style="{ backgroundColor: getConfig(change.changeType).color }">{{ change.changeType || '字段变更' }}</span>{{ change.fieldName || '未命名字段' }}</span>
                  <span class="text-[10px] text-gray-400">{{ formatDateTime(change.createdAt) }} · {{ change.operator || '未知操作人' }}</span>
                </div>
                <div class="mt-1 flex flex-wrap items-center gap-1.5 text-[10px]">
                  <span class="max-w-[42%] truncate text-red-500 line-through" :title="change.oldValue">{{ change.oldValue || '空' }}</span>
                  <span class="text-gray-300">→</span>
                  <span class="max-w-[42%] truncate font-medium text-emerald-600" :title="change.newValue">{{ change.newValue || '空' }}</span>
                  <span v-if="change.reason" class="text-gray-400">· {{ change.reason }}</span>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-else class="feishu-card py-16 text-center text-sm text-gray-400">
      当前没有可展示的变更记录。
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChangelogPage } from "../features/project-work/useChangelogPage"
const { router, loading, changelogs, requirements, projects, projectFilter, expandedEvents, typeAliases, typeColors, impactRank, workloadRank, requirementMap, productOptions, toTime, formatDate, formatDateTime, normalizedType, workTypeLabel, typeColor, typeBadgeStyle, productGroups, summaryCards, toggleEvent, openRequirement, openProduct, getConfig, loadData, changeTypeConfig } = useChangelogPage()
</script>
