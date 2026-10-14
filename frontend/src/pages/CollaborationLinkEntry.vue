<template>
  <main class="h-screen overflow-y-auto bg-slate-50 px-4 py-8">
    <div class="mx-auto max-w-2xl space-y-5">
      <header><p class="text-sm font-semibold text-blue-700">IT 项目协作空间 · 业务回复</p><h1 class="mt-2 text-2xl font-semibold text-slate-900">{{ copy.title }}</h1><p class="mt-2 text-sm text-slate-500">{{ copy.intro }}</p></header>
      <p v-if="loading" class="rounded-xl border bg-white p-8 text-center text-slate-500">正在读取本次请求…</p>
      <p v-if="error" role="alert" class="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">{{ error }}</p>
      <template v-if="context">
        <section class="rounded-xl border border-slate-300 bg-white p-5 space-y-4">
          <div><p class="text-xs text-slate-500">需求：{{ context.snapshot.requirementTitle }}</p><h2 class="mt-2 text-lg font-semibold">{{ context.snapshot.title }}</h2><p class="mt-1 text-xs text-slate-500">回复人：{{ context.snapshot.recipientName }} · 有效至 {{ context.expiresAt }}</p></div>
          <div class="rounded-lg bg-slate-50 p-4"><p class="text-xs font-semibold text-slate-600">开发人员的请求</p><p class="mt-2 whitespace-pre-wrap text-sm leading-6">{{ context.snapshot.content }}</p></div>
          <section v-if="copy.showCriteria" class="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <h2 class="text-sm font-semibold text-blue-900">{{ copy.criteriaTitle }}</h2>
            <template v-if="context.snapshot.deliveryBaseline">
              <p class="mt-3 text-xs text-slate-500">交付标准版本</p><p class="text-sm leading-6">{{ context.snapshot.deliveryBaseline.versionLabel }} · {{ context.snapshot.deliveryBaseline.templateLabel }}</p>
              <p class="mt-3 text-xs text-slate-500">本次交付范围</p><p class="whitespace-pre-wrap text-sm leading-6">{{ context.snapshot.deliveryBaseline.content?.scope }}</p>
              <p class="mt-3 text-xs text-slate-500">业务验证场景</p><p class="whitespace-pre-wrap text-sm leading-6">{{ context.snapshot.deliveryBaseline.content?.scenarios }}</p>
              <p class="mt-3 text-xs text-slate-500">功能验收通过标准</p><p class="whitespace-pre-wrap text-sm leading-6">{{ context.snapshot.deliveryBaseline.content?.expected }}</p>
              <details class="mt-3"><summary class="cursor-pointer text-xs text-blue-700">查看其他验收项</summary><div class="mt-2 space-y-2 text-sm leading-6"><p v-if="context.snapshot.deliveryBaseline.content?.evidence"><span class="text-xs text-slate-500">验证证据：</span>{{ context.snapshot.deliveryBaseline.content.evidence }}</p><p v-if="context.snapshot.deliveryBaseline.content?.exclusions"><span class="text-xs text-slate-500">不在本次范围：</span>{{ context.snapshot.deliveryBaseline.content.exclusions }}</p></div></details>
            </template>
            <template v-else>
              <p class="mt-3 text-xs text-slate-500">本轮交付说明</p><p class="whitespace-pre-wrap text-sm leading-6">{{ context.snapshot.description || '见本轮说明' }}</p>
              <p class="mt-3 text-xs text-slate-500">合格标准</p><p class="whitespace-pre-wrap text-sm leading-6">{{ context.snapshot.acceptanceCriteria || '请按本轮说明确认' }}</p>
            </template>
          </section>
          <div v-if="context.snapshot.attachments?.length"><p class="text-xs font-semibold text-slate-600">相关材料</p><button v-for="attachment in context.snapshot.attachments" :key="attachment.id" class="mt-2 block text-left text-sm text-blue-700 underline" @click="download(attachment)">{{ attachment.originalName }}</button></div>
        </section>
        <section v-if="context.status === 'submitted'" class="rounded-xl border border-emerald-300 bg-white p-5">
          <h2 class="font-semibold text-emerald-700">{{ copy.submittedTitle }} · {{ context.outcomeLabel }}</h2><p class="mt-2 text-xs text-slate-500">{{ context.submittedAt }}</p><p class="mt-3 whitespace-pre-wrap text-sm leading-6">{{ context.response?.content }}</p>
          <button v-for="attachment in context.response?.attachments || []" :key="attachment.id" class="mt-2 block text-sm text-blue-700 underline" @click="download(attachment)">{{ attachment.originalName }}</button>
          <p class="mt-4 text-sm text-slate-500">本轮内容已回填到需求协作记录。</p>
        </section>
        <form v-else class="rounded-xl border border-blue-300 bg-white p-5 space-y-4" @submit.prevent="submit">
          <fieldset v-if="context.kind !== 'materials'"><legend class="mb-3 text-sm font-semibold">{{ copy.choiceTitle }}</legend><label v-for="choice in choices" :key="choice.value" class="mb-2 flex cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm" :class="outcome === choice.value ? 'border-blue-400 bg-blue-50' : 'border-slate-300'"><input v-model="outcome" type="radio" name="outcome" :value="choice.value" required />{{ choice.label }}</label></fieldset>
          <section v-if="context.kind === 'verification' && outcome === 'changes'" class="rounded-lg border border-orange-200 bg-orange-50 p-4 space-y-3">
            <div><p class="text-sm font-semibold text-orange-900">请标记需要修改的类型</p><p class="mt-1 text-xs leading-5 text-orange-800">这只用于帮助 IT 判断后续处理方式，不影响你填写具体问题。</p></div>
            <label class="block text-sm font-semibold text-slate-700">修改类型<select v-model="feedbackType" class="feishu-input mt-2 w-full font-normal" required><option value="" disabled>请选择修改类型</option><option v-for="item in feedbackTypeChoices" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
            <label v-if="feedbackType === 'new_feature' || feedbackType === 'requirement_change'" class="block text-sm font-semibold text-slate-700">新事项标题<span class="font-normal text-slate-500">（便于 IT 建立后续 L3）</span><input v-model="requestedTitle" maxlength="180" class="feishu-input mt-2 w-full font-normal" placeholder="例如：增加结果订阅和定时推送" /></label>
          </section>
          <label class="block text-sm font-semibold">{{ copy.responseLabel }}<textarea v-model="content" rows="5" maxlength="10000" class="feishu-input mt-2 w-full resize-y font-normal" :placeholder="copy.responsePlaceholder" /></label>
          <AttachmentPicker :files="files" @add="addFiles" @remove="removeFile" />
          <p v-if="context.draftAttachments.length" class="text-xs text-slate-500">已上传待提交：{{ context.draftAttachments.map((a: any) => a.originalName).join('、') }}</p>
          <p class="text-xs text-slate-500">{{ copy.attachmentHint }}</p>
          <button type="submit" class="feishu-btn-primary w-full justify-center" :disabled="saving">{{ saving ? '正在提交…' : copy.submitLabel }}</button>
        </form>
      </template>
    </div>
  </main>
</template>

<script setup lang="ts">
import AttachmentPicker from '../components/AttachmentPicker.vue'
import { useCollaborationLinkEntryPage } from "../features/demand-delivery/useCollaborationLinkEntryPage"
const { token, context, loading, saving, error, outcome, content, feedbackType, requestedTitle, files, uploadKeys, uploaded, copy, choices, feedbackTypeChoices, addFiles, removeFile, submit, download } = useCollaborationLinkEntryPage()
</script>
