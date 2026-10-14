<template>
  <div class="space-y-6">
    <div v-if="loading" class="flex h-64 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
    </div>

    <template v-else>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <span class="text-xs text-gray-500">{{ periodLabel }}</span>
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex rounded-lg bg-gray-100 p-0.5">
            <button v-for="option in periodOptions" :key="option.value" @click="setDashboardRange(option.value)"
              :class="['rounded-md px-3 py-1.5 text-xs font-medium transition-colors', dashboardRange === option.value ? 'bg-white text-accent-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
              {{ option.label }}
            </button>
          </div>
          <button @click="syncDashboard" class="feishu-btn-primary">
            <Send class="h-3.5 w-3.5" /> 同步大盘
          </button>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-accent-100 bg-accent-50/40 px-3 py-2 text-xs">
        <span class="font-medium text-accent-700">统计范围：{{ periodLabel }}</span>
        <span class="text-accent-600">{{ periodRequirements.length }} 条本期工作记录 · {{ changedProductCount }} 个变动产品</span>
      </div>

      <!-- The four cards are entry points, not explanatory KPI boxes. -->
      <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <div v-for="item in overviewStats" :key="item.key" class="relative" @mouseenter="hoveredCard = item.key" @mouseleave="hoveredCard = ''">
          <button type="button" class="feishu-card group w-full min-h-[132px] rounded-2xl text-left transition-shadow hover:border-accent-200 hover:shadow-md active:scale-[0.99]" @click="openCardRoute(item.key)">
            <div class="flex items-center justify-between">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl" :class="item.bg">
                <component :is="item.icon" class="h-5 w-5" :class="item.iconClass" />
              </div>
              <span class="text-2xl font-bold text-gray-900">{{ item.value }}</span>
            </div>
            <p class="mt-2 text-sm font-medium text-gray-600">{{ item.label }}</p>
            <p class="mt-1 text-[10px] text-gray-400">{{ item.desc }}</p>
          </button>

          <!-- The outer bridge keeps the hover state alive while the pointer moves into the panel. -->
          <div v-if="hoveredCard === item.key" class="absolute left-0 right-0 top-full z-30 pt-2" @click.stop>
            <div class="rounded-2xl border border-gray-200 bg-white p-3 shadow-xl">
              <div class="mb-2 flex items-center justify-between gap-2">
                <span class="text-xs font-semibold text-gray-800">{{ item.popoverTitle }}</span>
                <button type="button" class="text-[10px] text-accent-600 hover:text-accent-700" @click.stop="openCardRoute(item.key)">查看全部 →</button>
              </div>
              <div v-if="cardPopoverRows(item.key).length" class="space-y-1.5">
                <button v-for="row in cardPopoverRows(item.key).slice(0, 6)" :key="row.key" type="button" class="flex w-full items-center justify-between gap-2 rounded-lg bg-gray-50 px-2.5 py-2 text-left hover:bg-accent-50" @click.stop="openPopoverRow(row)">
                  <span class="min-w-0 truncate text-[11px] font-medium text-gray-700">{{ row.label }}</span>
                  <span class="shrink-0 text-[10px] text-gray-400">{{ row.meta }}</span>
                </button>
              </div>
              <p v-else class="py-3 text-center text-[11px] text-gray-400">本期暂无数据</p>
            </div>
          </div>
        </div>
      </div>

      <!-- L3 records are projected into an L2 product lifecycle summary. -->
      <section class="feishu-card border border-accent-100">
        <div class="mb-4 flex flex-wrap items-end justify-between gap-2">
          <h2 class="flex items-center gap-2 text-sm font-semibold text-gray-900">
            <Sparkles class="h-4 w-4 text-accent-500" /> 产品发生了什么
          </h2>
          <div class="text-right text-[11px] text-gray-400">
            <span>变动产品 {{ changedProductCount }} 个</span>
            <span class="mx-1">·</span>
            <span>重点产品 {{ focusProductCount }} 个</span>
          </div>
        </div>
        <div class="mb-3 flex flex-wrap items-center gap-1.5 border-b border-gray-100 pb-3 text-[10px] text-gray-500">
          <span class="mr-1 font-medium text-gray-400">按 L3 工作类型：</span>
          <span v-for="type in visibleWorkTypes" :key="type" class="inline-flex items-center gap-1 rounded-full border px-2 py-1" :style="typeBadgeStyle(type)">
            <span class="h-1.5 w-1.5 rounded-full" :style="{ backgroundColor: typeColor(type) }" />{{ typeLabel(type) }}
          </span>
        </div>

        <div v-if="productChangeGroups.length" class="max-h-[560px] overflow-y-auto pr-1">
          <div class="grid gap-3 xl:grid-cols-3">
            <article v-for="group in productChangeGroups" :key="group.key" class="rounded-xl border border-gray-100 bg-gray-50/60 p-3 transition-colors hover:border-accent-200 hover:bg-accent-50/30">
              <div class="flex items-start justify-between gap-2">
                <button type="button" class="min-w-0 text-left" @click="openProduct(group.projectId)">
                  <p class="truncate text-sm font-semibold text-gray-900 hover:text-accent-600">{{ group.name }}</p>
                  <p class="mt-0.5 truncate text-[10px] text-gray-400">{{ group.categoryName || '未分类' }} · {{ projectStatusLabel(group.project?.status) }} · {{ group.totalCount }} 条本期工作</p>
                </button>
                <span class="shrink-0 rounded bg-white px-1.5 py-0.5 text-[10px] font-semibold text-accent-600">{{ group.focusCount ? `${group.focusCount} 项重点` : '常规变化' }}</span>
              </div>

              <div class="mt-2 flex items-center gap-2">
                <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200">
                  <div class="h-full rounded-full" :style="{ width: projectProgressPercent(group.project) + '%', backgroundColor: projectProgressColor(group.project) }" />
                </div>
                <span class="text-[10px] font-semibold text-gray-500">{{ projectProgressPercent(group.project) }}%</span>
              </div>

              <div class="mt-2 flex flex-wrap gap-1">
                <span v-for="item in group.changeSummary" :key="item.label" v-show="item.value" class="rounded bg-white px-1.5 py-0.5 text-[10px]" :style="{ color: item.color }">{{ item.label }} {{ item.value }}</span>
              </div>

              <p class="mt-2 text-[11px] font-medium leading-5 text-gray-600">{{ productHeadline(group) }}</p>
              <div class="mt-1 flex flex-wrap gap-1">
                <span v-for="stage in group.lifecycleStages" :key="stage.label" v-show="stage.value" class="rounded border border-white bg-white/70 px-1.5 py-0.5 text-[10px] text-gray-500">{{ stage.label }} {{ stage.value }}</span>
              </div>

              <div class="mt-3 rounded-lg border border-white bg-white/80 p-2.5">
                <p class="text-[10px] font-semibold text-gray-500">{{ group.highlights.length ? '主要变化' : '本期变化' }}</p>
                <div v-if="group.displayChanges.length" class="mt-1.5 space-y-1.5">
                  <button v-for="change in group.displayChanges" :key="change.id" type="button" class="flex w-full items-start gap-2 rounded-lg border border-transparent px-2 py-1.5 text-left hover:border-accent-100 hover:bg-accent-50/60" @click="openRequirement(change.id)">
                    <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full" :style="{ backgroundColor: typeColor(change.type) }" />
                    <span class="min-w-0 flex-1">
                      <span class="block truncate text-[11px] font-semibold text-gray-800">{{ change.title }}</span>
                      <span class="mt-0.5 flex flex-wrap gap-1 text-[10px] text-gray-400">
                        <span class="rounded px-1 py-0.5" :style="{ backgroundColor: tierColor(change) + '18', color: tierColor(change) }">{{ displayTierLabel(change) }}</span>
                        <span class="rounded px-1 py-0.5 font-medium" :style="typeBadgeStyle(change.type)">{{ displayType(change) }}</span>
                        <span>{{ change.impactLevel || '常规' }} · {{ change.workloadLevel || '中' }}工作量</span>
                      </span>
                    </span>
                  </button>
                </div>
                <p v-else class="mt-1.5 text-[11px] text-gray-400">本期以细节优化为主</p>
              </div>

              <div class="mt-2 flex items-center justify-between gap-2 border-t border-gray-100 pt-2 text-[10px] text-gray-400">
                <span v-if="group.otherCount">其余 {{ group.otherCount }} 条工作记录</span>
                <span v-else>本期重点变化已全部展示</span>
                <button type="button" class="shrink-0 text-accent-600 hover:text-accent-700" @click="openProductLedger(group.projectId)">查看 L3 底库 →</button>
              </div>
            </article>
          </div>
        </div>
        <div v-else class="rounded-lg border border-dashed border-gray-200 py-10 text-center text-xs text-gray-400">本统计周期暂无产品变化。</div>
      </section>

      <section class="feishu-card">
        <div class="mb-4 flex flex-wrap items-end justify-between gap-2">
          <h2 class="flex items-center gap-2 text-sm font-semibold text-gray-900"><Users class="h-4 w-4 text-accent-500" /> 开发者工作成果</h2>
          <button type="button" class="text-[11px] text-accent-600 hover:text-accent-700" @click="openWorkspace('workload')">进入工作台 →</button>
        </div>

        <div class="grid gap-3 xl:grid-cols-3">
          <article v-for="row in developerRows" :key="row.name" role="button" tabindex="0" class="cursor-pointer rounded-xl border bg-white p-4 text-left transition-colors hover:border-accent-200 hover:bg-accent-50/30" :class="selectedDeveloper === row.name ? 'border-accent-300 bg-accent-50/40 shadow-sm' : 'border-gray-100'" @click="selectDeveloper(row.name)" @keydown.enter="selectDeveloper(row.name)">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="truncate text-sm font-bold text-gray-900">{{ row.name }}</p>
                <p class="mt-0.5 text-[10px] text-gray-400">参与产品 {{ row.productCount }} 个</p>
              </div>
              <div class="text-right"><p class="text-2xl font-bold text-accent-600">{{ row.workloadScore }}</p><p class="text-[10px] text-gray-400">工作量分</p></div>
            </div>
            <div class="mt-4 grid grid-cols-3 gap-2 text-center">
              <div class="rounded-lg bg-gray-50 px-2 py-2"><p class="text-lg font-bold text-gray-900">{{ row.recordCount }}</p><p class="text-[10px] text-gray-400">工作记录</p></div>
              <div class="rounded-lg bg-emerald-50 px-2 py-2"><p class="text-lg font-bold text-emerald-700">{{ row.doneCount }}</p><p class="text-[10px] text-emerald-600">已交付</p></div>
              <div class="rounded-lg bg-red-50 px-2 py-2"><p class="text-lg font-bold text-red-700">{{ row.focusCount }}</p><p class="text-[10px] text-red-600">重点变化</p></div>
            </div>
            <div class="mt-3">
              <div class="flex h-2 overflow-hidden rounded-full bg-gray-100"><span class="bg-red-400" :style="{ width: workloadPercent(row, '大') + '%' }" /><span class="bg-blue-400" :style="{ width: workloadPercent(row, '中') + '%' }" /><span class="bg-slate-300" :style="{ width: workloadPercent(row, '小') + '%' }" /></div>
              <div class="mt-1 flex justify-between text-[10px] text-gray-400"><span>大 {{ row.largeCount }}</span><span>中 {{ row.mediumCount }}</span><span>小 {{ row.smallCount }}</span></div>
            </div>
            <div class="mt-3 space-y-1.5">
              <button v-for="item in row.workRows" :key="item.id" type="button" class="flex w-full items-start gap-2 rounded-lg border border-transparent px-2 py-1.5 text-left hover:border-accent-100 hover:bg-white" @click.stop="openRequirement(item.id)">
                <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" :style="{ backgroundColor: typeColor(item.type) }" />
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-[11px] font-medium text-gray-700">{{ item.title }}</span>
                  <span class="mt-0.5 flex flex-wrap gap-1 text-[10px] text-gray-400">
                    <span class="rounded px-1 py-0.5 font-medium" :style="typeBadgeStyle(item.type)">{{ displayType(item) }}</span>
                    <span>{{ item.projectName || projectForRow(item)?.name || '未归属产品' }}</span>
                  </span>
                </span>
              </button>
              <p v-if="row.otherWorkCount" class="text-[10px] text-gray-400">另有 {{ row.otherWorkCount }} 条工作记录</p>
              <p v-if="!row.workRows.length" class="text-[11px] text-gray-400">本期暂无工作记录</p>
            </div>
            <p class="mt-3 text-[10px] text-accent-600">点击开发者查看本期全部工作明细</p>
          </article>
        </div>

        <div v-if="selectedDeveloper" class="mt-4 rounded-lg border border-accent-100 bg-accent-50/30 p-4">
          <div class="mb-2 flex items-center justify-between"><h3 class="text-xs font-semibold text-gray-800">{{ selectedDeveloper }} · 本期工作明细</h3><button class="text-[10px] text-accent-600" @click="selectedDeveloper = ''">收起</button></div>
          <div class="grid max-h-64 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            <button v-for="item in selectedDeveloperDetails" :key="item.id" type="button" class="flex items-start justify-between gap-3 rounded-lg bg-white px-3 py-2 text-left hover:bg-accent-50" @click="openRequirement(item.id)">
              <span class="min-w-0"><span class="block truncate text-xs font-medium text-gray-900">{{ item.title }}</span><span class="mt-0.5 block text-[10px] text-gray-400">{{ item.projectName || '未归属产品' }} · {{ displayType(item) }}</span></span>
              <span class="shrink-0 text-[10px] font-semibold" :style="{ color: impactColor(item.impactLevel) }">{{ item.impactLevel || '常规' }} · {{ item.workloadLevel || '中' }}</span>
            </button>
          </div>
          <p v-if="!selectedDeveloperDetails.length" class="py-3 text-center text-xs text-gray-400">本期暂无工作记录</p>
        </div>
      </section>

    </template>
  </div>
</template>

<script setup lang="ts">
import { FolderKanban, PackageCheck, PlusCircle, Send, Sparkles, Users } from 'lucide-vue-next'
import { useDashboardOverviewPage } from "../features/system-insights/useDashboardOverviewPage"
const { route, router, loading, projects, requirements, selectedDeveloper, hoveredCard, validRanges, initialRange, dashboardRange, periodOptions, terminalStatuses, workloadWeights, impactWeights, preferredDevelopers, visibleWorkTypes, legacyTypeAliases, setDashboardRange, dashboardQuery, monthQuery, openProduct, openProductLedger, openRequirement, openWorkspace, openCardRoute, openPopoverRow, parseDate, periodWindow, periodLabel, inPeriod, requirementInPeriod, periodRequirements, isActiveProject, activeProjectList, periodNewRequirementList, splitPeople, matchesPerson, normalizedType, displayTier, changeScore, isFocusChange, changedProductIds, changedProductCount, totalWorkloadScore, doneCount, projectForRow, rowProjectName, sortedRows, productChangeGroups, focusProductCount, deliveredProductGroups, focusChangeList, overviewStats, preferredDeveloperNames, developerRows, selectedDeveloperDetails, cardPopoverRows, selectDeveloper, workloadPercent, typeColor, typeLabel, typeBadgeStyle, displayType, displayTierLabel, tierColor, productHeadline, impactColor, projectProgressPercent, projectProgressColor, projectStatusLabel, syncDashboard }=useDashboardOverviewPage()
</script>
