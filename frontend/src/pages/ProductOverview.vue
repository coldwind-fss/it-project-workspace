<template>
  <div class="space-y-5 page-transition">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-gray-900">产品进展</h1>
        <p class="mt-1 text-sm text-gray-500">{{ productViewDescription }}；产品动态、L3 工作和双方讨论在这里按同一生态呈现。</p>
      </div>
      <div class="flex items-center gap-2">
        <div class="flex flex-wrap items-center gap-1 rounded-lg bg-gray-100 p-1">
          <button v-for="option in productViewOptions" :key="option.value" type="button"
            class="rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors"
            :class="productView === option.value ? 'bg-white text-accent-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="setProductView(option.value)">{{ option.label }}</button>
        </div>
        <select v-model="categoryFilter" class="feishu-input h-9 text-xs">
          <option value="">全部大类</option>
          <option v-for="item in categoryOptions" :key="item" :value="item">{{ item }}</option>
        </select>
        <button class="feishu-btn-ghost text-xs" @click="loadData">刷新</button>
      </div>
    </div>

    <div v-if="loading" class="flex h-64 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
    </div>
    <template v-else>
      <div class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-accent-100 bg-accent-50/40 px-3 py-2 text-xs">
        <span class="font-medium text-accent-700">当前视角：{{ productViewLabel }}</span>
        <span class="text-accent-600">{{ routeRangeLabel }} · {{ filteredProducts.length }} 个产品</span>
      </div>
      <div class="grid grid-cols-4 gap-3">
        <div v-for="item in summaryCards" :key="item.label" class="feishu-card">
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-500">{{ item.label }}</span>
            <component :is="item.icon" class="h-4 w-4" :class="item.iconClass" />
          </div>
          <p class="mt-2 text-2xl font-bold text-gray-900">{{ item.value }}</p>
          <p class="mt-1 text-[11px] text-gray-400">{{ item.hint }}</p>
        </div>
      </div>

      <div v-if="productView === 'work'" class="feishu-card">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">L3 当前工作视图</h2>
            <p class="mt-1 text-[11px] text-gray-400">吸收原需求看板的工作范围和状态判断；具体沟通直接在动态中完成。</p>
          </div>
          <button class="text-xs text-accent-600 hover:text-accent-700" @click="router.push('/requirements')">打开需求底库 →</button>
        </div>
        <div class="mb-3 grid grid-cols-4 gap-2">
          <div v-for="item in workStatusCards" :key="item.status" class="rounded-lg px-3 py-2" :class="item.className"><p class="text-[10px] text-gray-500">{{ item.status }}</p><p class="mt-1 text-lg font-bold">{{ item.value }}</p></div>
        </div>
        <div v-if="workRequirements.length" class="grid grid-cols-1 gap-2 md:grid-cols-2">
          <button v-for="item in workRequirements" :key="item.id" class="flex items-center gap-3 rounded-lg border border-gray-100 bg-gray-50/70 px-3 py-2 text-left hover:border-accent-200 hover:bg-accent-50/30" @click="router.push('/requirements/' + item.id)">
            <span class="h-2 w-2 shrink-0 rounded-full" :style="{ backgroundColor: statusColor(item.status) }" />
            <span class="min-w-0 flex-1"><span class="block truncate text-xs font-medium text-gray-800">{{ item.title }}</span><span class="mt-0.5 block truncate text-[10px] text-gray-400">{{ item.projectName }} · {{ item.assignee || '未分配' }}</span></span>
            <span class="shrink-0 rounded px-1.5 py-0.5 text-[10px]" :style="{ backgroundColor: statusColor(item.status) + '18', color: statusColor(item.status) }">{{ item.status }}</span>
          </button>
        </div>
        <p v-else class="rounded-lg bg-gray-50 px-3 py-5 text-center text-xs text-gray-400">当前没有未完成的 L3 工作。</p>
      </div>

      <div v-if="recentChanges.length" class="feishu-card">
        <div class="mb-3 flex items-center justify-between">
          <div>
            <h2 class="flex items-center gap-2 text-sm font-semibold text-gray-900"><Sparkles class="h-4 w-4 text-amber-500" />最近的重点变化</h2>
            <p class="mt-1 text-[11px] text-gray-400">突出产品能力、模块和流程发生的较大变化，细小工作仍在底库中完整保留。</p>
          </div>
          <button class="text-xs text-accent-600 hover:text-accent-700" @click="router.push('/requirements')">查看完整台账 →</button>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <button v-for="item in recentChanges" :key="item.id" class="rounded-lg border border-gray-100 bg-gray-50/70 p-3 text-left transition-colors hover:border-accent-200 hover:bg-accent-50/40" @click="router.push('/requirements/' + item.id)">
            <div class="flex items-start justify-between gap-2">
              <p class="min-w-0 truncate text-xs font-semibold text-gray-900">{{ item.title }}</p>
              <span class="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold" :style="{ backgroundColor: impactColor(item.impactLevel) + '18', color: impactColor(item.impactLevel) }">{{ item.impactLevel }}</span>
            </div>
            <p class="mt-1 truncate text-[11px] text-gray-400">{{ item.projectName }} · {{ item.type }} · {{ item.changeObject || '功能' }} · {{ item.workloadLevel || '中' }}工作量</p>
          </button>
        </div>
      </div>

      <div class="space-y-3">
        <div v-for="item in filteredProducts" :key="item.id" class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <button class="truncate text-base font-bold text-gray-900 hover:text-accent-600" @click="router.push('/projects/' + item.id)">{{ item.name }}</button>
                <span class="rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 font-mono text-[10px] text-gray-500">{{ item.currentVersion || '未设置版本' }}</span>
                <span class="rounded-full px-2 py-0.5 text-[10px] font-medium" :style="{ backgroundColor: projectStatusColor(item.status) + '18', color: projectStatusColor(item.status) }">{{ projectStatusLabel(item.status) }}</span>
              </div>
              <p class="mt-1 text-[11px] text-gray-400">{{ item.categoryName || '未分类' }} · {{ item.department || '未设置部门' }} · {{ item.businessOwner || '未设置业务负责人' }}</p>
            </div>
                <div class="flex items-center gap-3"><button class="text-xs text-violet-600 hover:text-violet-700" @click="focusedProjectId = focusedProjectId === item.id ? '' : item.id">{{ focusedProjectId === item.id ? '收起共享动态' : '查看共享动态' }}</button><button class="text-xs text-accent-600 hover:text-accent-700" @click="router.push('/projects/' + item.id)">进入产品详情 →</button></div>
          </div>

          <div class="mt-4 grid grid-cols-5 gap-2">
            <div class="rounded-lg bg-gray-50 p-2.5"><p class="text-[10px] text-gray-400">产品进度</p><p class="mt-1 text-lg font-bold text-gray-900">{{ progressPercent(item) }}%</p></div>
            <div class="rounded-lg bg-blue-50/70 p-2.5"><p class="text-[10px] text-blue-500">工作记录</p><p class="mt-1 text-lg font-bold text-blue-700">{{ item.total }}</p></div>
            <div class="rounded-lg bg-red-50/70 p-2.5"><p class="text-[10px] text-red-500">核心变化</p><p class="mt-1 text-lg font-bold text-red-700">{{ item.coreCount }}</p></div>
            <div class="rounded-lg bg-amber-50/70 p-2.5"><p class="text-[10px] text-amber-600">新增功能</p><p class="mt-1 text-lg font-bold text-amber-700">{{ item.addCount }}</p></div>
            <div class="rounded-lg bg-emerald-50/70 p-2.5"><p class="text-[10px] text-emerald-600">已交付</p><p class="mt-1 text-lg font-bold text-emerald-700">{{ item.doneCount }}</p></div>
          </div>

          <div class="mt-4 rounded-lg border border-accent-100 bg-accent-50/30 p-3">
            <div class="mb-2 flex items-center justify-between">
              <h3 class="flex items-center gap-2 text-xs font-semibold text-gray-800"><Layers3 class="h-3.5 w-3.5 text-accent-500" />产品发生了什么</h3>
              <span class="text-[10px] text-gray-400">重点展示 {{ item.notable.length }} 条 / 全部 {{ item.total }} 条</span>
            </div>
            <div v-if="item.notable.length" class="space-y-2">
              <button v-for="change in item.notable" :key="change.id" class="flex w-full items-start gap-2 rounded-lg bg-white px-3 py-2 text-left transition-colors hover:bg-accent-50" @click="router.push('/requirements/' + change.id)">
                <span class="mt-0.5 h-2 w-2 shrink-0 rounded-full" :style="{ backgroundColor: impactColor(change.impactLevel) }" />
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span class="text-xs font-semibold text-gray-900">{{ change.title }}</span>
                    <span class="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] text-blue-600">{{ change.type }}</span>
                    <span class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">{{ change.changeObject || '功能' }}</span>
                    <span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :style="{ backgroundColor: impactColor(change.impactLevel) + '18', color: impactColor(change.impactLevel) }">{{ change.impactLevel }}</span>
                  </div>
                  <p class="mt-0.5 text-[10px] text-gray-400">{{ change.status }} · {{ change.workloadLevel || '中' }}工作量 · {{ change.assignee || '未分配' }}</p>
                </div>
              </button>
            </div>
            <p v-else class="py-3 text-center text-xs text-gray-400">暂无重点变化，完整记录仍可在需求列表查看。</p>
            <div v-if="item.regularCount" class="mt-2 border-t border-accent-100 pt-2 text-[10px] text-gray-400">另有 {{ item.regularCount }} 条常规优化/细节工作已保留在 L3 台账中。</div>
          </div>
          <SharedActivityFeed v-if="focusedProjectId === item.id" scope-type="project" :scope-id="item.id" compact title="产品共享动态" subtitle="该 L2 产品下的 L3 进展、交付与业务讨论汇总在同一条动态生态中。" />
        </div>
        <div v-if="filteredProducts.length === 0" class="rounded-xl border border-dashed border-gray-200 bg-white py-12 text-center text-sm text-gray-400">暂无符合筛选条件的产品</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { CheckCircle2, Layers3, PackageOpen, Sparkles, Wrench } from 'lucide-vue-next'
import SharedActivityFeed from '../components/SharedActivityFeed.vue'
import { useProductOverviewPage } from "../features/system-insights/useProductOverviewPage"
const { route, router, loading, projects, requirements, categoryFilter, focusedProjectId, impactWeights, workloadWeights, typeColors, dashboardRanges, productViewOptions, currentUser, currentUserName, isManager, routeRange, routeCategory, routeProjectStatus, productView, productViewLabel, productViewDescription, effectiveRange, routeRangeLabel, routePeriodWindow, splitPeople, hasPerson, setProductView, inRoutePeriod, isFocusChange, categoryOptions, score, impactColor, projectStatusLabel, projectStatusBucket, isActiveProject, projectStatusColor, statusColor, progressPercent, productRows, filteredProducts, workRequirements, workStatusCards, allRows, recentChanges, summaryCards, loadData }=useProductOverviewPage()
</script>
