<template>
  <main class="h-screen min-h-screen overflow-y-auto overscroll-contain bg-slate-50 px-4 py-5 sm:px-6 sm:py-8">
    <div class="mx-auto w-full max-w-2xl">
      <div class="mb-5 flex items-center gap-3"><div class="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600 text-lg font-bold text-white shadow-sm">评</div><div><p class="text-sm font-semibold text-gray-900">需求池业务评估</p><p class="text-[11px] text-gray-500">直属领导 / 部门负责人意见</p></div></div>
      <section v-if="successMessage" class="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm sm:p-8"><div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-2xl text-emerald-600">✓</div><h1 class="mt-4 text-center text-lg font-semibold text-gray-900">{{ successMessage }}</h1><p class="mt-2 text-center text-sm leading-6 text-gray-500">评估意见已回写需求池，IT 可以据此形成综合结论。</p></section>
      <section v-else class="overflow-hidden rounded-2xl border border-violet-100 bg-white shadow-sm">
        <div class="border-b border-violet-100 bg-gradient-to-r from-violet-50 via-white to-blue-50 px-5 py-5 sm:px-7"><p class="text-xs font-semibold text-violet-600">{{ review?.reviewerRoleLabel || '业务评估' }}</p><h1 class="mt-1 text-lg font-semibold text-gray-900">请评估这项需求是否值得承接</h1><p class="mt-2 text-xs leading-5 text-gray-500">请先查看需求原始信息和 IT 初筛摘要，只需判断业务必要性和优先级，不需要填写业务价值或期望结果。</p></div>
        <div class="space-y-5 px-5 py-5 sm:px-7 sm:py-6">
          <div v-if="errorMessage" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2.5 text-xs leading-5 text-amber-700">{{ errorMessage }}</div>
          <div v-if="loading" class="py-10 text-center text-sm text-gray-400">正在读取评估单...</div>
          <template v-else-if="review">
            <div class="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm sm:px-5 sm:py-5">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-slate-700">需求初始信息</p>
                  <p class="mt-1 text-[11px] leading-5 text-slate-400">业务提出的原始需求，以及 IT 的初步判断</p>
                </div>
                <div class="flex flex-wrap items-center justify-end gap-2 text-[11px]"><span class="rounded bg-violet-50 px-1.5 py-0.5 font-semibold text-violet-600">{{ review.statusLabel }}</span><span class="text-slate-400">评估人：{{ review.reviewerName || '-' }}</span></div>
              </div>
              <div class="mt-4 border-t border-slate-100 pt-4">
                <p class="text-sm font-semibold text-gray-900">{{ review.demand?.title }}</p>
                <p class="mt-1 text-[11px] leading-5 text-gray-500">{{ review.demand?.department || '未填写部门' }} · 提出人：{{ review.demand?.requesterName || '-' }} · {{ review.demand?.projectName || '暂未归类项目' }}</p>
                <p class="mt-3 whitespace-pre-wrap rounded-lg bg-slate-50 px-3 py-2 text-xs leading-6 text-gray-600">{{ review.demand?.description }}</p>
                <div v-if="review.demand?.attachments?.length" class="mt-3 flex flex-wrap items-center gap-2"><span class="text-[11px] text-gray-400">相关资料：</span><a v-for="attachment in review.demand.attachments" :key="attachment.id" :href="attachment.url" target="_blank" rel="noopener" class="inline-flex max-w-full items-center rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-[11px] text-blue-700 hover:border-blue-300 hover:bg-blue-50"><span class="truncate">{{ attachment.originalName }}</span></a></div>
              </div>
              <div class="mt-5 border-t border-slate-100 pt-4">
                <div class="flex flex-wrap items-center justify-between gap-2"><p class="text-xs font-semibold text-blue-800">IT 初筛判断</p><span class="text-[10px] text-slate-400">只读说明</span></div>
                <p class="mt-1 text-[11px] leading-5 text-slate-500">以下内容由 IT 根据需求原始资料完成，用于帮助评估是否值得承接及其优先级。</p>
                <dl class="mt-3 grid grid-cols-1 gap-x-5 gap-y-2 text-[11px] sm:grid-cols-2">
                  <div><dt class="inline text-slate-400">解决方案类型：</dt><dd class="inline font-medium text-slate-700">{{ review.demand?.solutionTypeLabel || '待判断' }}</dd></div>
                  <div><dt class="inline text-slate-400">IT 建议：</dt><dd class="inline font-medium text-slate-700">{{ review.demand?.intakePathLabel || '待判断' }}</dd></div>
                  <div><dt class="inline text-slate-400">影响范围：</dt><dd class="inline font-medium text-slate-700">{{ review.demand?.impactScopeLabel || '待判断' }}</dd></div>
                  <div><dt class="inline text-slate-400">复杂度：</dt><dd class="inline font-medium text-slate-700">{{ review.demand?.complexityLevelLabel || '待判断' }}</dd></div>
                  <div v-if="review.demand?.expectedDeliveryTime"><dt class="inline text-slate-400">预计完成：</dt><dd class="inline font-medium text-slate-700">{{ review.demand.expectedDeliveryTime }}</dd></div>
                  <div><dt class="inline text-slate-400">AI / PoC：</dt><dd class="inline font-medium text-slate-700">{{ review.demand?.aiModeLabel || '不涉及 AI' }} · {{ review.demand?.pocRequirementLabel || '不需要 PoC' }}</dd></div>
                </dl>
                <p v-if="review.demand?.evaluationDecision" class="mt-3 whitespace-pre-wrap text-xs leading-6 text-blue-900"><span class="font-medium">初步结论：</span>{{ review.demand.evaluationDecisionLabel }}</p>
                <p v-if="review.demand?.evaluationReason" class="mt-1 whitespace-pre-wrap text-xs leading-6 text-slate-700"><span class="font-medium">判断说明：</span>{{ review.demand.evaluationReason }}</p>
                <p v-if="review.demand?.evaluationNotes" class="mt-1 whitespace-pre-wrap text-xs leading-6 text-slate-600"><span class="font-medium">范围 / 依赖：</span>{{ review.demand.evaluationNotes }}</p>
                <p v-if="!review.demand?.evaluationDecision && !review.demand?.evaluationReason && !review.demand?.evaluationNotes" class="mt-3 text-xs leading-5 text-slate-500">IT 尚未补充文字判断，请结合需求描述和上述初筛信息进行评估。</p>
              </div>
              <div v-if="review.demand?.l3Branches?.length" class="mt-5 border-t border-violet-100 pt-4">
                <div class="flex items-center justify-between gap-2"><p class="text-xs font-semibold text-violet-800">本次提报包含的独立 L3 工作项</p><span class="text-[10px] text-violet-500">一次提交，逐项判断</span></div>
                <p class="mt-1 text-[11px] leading-5 text-violet-700">业务只需针对每个独立工作项判断必要性和优先级；通用的需求背景与价值口径不重复填写。</p>
                <div class="mt-3 space-y-2">
                  <div v-for="branch in review.demand.l3Branches" :key="branch.id" class="rounded-lg border border-violet-100 bg-violet-50/40 p-3">
                    <div class="flex items-start justify-between gap-3"><div><p class="text-xs font-semibold text-violet-950">{{ branch.title }}</p><p class="mt-1 text-[10px] text-violet-600">{{ branch.itemKindLabel }} · {{ branch.relationToValueLabel }}</p></div><span v-if="branch.scope" class="max-w-[45%] text-right text-[10px] leading-4 text-violet-700">{{ branch.scope }}</span></div>
                    <div v-if="review.status !== 'submitted'" class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2"><label class="block"><span class="form-label">本 L3 业务判断 <span class="text-rose-500">*</span></span><select v-model="branchDecisionMap[branch.id].decision" class="feishu-input w-full"><option value="">请选择</option><option value="support">有必要实施</option><option value="adjust">有必要，但建议调整</option><option value="reject">暂无实施必要</option></select></label><label class="block"><span class="form-label">本 L3 优先级 <span class="text-rose-500">*</span></span><select v-model="branchDecisionMap[branch.id].prioritySuggestion" class="feishu-input w-full"><option value="">请选择</option><option value="P0">现在处理</option><option value="P1">近期处理</option><option value="P2">计划内处理</option><option value="P3">暂缓</option></select></label></div>
                    <p v-if="review.status === 'submitted' && branchDecisionMap[branch.id]?.decision" class="mt-2 text-xs text-violet-900">业务判断：{{ branchDecisionLabel(branchDecisionMap[branch.id].decision) }} · 优先级：{{ branchDecisionMap[branch.id].prioritySuggestion }}</p>
                    <label v-if="review.status !== 'submitted'" class="mt-2 block"><span class="form-label">本 L3 补充意见 <span class="font-normal text-gray-400">（可选）</span></span><textarea v-model="branchDecisionMap[branch.id].comment" rows="2" maxlength="5000" class="feishu-input w-full resize-y" placeholder="只写本独立 L3 的范围、时机或前置条件建议" /></label>
                    <p v-if="review.status === 'submitted' && branchDecisionMap[branch.id]?.comment" class="mt-1 whitespace-pre-wrap text-[11px] leading-5 text-violet-800">意见：{{ branchDecisionMap[branch.id].comment }}</p>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="review.status === 'submitted'" class="rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-3 text-xs leading-6 text-emerald-800">这张评估单已经提交过，无需重复填写。</div>
            <template v-else>
              <div class="rounded-lg border border-violet-100 bg-violet-50/50 px-3 py-2.5 text-xs leading-5 text-violet-800"><span class="font-medium">本次请重点判断：</span>{{ reviewHint }}</div>
              <label class="block"><span class="form-label">业务必要性 <span class="text-rose-500">*</span></span><select v-model="form.decision" class="feishu-input w-full"><option value="">请选择</option><option value="support">有必要实施</option><option value="adjust">有必要，但建议调整</option><option value="reject">暂无实施必要</option></select></label>
              <label class="block"><span class="form-label">优先级建议 <span class="text-rose-500">*</span></span><select v-model="form.prioritySuggestion" class="feishu-input w-full"><option value="">请选择</option><option value="P0">现在处理</option><option value="P1">近期处理</option><option value="P2">计划内处理</option><option value="P3">暂缓</option></select></label>
              <label class="block"><span class="form-label">评审意见 <span class="font-normal text-gray-400">（可选）</span></span><textarea v-model="form.comment" rows="4" maxlength="5000" class="feishu-input w-full resize-y" placeholder="如有需要，请补充为什么这样判断，或提出范围、时机、前置条件等建议" /></label>
              <div class="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-[11px] leading-5 text-gray-400">本次意见用于判断业务必要性和优先级，不等于立即承诺开发排期。</p><button type="button" class="feishu-btn-primary justify-center px-5" :disabled="saving || !canSubmit" @click="submit">{{ saving ? '提交中...' : '提交评估意见' }}</button></div>
            </template>
          </template>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useDemandReviewEntryPage } from "../features/demand-delivery/useDemandReviewEntryPage"
const { route, reviewId, reviewToken, currentUser, review, loading, saving, errorMessage, successMessage, form, branchDecisionMap, reviewHint, canSubmit, branchDecisionLabel, syncBranchDecisions, readUser, waitForDingTalkSdk, withTimeout, ensureAuth, submit } = useDemandReviewEntryPage()
</script>

<style scoped>
.form-label { display: block; margin-bottom: 0.35rem; font-size: 0.7rem; color: #6b7280; }
</style>
