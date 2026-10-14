<template>
  <main class="min-h-screen overflow-y-auto bg-slate-50 px-4 py-6 sm:px-6 sm:py-10">
    <div class="mx-auto w-full max-w-2xl">
      <div class="mb-5 flex items-center gap-3"><div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-lg font-bold text-white shadow-sm">果</div><div><p class="text-sm font-semibold text-gray-900">业务反馈</p><p class="text-[11px] text-gray-500">用不到一分钟告诉 IT 当前使用情况</p></div></div>
      <section v-if="successMessage" class="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm sm:p-8"><div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-2xl text-emerald-600">✓</div><h1 class="mt-4 text-center text-lg font-semibold text-gray-900">{{ successMessage }}</h1><p class="mt-2 text-center text-sm leading-6 text-gray-500">感谢反馈，内容已回写 IT 项目记录。</p><p v-if="uploadError" class="mt-4 rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2 text-left text-xs leading-5 text-amber-700">{{ uploadError }}</p></section>
      <section v-else class="overflow-hidden rounded-2xl border border-emerald-100 bg-white shadow-sm">
        <div class="border-b border-emerald-100 bg-gradient-to-r from-emerald-50 via-white to-blue-50 px-5 py-5 sm:px-7"><p class="text-xs font-semibold text-emerald-600">{{ stage?.label || '成果回访' }}</p><h1 class="mt-1 text-lg font-semibold text-gray-900">{{ stage?.title || '请补充反馈' }}</h1><p class="mt-2 text-xs leading-5 text-gray-500">{{ stage?.description || '几句话即可，不需要填写复杂指标。' }}</p></div>
        <div class="space-y-5 px-5 py-5 sm:px-7 sm:py-6">
          <div v-if="errorMessage" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2.5 text-xs leading-5 text-amber-700">{{ errorMessage }}</div>
          <div v-if="loading" class="py-10 text-center text-sm text-gray-400">正在准备回访表单...</div>
          <template v-else-if="context">
            <div class="rounded-xl border border-gray-100 bg-gray-50/70 px-4 py-3"><p class="text-sm font-semibold text-gray-900">{{ context.demand?.title }}</p><p class="mt-1 text-[11px] text-gray-500">{{ request?.recipientName || '业务负责人' }} · {{ context.demand?.projectName || context.demand?.department || '项目' }}</p><div v-if="request?.stage !== 'goal' && context.valueCard?.expected?.summary" class="mt-3 rounded-lg border border-blue-100 bg-blue-50/70 px-3 py-2 text-xs leading-5 text-blue-800"><span class="font-medium">上线前目标：</span>{{ context.valueCard.expected.summary }}</div></div>
            <div v-if="request?.status === 'submitted'" class="rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-3 text-xs leading-6 text-emerald-800">这次回访已经提交过，无需重复填写。</div>
            <template v-else-if="request?.stage === 'goal'">
              <div class="rounded-lg border border-blue-100 bg-blue-50/60 px-3 py-2.5 text-xs leading-5 text-blue-800">只需要确认一个方向即可，不是绩效填报，也不要求填写数字。暂时没有明确目标时可以直接选择“暂时没有明确目标”。</div>
              <label class="block"><span class="form-label">上线后最希望看到的变化 <span class="font-normal text-gray-400">（可选）</span></span><textarea v-model="form.desiredChange" rows="4" maxlength="10000" class="feishu-input w-full resize-y" placeholder="例如：少填表、少核对、处理更快；软件评测也可以写希望验证什么。" :disabled="form.noGoal" /></label>
              <label class="flex cursor-pointer items-center gap-2 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5 text-xs text-gray-600"><input v-model="form.noGoal" type="checkbox" class="rounded border-gray-300 text-accent-500" />暂时没有明确目标，先按需求内容推进</label>
              <label class="block"><span class="form-label">补充说明 <span class="font-normal text-gray-400">（可选）</span></span><textarea v-model="form.currentState" rows="3" maxlength="10000" class="feishu-input w-full resize-y" placeholder="如果有需要补充的背景、当前做法或验证范围，可以写在这里。" /></label>
            </template>
            <template v-else-if="request?.stage === 'day7'">
              <div class="grid gap-3 sm:grid-cols-3">
                <label class="block"><span class="form-label">现在是否能使用 <span class="text-rose-500">*</span></span><select v-model="form.useStatus" class="feishu-input w-full"><option value="">请选择</option><option value="已正常使用">已正常使用</option><option value="已开始使用但有问题">已开始使用但有问题</option><option value="还未开始使用">还未开始使用</option></select></label>
                <label class="block"><span class="form-label">原问题是否解决 <span class="text-rose-500">*</span></span><select v-model="form.goalStatus" class="feishu-input w-full"><option value="">请选择</option><option value="已解决">已解决</option><option value="部分解决">部分解决</option><option value="暂未解决">暂未解决</option><option value="还无法判断">还无法判断</option></select></label>
                <label class="block"><span class="form-label">整体感受 <span class="text-rose-500">*</span></span><select v-model="form.satisfaction" class="feishu-input w-full"><option value="">请选择</option><option value="满意">满意</option><option value="基本满意">基本满意</option><option value="需要调整">需要调整</option></select></label>
              </div>
              <label class="block"><span class="form-label">补充说明 <span class="font-normal text-gray-400">（可选）</span></span><textarea v-model="form.summary" rows="3" maxlength="10000" class="feishu-input w-full resize-y" placeholder="如果有具体使用场景、问题细节或其他想说明的内容，可以写在这里。" /></label>
              <p class="rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-2 text-xs leading-5 text-emerald-800">上面的三个选项为必填；补充说明按需填写。</p>
            </template>
            <template v-else>
              <label class="block"><span class="form-label">实际上线效果 <span class="text-rose-500">*</span></span><select v-model="form.effectStatus" class="feishu-input w-full"><option value="">请选择</option><option value="明显改善">明显改善</option><option value="有一定改善">有一定改善</option><option value="暂无明显改善">暂无明显改善</option><option value="暂时无法判断">暂时无法判断</option></select></label>
              <div><span class="form-label">主要体现在哪些方面 <span class="font-normal text-gray-400">（可选）</span></span><div class="flex flex-wrap gap-2"><label v-for="item in changeTypeOptions" :key="item" class="cursor-pointer rounded-full border px-3 py-1.5 text-xs transition" :class="form.changeTypes.includes(item) ? 'border-emerald-400 bg-emerald-50 text-emerald-700' : 'border-gray-200 bg-white text-gray-600 hover:border-emerald-200'"><input v-model="form.changeTypes" type="checkbox" :value="item" class="sr-only" />{{ item }}</label></div></div>
              <label class="block"><span class="form-label">补充实际结果 <span v-if="day30NeedsDetail" class="text-rose-500">*</span><span v-else class="font-normal text-gray-400">（可选）</span></span><textarea v-model="form.summary" rows="3" maxlength="10000" class="feishu-input w-full resize-y" placeholder="一句话说明实际变化即可，例如：每天少花 20 分钟。" /></label>
            </template>
            <details v-if="request?.stage === 'day30' && structuredMetricRows.length" class="rounded-lg border border-blue-100 bg-blue-50/50 px-3 py-2.5">
              <summary class="cursor-pointer text-xs font-medium text-blue-800">补充结构化实际值（可选）</summary>
              <p class="mt-2 text-[10px] leading-4 text-blue-700">只填写你手头有的数据；没有数字可以只提交上面的文字回访，不会按 0 计算。</p>
              <div class="mt-3 space-y-2">
                <div v-for="metric in form.metricResults" :key="metric.key" class="grid gap-2 rounded-lg border border-blue-100 bg-white p-2.5 sm:grid-cols-[minmax(0,1fr)_110px_110px_130px] sm:items-end">
                  <div><p class="text-[11px] font-medium text-gray-800">{{ metric.label || metric.key }} <span v-if="metric.unit" class="font-normal text-gray-400">（{{ metric.unit }}）</span></p><p class="mt-1 text-[10px] text-gray-400">上线前 {{ displayValue(metric.baselineValue) }} · 目标 {{ displayValue(metric.targetValue) }}</p></div>
                  <label class="block"><span class="form-label">上线后实际值</span><input v-model="metric.actualValue" type="number" step="any" class="feishu-input w-full" placeholder="可留空" /></label>
                  <label class="block"><span class="form-label">是否达成</span><select v-model="metric.targetMet" class="feishu-input w-full"><option value="">待判断</option><option :value="true">达成</option><option :value="false">未达成</option></select></label>
                  <label class="block"><span class="form-label">数据来源</span><input v-model="metric.source" class="feishu-input w-full" placeholder="业务填写 / 报表" /></label>
                </div>
              </div>
            </details>
            <AttachmentPicker :files="files" @add="addFiles" @remove="removeFile" />
            <div v-if="uploadError" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2 text-xs leading-5 text-amber-700">{{ uploadError }}</div>
            <div class="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-[11px] leading-5 text-gray-400">只用于改进 IT 交付，不是绩效打分表。</p><button type="button" class="feishu-btn-primary justify-center px-5" :disabled="saving || !canSubmit" @click="submit">{{ saving ? '提交中...' : '提交反馈' }}</button></div>
          </template>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import AttachmentPicker from '../components/AttachmentPicker.vue'
import { useDemandOutcomeEntryPage } from "../features/demand-delivery/useDemandOutcomeEntryPage"
const { token, context, request, stage, form, files, loading, saving, errorMessage, uploadError, successMessage, changeTypeOptions, day30NeedsDetail, structuredMetricRows, canSubmit, addFiles, removeFile, displayValue, hydrateMetricResults, readToken, submit } = useDemandOutcomeEntryPage()
</script>

<style scoped>
.form-label { display: block; margin-bottom: 0.35rem; font-size: 0.7rem; color: #6b7280; }
</style>
