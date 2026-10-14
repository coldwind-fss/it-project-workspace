<template>
  <section class="mb-5 rounded-xl border-2 border-blue-200 bg-slate-50 p-4 sm:p-5">
    <header class="flex items-start justify-between gap-3"><div><h2 class="text-base font-semibold text-slate-900">{{ deliveryOnly ? '交付与上线后运营' : '开发协作与交付' }}</h2><p class="mt-1 text-xs leading-5 text-slate-500">{{ deliveryOnly ? '交付记录、使用回访、整改和复盘会挂在同一条 L3 生命周期下。' : '资料往来 → 多轮验证 → IT 交付 → 使用回访。历史保留在同一条 L3 中。' }}</p></div><button class="shrink-0 text-xs text-blue-700" :disabled="busy" @click="load">刷新记录</button></header>
    <p v-if="error" role="alert" class="my-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">{{ error }}</p>
    <p v-if="notice" role="status" class="my-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{{ notice }}</p>
    <div v-if="data" class="mt-4 space-y-4">
      <div v-if="data.canEdit && !props.readOnly" class="rounded-xl border border-blue-300 bg-white p-4">
        <div v-if="!deliveryOnly" class="flex flex-wrap gap-2"><button v-for="(label, kind) in kinds" :key="kind" class="rounded-lg border px-3 py-2 text-sm" :class="mode === kind ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300 text-slate-700'" @click="start(String(kind))">{{ label }}</button><button class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700" :class="mode === 'delivery' ? 'border-blue-600 bg-blue-600 text-white' : ''" @click="start('delivery')">IT 交付 / 上线</button></div>
        <div v-else class="flex flex-wrap gap-2"><button class="rounded-lg border px-3 py-2 text-sm" :class="mode === 'delivery' ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300 text-slate-700'" @click="start('delivery')">记录交付 / 上线</button></div>
        <form v-if="mode && mode !== 'delivery'" class="mt-4 space-y-3" @submit.prevent="createLink">
          <div class="flex items-center justify-between text-xs text-slate-500"><span>{{ draft.collaborationId ? '继续原协作主题，新建一轮请求' : '发起新的协作主题' }}</span><button type="button" @click="mode = ''">收起</button></div>
          <label class="block text-xs text-slate-600">主题<input v-model="draft.title" class="feishu-input mt-1 w-full" maxlength="300" required /></label>
          <div class="grid gap-3 sm:grid-cols-2"><label class="block text-xs text-slate-600">业务回复人<input v-model="draft.recipientName" class="feishu-input mt-1 w-full" maxlength="120" required /></label><label class="block text-xs text-slate-600">链接有效天数<input v-model.number="draft.validDays" class="feishu-input mt-1 w-full" type="number" min="1" max="90" required /></label></div>
          <label class="block text-xs text-slate-600">{{ mode === 'materials' ? '请业务补充什么资料' : mode === 'baseline' ? '请业务确认的交付安排' : '本轮完成内容与验证方式' }}<textarea v-model="draft.content" rows="4" maxlength="10000" class="feishu-input mt-1 w-full resize-y" required /></label>
          <div v-if="mode !== 'materials'" class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs leading-5"><p class="font-semibold">将使用当前 L3 的范围和验收标准</p><p class="mt-1 whitespace-pre-wrap">{{ requirement.acceptanceCriteria || '尚未填写验收标准，请先编辑 L3 补充。' }}</p><p class="mt-2 text-slate-500">业务可直接确认或提出修改，无需重复填表。范围确认按需发起。</p></div>
          <details v-if="data.attachments.length" class="rounded-lg border border-slate-200 p-3"><summary class="cursor-pointer text-xs text-slate-600">选择分享材料（已选 {{ draft.attachmentIds.length }} 个）</summary><label v-for="attachment in data.attachments" :key="attachment.id" class="mt-2 flex items-center gap-2 text-xs"><input v-model="draft.attachmentIds" type="checkbox" :value="attachment.id" />{{ attachment.originalName }}</label></details>
          <p class="text-xs text-slate-500">仅分享勾选的附件；新文件可先在下方共享动态中上传，再刷新记录。</p>
          <button type="submit" class="feishu-btn-primary" :disabled="busy">{{ busy ? '生成中…' : '生成业务链接' }}</button>
        </form>
        <form v-if="mode === 'delivery'" class="mt-4 space-y-3" @submit.prevent="deliver">
          <label class="block text-xs text-slate-600">业务验证依据<select v-model="delivery.acceptanceRequestId" class="feishu-input mt-1 w-full"><option value="">本次无需业务验证，填写交付依据</option><option v-for="round in passedRounds" :key="round.id" :value="round.id">{{ round.snapshot.title }} · {{ round.submittedAt }}</option></select></label>
          <label v-if="!delivery.acceptanceRequestId" class="block text-xs text-slate-600">本次无需验证的原因 / 交付依据<textarea v-model="delivery.verificationExemption" rows="2" maxlength="2000" class="feishu-input mt-1 w-full" required /></label>
          <div class="grid gap-3 sm:grid-cols-2"><label class="block text-xs text-slate-600">交付形式<select v-model="delivery.deliveryKind" class="feishu-input mt-1 w-full"><option>上线</option><option>已交付</option><option>试运行</option></select></label><label class="block text-xs text-slate-600">业务联系人<input v-model="delivery.businessOwnerName" class="feishu-input mt-1 w-full" maxlength="120" /></label><label class="block text-xs text-slate-600">交付日期<input v-model="delivery.deliveryDate" type="date" class="feishu-input mt-1 w-full" required /></label><label class="block text-xs text-slate-600">开始使用日期<input v-model="delivery.useStartDate" type="date" class="feishu-input mt-1 w-full" required /></label></div>
          <label class="block text-xs text-slate-600">交付说明<textarea v-model="delivery.notes" rows="2" class="feishu-input mt-1 w-full" maxlength="5000" /></label>
          <p class="text-xs leading-5 text-slate-500">完成后 L3 标记为已交付，并按使用开始日期安排 3 天回执和 30 天复盘。联系人可稍后在运营详情补充。</p>
          <button type="submit" class="feishu-btn-primary" :disabled="busy">{{ busy ? '保存中…' : '完成本轮交付并建立回访' }}</button>
        </form>
      </div>
      <section v-if="!deliveryOnly" class="rounded-xl border border-slate-300 bg-white p-4">
        <h3 class="text-sm font-semibold">协作往来与验证历史 <span class="text-slate-400">{{ data.links.length }}</span></h3>
        <p v-if="!data.links.length" class="mt-3 text-xs text-slate-500">尚未发起业务链接。已有开发和业务讨论仍在下方共享动态中。</p>
        <div class="mt-3 max-h-[32rem] space-y-3 overflow-y-auto pr-1">
          <article v-for="round in data.links" :key="round.id" class="rounded-lg border border-slate-200 p-3">
            <div class="flex flex-wrap items-center justify-between gap-2"><h4 class="text-sm font-semibold">{{ round.snapshot.title }}</h4><span class="rounded bg-blue-50 px-2 py-1 text-xs text-blue-800">{{ round.kindLabel }} · {{ round.status === 'submitted' ? round.outcomeLabel : statusLabels[round.status] }}</span></div>
            <p class="mt-2 text-xs text-slate-500">{{ round.createdAt }} · {{ round.snapshot.recipientName }}</p><p class="mt-2 whitespace-pre-wrap text-sm leading-6">{{ round.snapshot.content }}</p>
            <details class="mt-2 text-xs"><summary class="cursor-pointer text-blue-700">查看本轮范围、标准及材料</summary><p class="mt-2 whitespace-pre-wrap leading-5">{{ round.snapshot.description }}</p><p class="mt-2 whitespace-pre-wrap leading-5">验收标准：{{ round.snapshot.acceptanceCriteria || '资料补充' }}</p><button v-for="attachment in round.snapshot.attachments" :key="attachment.id" class="mt-2 block text-blue-700 underline" @click="download(attachment)">{{ attachment.originalName }}</button></details>
            <div v-if="round.response" class="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3"><p class="text-xs text-slate-500">业务回复 · {{ round.submittedAt }}</p><p class="mt-1 whitespace-pre-wrap text-sm leading-6">{{ round.response.content }}</p><button v-for="attachment in round.response.attachments" :key="attachment.id" class="mt-2 block text-xs text-blue-700 underline" @click="download(attachment)">{{ attachment.originalName }}</button></div>
            <div v-if="round.feedback" class="mt-3 rounded-lg border border-orange-200 bg-orange-50 p-3 text-xs leading-5 text-orange-900"><p class="font-semibold">反馈分流：{{ round.feedback.feedbackTypeLabel }}</p><p class="mt-1">处理结果：{{ round.feedback.routeTypeLabel }}</p><router-link v-if="round.feedback.routedRequirementId && round.feedback.routedRequirementId !== requirement.id" :to="'/requirements/' + round.feedback.routedRequirementId" class="mt-1 inline-block text-blue-700 underline">打开关联的新 L3 →</router-link></div>
            <div v-if="data.canEdit && !props.readOnly" class="mt-3 flex flex-wrap gap-4 text-xs"><button v-if="round.link" class="text-blue-700" @click="copy(round.link)">复制业务链接</button><button v-if="round.status === 'pending'" class="text-slate-500" :disabled="busy" @click="revoke(round)">撤销链接</button><button class="text-blue-700" :disabled="busy" @click="start(round.kind, round)">发起下一轮</button></div>
          </article>
        </div>
      </section>
      <section v-if="data.operations.length" class="rounded-xl border border-emerald-300 bg-white p-4"><h3 class="text-sm font-semibold">交付、回访与整改</h3><details v-for="operation in data.operations" :key="operation.id" class="mt-3 rounded-lg border border-slate-200 p-3"><summary class="cursor-pointer text-sm">{{ operation.deliveryDate }} · {{ operation.deliveryKind }} · {{ operation.acceptanceRequestId ? '业务已验证' : operation.verificationExemption ? 'IT 已记录交付依据' : '历史状态交付' }}</summary><p class="mt-2 text-xs leading-5">{{ operation.notes }} {{ operation.verificationExemption }}</p><div v-for="receipt in operation.outcomeRequests" :key="receipt.id" class="mt-3 border-t pt-2 text-xs"><p>{{ receipt.stageLabel }} · {{ receipt.statusLabel }} · {{ receipt.scheduledAt }}</p><p v-if="receipt.responseSnapshot?.summary" class="mt-1 whitespace-pre-wrap leading-5">{{ receipt.responseSnapshot.summary }}</p></div><p v-for="issue in operation.issues" :key="issue.id" class="mt-2 text-xs text-amber-800">整改：{{ issue.title }} · {{ issue.status }}</p><p v-for="knowledge in operation.knowledge" :key="knowledge.id" class="mt-2 text-xs">复盘 / 知识：{{ knowledge.title }}</p><router-link :to="'/postlaunch/operations?operationId=' + operation.id" class="mt-3 inline-block text-xs text-blue-700">进入本轮运营详情 →</router-link></details></section>
      <details v-if="data.sources.length" class="rounded-xl border border-slate-300 bg-white p-4"><summary class="cursor-pointer text-sm font-semibold">需求来源与评估证据</summary><article v-for="source in data.sources" :key="source.id" class="mt-4 space-y-2 text-xs leading-5"><h4 class="font-semibold">{{ source.title }} · {{ source.requesterName }}</h4><p class="whitespace-pre-wrap">{{ source.description }}</p><p>IT 判断：{{ source.evaluationReason }} {{ source.evaluationNotes }}</p><p v-for="review in source.reviews" :key="review.reviewerName + review.submittedAt">业务评估：{{ review.reviewerName }} · {{ review.decision }} · {{ review.prioritySuggestion }} {{ review.comment }}</p><p v-for="poc in source.pocs" :key="poc.id" class="whitespace-pre-wrap">PoC：{{ poc.result || poc.goal }} · {{ poc.conclusion }}</p><button v-for="attachment in source.attachments" :key="attachment.id" class="block text-blue-700 underline" @click="download(attachment)">{{ attachment.originalName }}</button></article></details>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api } from '../api/application-api'
const props = withDefaults(defineProps<{ requirement: any; revision?: number; deliveryOnly?: boolean; readOnly?: boolean }>(), { deliveryOnly: false, readOnly: false })
const emit = defineEmits<{ changed: [] }>()
const data = ref<any>(null), mode = ref(''), busy = ref(false), error = ref(''), notice = ref('')
const deliveryOnly = computed(() => props.deliveryOnly)
const kinds: Record<string, string> = { materials: '资料请求', baseline: '范围确认（按需）', verification: '业务验证' }
const statusLabels: Record<string, string> = { pending: '待回复', revoked: '已撤销', expired: '已过期' }
const draft = ref<any>({}), delivery = ref<any>({})
const passedRounds = computed(() => (data.value?.links || []).filter((r: any) => r.kind === 'verification' && r.outcome === 'passed' && !data.value.operations.some((o: any) => o.acceptanceRequestId === r.id)))
function today() { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}` }
function start(kind: string, previous?: any) {
  if (busy.value) return
  mode.value = kind; error.value = ''; notice.value = ''
  draft.value = { clientKey: crypto.randomUUID(), kind, title: previous?.snapshot.title || (kinds[kind] || '') + '：' + props.requirement.title, content: '', recipientName: previous?.snapshot.recipientName || props.requirement.requester || '', validDays: 14, collaborationId: previous?.collaborationId || '', attachmentIds: [] }
  delivery.value = { clientKey: crypto.randomUUID(), acceptanceRequestId: passedRounds.value[0]?.id || '', verificationExemption: '', deliveryKind: '上线', deliveryDate: today(), useStartDate: today(), businessOwnerName: props.requirement.requester || '', notes: '' }
}
let sequence = 0
async function load() {
  const current = ++sequence
  try { const result = await api.getRequirementLifecycle(props.requirement.id); if (current === sequence) data.value = result }
  catch (e: any) { if (current === sequence) error.value = e.message }
}
async function createLink() {
  if (busy.value) return
  busy.value = true; error.value = ''
  try { await api.createCollaborationLink(props.requirement.id, draft.value); mode.value = ''; await load(); emit('changed'); notice.value = '业务链接已生成，并按接收人配置发送了通知；下方仍可复制链接转交业务回复人。' }
  catch (e: any) { error.value = e.message }
  finally { busy.value = false }
}
async function deliver() {
  if (busy.value) return
  busy.value = true; error.value = ''
  try { await api.deliverRequirement(props.requirement.id, delivery.value); mode.value = ''; await load(); emit('changed'); notice.value = '本轮交付已保存，回访记录已关联。' }
  catch (e: any) { error.value = e.message }
  finally { busy.value = false }
}
async function revoke(round: any) {
  busy.value = true; error.value = ''
  try { await api.revokeCollaborationLink(round.id); await load(); emit('changed') } catch (e: any) { error.value = e.message }
  finally { busy.value = false }
}
async function copy(link: string) { try { await navigator.clipboard.writeText(link); notice.value = '业务链接已复制' } catch { notice.value = link } }
async function download(attachment: any) {
  const blob = await api.getBusinessAttachmentBlob(attachment.id)
  if (!blob) { error.value = '附件读取失败'; return }
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = attachment.originalName; a.click(); setTimeout(() => URL.revokeObjectURL(url), 30000)
}
watch(() => [props.requirement.id, props.revision], load, { immediate: true })
</script>
