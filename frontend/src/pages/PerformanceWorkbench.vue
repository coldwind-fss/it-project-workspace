<template>
  <div class="page-transition max-w-[1500px] space-y-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-xs font-semibold text-blue-600">个人月度结算</p>
        <h1 class="mt-1 text-xl font-bold text-gray-900">我的绩效工作台</h1>
        <p class="mt-1 text-sm text-gray-500">主表与原绩效表逐行对应；完成情况和数据来源由系统按证据归集。</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <label class="text-xs text-gray-500">结算月份<input v-model="month" type="month" class="field ml-2" :disabled="saving" @change="load" /></label>
        <button class="feishu-btn-primary" :disabled="saving || !payload" @click="save(false)">{{ saving ? '保存中…' : '保存草稿' }}</button>
        <button class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50" :disabled="saving || !payload || payload.record?.status === 'final'" @click="save(true)">定稿</button>
      </div>
    </div>

    <div v-if="loading" class="flex h-48 items-center justify-center"><div class="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" /></div>
    <div v-else-if="!payload" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800">当前账号无法读取个人绩效工作台。该页面仅对十叶开放。</div>
    <template v-else>
      <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <div class="metric"><span>结算月份</span><b>{{ month }}</b><small>{{ payload.draft?.ruleVersion || '规则版本待生成' }}</small></div>
        <div class="metric"><span>当前状态</span><b class="text-blue-600">{{ payload.record?.status === 'final' ? '已定稿' : '草稿' }}</b><small>{{ payload.record?.finalizedAt || '尚未冻结快照' }}</small></div>
        <div class="metric"><span>自动归集分</span><b>{{ displayScore(payload.draft?.summary?.autoScore, payload.draft?.summary?.autoScoreMax) }}</b><small>仅展示已有可计算事实</small></div>
        <div class="metric"><span>数据完整度</span><b>{{ payload.draft?.summary?.dataCompleteness ?? 0 }}%</b><small>七条方向中已形成完整结论的比例</small></div>
        <div class="metric"><span>待补 / 待人工</span><b class="text-amber-600">{{ payload.draft?.summary?.pendingCount ?? 0 }}</b><small>缺口不会按 0 分计算</small></div>
      </section>

      <section class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 px-5 py-4">
          <div><h2 class="text-base font-semibold text-gray-900">{{ month }} 个人绩效结算表</h2><p class="mt-1 text-xs text-gray-500">本人：{{ payload.draft?.userName || '十叶' }} · 规则版本：{{ payload.draft?.ruleVersion }}</p></div>
          <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">完成情况由系统生成</span>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-[1350px] w-full table-fixed text-left text-xs">
            <colgroup><col class="w-12" /><col class="w-[180px]" /><col class="w-[440px]" /><col class="w-[250px]" /><col class="w-[390px]" /><col class="w-20" /></colgroup>
            <thead class="bg-blue-50 text-blue-700"><tr><th class="px-4 py-3 font-semibold">#</th><th class="px-4 py-3 font-semibold">考核指标</th><th class="px-4 py-3 font-semibold">评分细则</th><th class="px-4 py-3 font-semibold">数据来源</th><th class="px-4 py-3 font-semibold">完成情况</th><th class="px-4 py-3 font-semibold">权重</th></tr></thead>
            <tbody class="divide-y divide-gray-100 align-top">
              <tr v-for="row in payload.draft?.rows || []" :key="row.key" class="hover:bg-blue-50/20">
                <td class="px-4 py-4 text-lg font-semibold text-gray-400">{{ row.index }}</td>
                <td class="px-4 py-4"><p class="font-semibold leading-5 text-gray-900">{{ row.indicator }}</p><span class="mt-2 inline-flex rounded-full px-2 py-1 text-[10px]" :class="statusClass(row.completion?.status)">{{ statusLabel(row.completion?.status) }}</span></td>
                <td class="px-4 py-4"><p class="whitespace-pre-wrap leading-5 text-gray-600">{{ row.scoringRule?.text }}</p><div class="mt-3 flex flex-wrap gap-1.5"><span v-for="item in row.scoringRule?.subItems || []" :key="item.key" class="rounded bg-gray-50 px-2 py-1 text-[10px] text-gray-500">{{ item.label }} {{ item.maxScore }}分</span></div></td>
                <td class="px-4 py-4"><div class="space-y-2"><div v-for="source in row.dataSources || []" :key="source.type" class="rounded-lg border border-gray-100 bg-gray-50 px-2.5 py-2"><div class="flex items-center justify-between gap-2"><span class="font-medium text-gray-700">{{ source.label }}</span><span class="text-blue-600">{{ source.count }}条</span></div><p class="mt-1 text-[10px] text-gray-400">{{ source.period }} · {{ source.type }}</p></div></div></td>
                <td class="px-4 py-4"><p class="font-medium leading-5 text-gray-800">{{ row.completion?.summary }}</p><div class="mt-3 space-y-1.5"><div v-for="fact in row.completion?.facts || []" :key="fact.label" class="flex items-start justify-between gap-3 rounded bg-gray-50 px-2.5 py-1.5"><span class="text-gray-500">{{ fact.label }}</span><span class="text-right font-medium text-gray-700">{{ fact.value }}</span></div></div><div v-if="row.completion?.gaps?.length" class="mt-3 rounded-lg border border-amber-100 bg-amber-50 px-2.5 py-2 text-[11px] leading-5 text-amber-800"><span class="font-semibold">待补：</span>{{ row.completion.gaps.join('；') }}</div><details class="mt-3 rounded-lg border border-gray-100 px-2.5 py-2"><summary class="cursor-pointer text-[11px] font-medium text-blue-700">查看得分口径与证据</summary><div class="mt-2 space-y-1.5 text-[11px] leading-5 text-gray-500"><p>当前得分：{{ scoreText(row.score) }} · 权重 {{ percent(row.weight) }}</p><p>计算依据：{{ row.score?.basis || '暂无' }}</p><p>证据记录：{{ row.completion?.evidenceIds?.length || 0 }} 条（由服务端生成）</p></div></details></td>
                <td class="px-4 py-4 text-center"><span class="text-base font-semibold text-blue-700">{{ percent(row.weight) }}</span><p class="mt-2 text-[10px] text-gray-400">{{ scoreText(row.score) }}</p></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_400px]">
        <div class="rounded-2xl border border-gray-200 bg-white p-5"><h2 class="text-sm font-semibold text-gray-900">系统结算说明</h2><div class="mt-3 space-y-2 text-xs leading-5 text-gray-600"><p>数据来源列展示系统实际归集的模块、记录数和月份；完成情况列展示实际值、目标值、达成情况和数据缺口。</p><p>只有服务端确认具备完整数据的子项才会形成自动计算结果；五级满意度、响应时长、健康检查、直属领导评价等尚未接入的内容会标记为待补或待人工，不会按 0 分计算。</p><p v-if="payload.record?.status === 'final'" class="font-medium text-emerald-700">本月已定稿，当前展示的是冻结的证据和规则快照。</p></div></div>
        <aside class="space-y-4"><div class="rounded-2xl border border-blue-100 bg-blue-50/40 p-4"><h2 class="text-sm font-semibold text-gray-900">本月工作内容</h2><label class="label">月度目标<textarea v-model="form.goals" class="field area" placeholder="本月要达成什么？" /></label><label class="label">工作计划<textarea v-model="form.plan" class="field area" placeholder="计划和重点安排" /></label><label class="label">下月计划<textarea v-model="form.nextPlan" class="field area" placeholder="下月计划" /></label></div><div class="rounded-2xl border border-gray-200 bg-white p-4"><h2 class="text-sm font-semibold text-gray-900">月度总结补充</h2><textarea v-model="form.finalText" class="field mt-3 min-h-[160px] w-full" placeholder="可以补充背景、反思和未结构化事项；不能替代系统完成情况。" /><p class="mt-2 text-[11px] text-gray-400">这段文字只作为人工补充，系统结算仍以表格中的来源和完成情况为准。</p></div></aside>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { usePerformanceWorkbenchPage } from "../features/system-insights/usePerformanceWorkbenchPage"
const { month, loading, saving, payload, form, percent, displayScore, scoreText, statusLabel, statusClass, load, save }=usePerformanceWorkbenchPage()
</script>

<style scoped>
.field { border:1px solid #d1d5db; border-radius:.65rem; background:#fff; padding:.6rem .75rem; font-size:.8rem; outline:none; }
.field:focus { border-color:#60a5fa; box-shadow:0 0 0 2px #dbeafe; }
.metric { border:1px solid #e5e7eb; border-radius:.9rem; background:#fff; padding:1rem; display:flex; flex-direction:column; gap:.3rem; }
.metric span { font-size:.72rem; color:#6b7280; }
.metric b { font-size:1.2rem; color:#111827; }
.metric small { font-size:.65rem; color:#9ca3af; line-height:1.4; }
.label { display:block; margin-top:.8rem; font-size:.72rem; font-weight:600; color:#4b5563; }
.area { display:block; width:100%; min-height:56px; margin-top:.35rem; resize:vertical; font-weight:400; }
</style>
