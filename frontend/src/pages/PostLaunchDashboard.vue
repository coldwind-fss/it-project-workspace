<template>
  <div class="page-transition space-y-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-xs font-semibold text-blue-600">领导 / 管理者入口</p>
        <h1 class="mt-1 text-xl font-bold text-gray-900">上线后管理看板</h1>
        <p class="mt-1 text-sm text-gray-500">系统自动汇总已经产生的交付、验收、回访和价值数据；缺少分母时不按 0 计算。</p>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="dashboard?.generatedAt" class="hidden text-[11px] text-gray-400 sm:inline">更新于 {{ dashboard.generatedAt }}</span>
        <router-link to="/postlaunch/operations" class="feishu-btn-ghost border border-gray-200 bg-white">进入运营记录</router-link>
        <button class="feishu-btn-ghost border border-gray-200 bg-white" @click="refresh">刷新</button>
      </div>
    </div>

    <div v-if="loading" class="flex h-48 items-center justify-center"><div class="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" /></div>
    <template v-else>
      <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-3"><div><h2 class="text-sm font-semibold text-gray-900">六项核心指标</h2><p class="mt-1 text-xs text-gray-500">指标只读取真实交付、业务验收和上线回执；每张卡同时显示分子、分母和覆盖情况。</p></div><span class="rounded-full bg-slate-100 px-3 py-1 text-[11px] text-slate-500">{{ dashboard?.summary?.operations || 0 }} 条交付记录</span></div>
        <div class="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <div v-for="metric in metricCards" :key="metric.key" class="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
            <p class="text-xs text-gray-500">{{ metric.label }}</p>
            <p class="mt-1 text-2xl font-bold text-slate-900">{{ metric.value == null ? '暂无数据' : metric.value + '%' }}</p>
            <p class="mt-1 text-[10px] text-gray-500">{{ metric.denominator ? metric.numerator + ' / ' + metric.denominator : '暂无可计算样本' }}<span v-if="metric.coverage != null"> · 覆盖 {{ metric.coverage }}%</span></p>
            <p class="mt-1 text-[10px] leading-4 text-gray-400">{{ metric.note }}</p>
          </div>
        </div>
      </section>

      <section class="rounded-2xl border border-blue-100 bg-blue-50/40 p-4">
        <div class="flex flex-wrap items-end gap-3">
          <label class="filter-label">归属部门<input v-model="filters.department" class="field mt-1 w-36" placeholder="全部部门" /></label>
          <label class="filter-label">项目类型<select v-model="filters.solutionType" class="field mt-1 w-44"><option value="">全部项目类型</option><option v-for="item in projectTypeOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label class="filter-label">上线月份<input v-model="filters.deliveryMonth" type="month" class="field mt-1 w-40" /></label>
          <label class="filter-label">价值状态<select v-model="filters.valueStatus" class="field mt-1 w-44"><option value="">全部价值状态</option><option v-for="item in valueStatusOptions" :key="item" :value="item">{{ item }}</option></select></label>
          <button class="feishu-btn-primary" @click="refresh">应用筛选</button>
          <button class="feishu-btn-ghost border border-gray-200 bg-white" @click="clearFilters">清空筛选</button>
        </div>
      </section>
      <div v-if="dashboard?.excludedOperations" class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs leading-5 text-slate-600">已排除 {{ dashboard.excludedOperations }} 条未完成需求池完整链路的运营记录；这些记录仍保留在“上线后运营记录”，但不参与价值验证和管理看板统计。</div>

      <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 px-4 py-3"><div><h2 class="text-sm font-semibold text-gray-900">产品价值结果</h2><p class="mt-1 text-[11px] text-gray-400">每个产品 / L2 一行；点击“查看详情”打开指标来源和原始回访记录。</p></div><span class="text-xs text-gray-400">{{ projectRows.length }} 个产品</span></div>
        <div v-if="projectRows.length" class="overflow-x-auto">
          <table class="min-w-[1080px] w-full text-left text-xs">
            <thead class="bg-slate-50 text-[11px] text-gray-500"><tr><th class="px-4 py-3 font-medium">产品 / L2</th><th class="px-3 py-3 font-medium">交付</th><th class="px-3 py-3 font-medium">验收</th><th class="px-3 py-3 font-medium">3 天回执</th><th class="px-3 py-3 font-medium">30 天验证</th><th class="px-3 py-3 font-medium">满意度</th><th class="px-3 py-3 font-medium">使用率</th><th class="px-3 py-3 font-medium">提效数据</th><th class="px-4 py-3 font-medium">操作</th></tr></thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="project in projectRows" :key="project.key" class="hover:bg-blue-50/30">
                <td class="px-4 py-3"><p class="max-w-[230px] truncate font-semibold text-gray-900">{{ project.name }}</p><p class="mt-1 text-[10px] text-gray-400">{{ project.department || '未设置部门' }} · {{ project.l3Count }} 个事项</p><span v-if="project.missing.length" class="mt-1 inline-flex rounded bg-amber-50 px-1.5 py-0.5 text-[10px] text-amber-700">待补数据 {{ project.missing.length }} 项</span></td>
                <td class="px-3 py-3 text-gray-600">{{ project.delivery }}</td>
                <td class="px-3 py-3" :class="project.acceptance === '全部通过' ? 'text-emerald-600' : 'text-gray-600'">{{ project.acceptance }}</td>
                <td class="px-3 py-3" :class="project.day7 === '已提交' ? 'text-emerald-600' : 'text-amber-600'">{{ project.day7 }}</td>
                <td class="px-3 py-3" :class="project.day30 === '已提交' ? 'text-emerald-600' : 'text-amber-600'">{{ project.day30 }}</td>
                <td class="px-3 py-3 font-medium text-gray-700">{{ project.satisfaction }}</td>
                <td class="px-3 py-3 font-medium text-gray-700">{{ project.usage }}</td>
                <td class="px-3 py-3 font-medium text-gray-700">{{ project.efficiency }}</td>
                <td class="px-4 py-3"><button type="button" class="text-blue-700 hover:text-blue-900" @click="openProject(project)">查看详情 →</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-4 py-12 text-center text-sm text-gray-400">暂无可汇总的交付结果</div>
      </section>

      <section class="overflow-hidden rounded-2xl border border-amber-200 bg-amber-50/40 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-amber-100 px-4 py-3"><div><h2 class="text-sm font-semibold text-amber-900">待补数据</h2><p class="mt-1 text-[11px] text-amber-700">这里列出影响管理指标计算的缺失项；文字说明仍然保留，不会被错误当成数字。</p></div><span class="text-xs text-amber-700">{{ missingDataRows.length }} 条</span></div>
        <div v-if="missingDataRows.length" class="divide-y divide-amber-100">
          <div v-for="row in missingDataRows" :key="row.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3"><div><p class="text-xs font-semibold text-gray-900">{{ row.projectName || '独立 L3' }} · {{ row.title }}</p><p class="mt-1 text-[10px] text-amber-700">缺少：{{ row.metricDataStatus.missing.join('、') }}</p></div><router-link :to="{ path: '/postlaunch/operations', query: { operationId: row.id } }" class="text-[11px] font-medium text-blue-700">进入运营记录 →</router-link></div>
        </div>
        <div v-else class="px-4 py-8 text-center text-sm text-emerald-700">暂无待补数据</div>
      </section>
    </template>

    <div v-if="selectedProject" class="fixed inset-0 z-50 bg-slate-950/40" @click.self="selectedProject = null">
      <aside class="absolute right-0 top-0 h-full w-full max-w-2xl overflow-y-auto bg-white shadow-2xl">
        <div class="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-blue-100 bg-white px-5 py-4"><div><p class="text-xs font-semibold text-blue-600">产品价值详情</p><h2 class="mt-1 text-lg font-bold text-gray-900">{{ selectedProject.name }}</h2><p class="mt-1 text-xs text-gray-500">{{ selectedProject.department || '未设置部门' }} · {{ selectedProject.l3Count }} 个 L3 事项</p></div><button type="button" class="text-xl text-gray-400 hover:text-gray-700" aria-label="关闭" @click="selectedProject = null">×</button></div>
        <div class="space-y-4 p-5">
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-4"><div v-for="item in [{ label: '满意度', value: selectedProject.satisfaction }, { label: '使用率', value: selectedProject.usage }, { label: '提效数据', value: selectedProject.efficiency }, { label: '验收', value: selectedProject.acceptance }]" :key="item.label" class="rounded-xl bg-slate-50 p-3"><p class="text-[10px] text-gray-500">{{ item.label }}</p><p class="mt-1 text-sm font-semibold text-gray-800">{{ item.value }}</p></div></div>
          <div v-if="selectedProject.missing.length" class="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs leading-5 text-amber-800"><span class="font-semibold">待补数据：</span>{{ selectedProject.missing.join('、') }}</div>
          <div v-for="row in selectedProjectRows" :key="row.id" class="rounded-xl border border-gray-200 p-4">
            <div class="flex flex-wrap items-start justify-between gap-2"><div><h3 class="text-sm font-semibold text-gray-900">{{ row.title }}</h3><p class="mt-1 text-[10px] text-gray-500">交付 {{ row.deliveryDate || '未记录' }} · 3 天 {{ stageStatus(row, 'day7') }} · 30 天 {{ stageStatus(row, 'day30') }}</p></div><router-link :to="{ path: '/postlaunch/operations', query: { operationId: row.id } }" class="text-[11px] text-blue-700" @click="selectedProject = null">打开运营记录</router-link></div>
            <div class="mt-3 grid gap-3 sm:grid-cols-2"><div class="rounded-lg bg-blue-50/60 p-3"><p class="text-[10px] font-medium text-blue-700">指标来源</p><p class="mt-1 text-[11px] leading-5 text-gray-600">上线前基线、目标值来自成果卡；上线后实际值来自 30 天价值验证。{{ row.metricDataStatus?.missing?.length ? '当前仍有数据缺口。' : '当前数据可参与计算。' }}</p></div><div class="rounded-lg bg-emerald-50/60 p-3"><p class="text-[10px] font-medium text-emerald-700">数据状态</p><p class="mt-1 text-[11px] leading-5 text-gray-600">{{ row.metricDataStatus?.missing?.length ? row.metricDataStatus.missing.join('、') : '数据完整' }}</p></div></div>
            <div v-if="structuredMetricRows(row).length" class="mt-3 overflow-x-auto rounded-lg border border-gray-100"><table class="min-w-[700px] w-full text-left text-[10px]"><thead class="bg-gray-50 text-gray-500"><tr><th class="px-2 py-2 font-medium">指标</th><th class="px-2 py-2 font-medium">单位</th><th class="px-2 py-2 font-medium">上线前</th><th class="px-2 py-2 font-medium">目标</th><th class="px-2 py-2 font-medium">上线后</th><th class="px-2 py-2 font-medium">前后变化</th><th class="px-2 py-2 font-medium">结果</th></tr></thead><tbody class="divide-y divide-gray-100"><tr v-for="metric in structuredMetricRows(row)" :key="metric.key"><td class="px-2 py-2 text-gray-700">{{ metric.label }}</td><td class="px-2 py-2 text-gray-500">{{ metric.unit || '—' }}</td><td class="px-2 py-2">{{ displayValue(metric.baselineValue) }}</td><td class="px-2 py-2">{{ displayValue(metric.targetValue) }}</td><td class="px-2 py-2">{{ displayValue(metric.actualValue) }}</td><td class="px-2 py-2">{{ metric.changeText }}</td><td class="px-2 py-2" :class="metric.targetMet === true ? 'text-emerald-600' : metric.targetMet === false ? 'text-rose-600' : 'text-gray-500'">{{ metric.targetMet === true ? '达成' : metric.targetMet === false ? '未达成' : '待实际值' }}</td></tr></tbody></table></div>
            <div class="mt-3 space-y-2 text-[11px] leading-5"><p><span class="font-medium text-gray-700">3 天回执：</span>{{ rawOutcome(row, 'day7') }}</p><p><span class="font-medium text-gray-700">30 天价值验证：</span>{{ rawOutcome(row, 'day30') }}</p></div>
          </div>
          <div v-if="!selectedProjectRows.length" class="py-8 text-center text-sm text-gray-400">暂无明细记录</div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePostLaunchDashboardPage } from "../features/system-insights/usePostLaunchDashboardPage"
const { route, router, loading, dashboard, rows, projects, selectedProject, filters, valueStatusOptions, metricDefinitions, metricCards, l2Rows, projectTypeOptions, projectRows, missingDataRows, selectedProjectRows, deliverySummary, acceptanceSummary, projectStageSummary, stageStatus, rateForRows, efficiencyForRows, formatRate, displayValue, metricResultsForRow, structuredMetricRows, numericValue, rawOutcome, openProject, clearFilters, refresh }=usePostLaunchDashboardPage()
</script>

<style scoped>
.field { border: 1px solid #d1d5db; border-radius: .65rem; background: white; padding: .6rem .75rem; font-size: .8rem; outline: none; }
.field:focus { border-color: #60a5fa; box-shadow: 0 0 0 2px #dbeafe; }
.filter-label { display: block; font-size: .7rem; color: #64748b; }
</style>
