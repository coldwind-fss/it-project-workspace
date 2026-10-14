<template>
  <main class="min-h-full overflow-y-auto bg-slate-50 px-4 py-5 sm:px-6 sm:py-8">
    <div class="mx-auto w-full max-w-2xl">
      <div class="mb-5 flex items-center gap-3"><div class="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500 text-lg font-bold text-white shadow-sm">补</div><div><p class="text-sm font-semibold text-gray-900">业务信息补充</p><p class="text-[11px] text-gray-500">只需回答与该类需求相关的几个问题</p></div></div>
      <section v-if="successMessage" class="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm sm:p-8"><div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-2xl text-emerald-600">✓</div><h1 class="mt-4 text-center text-lg font-semibold text-gray-900">{{ successMessage }}</h1><p class="mt-2 text-center text-sm leading-6 text-gray-500">信息已提交给 IT，后续会进入综合评估。</p></section>
      <section v-else class="overflow-hidden rounded-2xl border border-amber-100 bg-white shadow-sm">
        <div class="border-b border-amber-100 bg-gradient-to-r from-amber-50 via-white to-orange-50 px-5 py-5 sm:px-7"><p class="text-xs font-semibold text-amber-600">需求池补充单</p><h1 class="mt-1 text-lg font-semibold text-gray-900">请补充业务信息</h1><p class="mt-2 text-xs leading-5 text-gray-500">问题会根据需求类型自动生成，填写完成后即可提交。</p></div>
        <div class="space-y-5 px-5 py-5 sm:px-7 sm:py-6"><div v-if="errorMessage" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2.5 text-xs leading-5 text-amber-700">{{ errorMessage }}</div><div v-if="loading" class="py-10 text-center text-sm text-gray-400">正在读取补充单...</div><template v-else-if="supplement"><div class="rounded-xl border border-gray-100 bg-gray-50/70 px-4 py-3"><p class="text-sm font-semibold text-gray-900">{{ supplement.demand?.title }}</p><p class="mt-1 text-[11px] leading-5 text-gray-500">{{ supplement.demand?.department || '未填写部门' }} · 接收人：{{ supplement.recipientName || '-' }}</p><p class="mt-3 whitespace-pre-wrap rounded-lg bg-white px-3 py-2 text-xs leading-6 text-gray-600">{{ supplement.demand?.description }}</p></div><div v-if="supplement.status === 'submitted'" class="rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-3 text-xs leading-6 text-emerald-800">这张补充单已经提交过，无需重复填写。</div><template v-else><div v-for="question in supplement.questions" :key="question.key"><label class="form-label">{{ question.label }} <span v-if="question.required" class="text-rose-500">*</span></label><textarea v-if="question.type === 'textarea'" v-model="answers[question.key]" rows="3" maxlength="5000" class="feishu-input w-full resize-y" /><input v-else v-model="answers[question.key]" maxlength="5000" class="feishu-input w-full" /></div><div class="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-[11px] leading-5 text-gray-400">提交后 IT 会继续综合评估。</p><button type="button" class="feishu-btn-primary justify-center px-5" :disabled="saving || !canSubmit" @click="submit">{{ saving ? '提交中...' : '提交补充信息' }}</button></div></template></template></div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useDemandSupplementEntryPage } from "../features/demand-delivery/useDemandSupplementEntryPage"
const { route, supplementId, currentUser, supplement, answers, loading, saving, errorMessage, successMessage, canSubmit, readUser, waitForDingTalkSdk, ensureAuth, submit } = useDemandSupplementEntryPage()
</script>

<style scoped>
.form-label { display: block; margin-bottom: 0.35rem; font-size: 0.7rem; color: #6b7280; }
</style>
