<template>
  <section class="rounded-xl border-2 border-emerald-200 bg-emerald-50/30 p-4 sm:p-5">
    <header class="flex items-start justify-between gap-3">
      <div>
        <h2 class="flex items-center gap-2 text-base font-semibold text-slate-900"><span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">✓</span>上线前交付标准</h2>
        <p class="mt-1 text-xs leading-5 text-slate-500">IT 先写清本次交付如何验收，业务只需通过免登录链接确认或提出修改。</p>
      </div>
      <button type="button" class="shrink-0 text-xs text-emerald-700" :disabled="loading || saving" @click="load">刷新</button>
    </header>

    <p v-if="error" role="alert" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">{{ error }}</p>
    <p v-if="notice" role="status" class="mt-3 rounded-lg border border-emerald-200 bg-white px-3 py-2 text-xs text-emerald-800">{{ notice }}</p>

    <div v-if="latest" class="mt-4 rounded-xl border border-emerald-200 bg-white p-4">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div><span class="font-semibold text-sm text-slate-900">{{ latest.versionLabel }} · {{ latest.templateLabel }}</span><span class="ml-2 rounded bg-emerald-50 px-2 py-1 text-[10px] text-emerald-700">{{ latest.statusLabel }}</span></div>
        <span class="text-[11px] text-slate-400">{{ latest.createdAt }}</span>
      </div>
      <div class="mt-3 grid gap-3 text-xs leading-5 sm:grid-cols-2">
        <div><p class="text-[10px] text-slate-400">本次交付范围</p><p class="whitespace-pre-wrap text-slate-700">{{ latest.content?.scope }}</p></div>
        <div><p class="text-[10px] text-slate-400">业务验证场景</p><p class="whitespace-pre-wrap text-slate-700">{{ latest.content?.scenarios }}</p></div>
        <div><p class="text-[10px] text-slate-400">功能验收通过标准</p><p class="whitespace-pre-wrap text-slate-700">{{ latest.content?.expected }}</p></div>
        <div><p class="text-[10px] text-slate-400">验证证据</p><p class="whitespace-pre-wrap text-slate-700">{{ latest.content?.evidence || '由业务截图、数据或操作结果确认' }}</p></div>
      </div>
      <details class="mt-3 text-xs"><summary class="cursor-pointer text-emerald-700">查看类型专项标准</summary><div class="mt-2 grid gap-2 sm:grid-cols-2"><div v-for="field in templateFields" :key="field.key"><p class="text-[10px] text-slate-400">{{ field.label }}</p><p class="whitespace-pre-wrap text-slate-700">{{ latest.content?.[field.key] || '未填写' }}</p></div></div></details>
    </div>
    <p v-else class="mt-4 rounded-lg border border-dashed border-emerald-200 bg-white px-3 py-5 text-center text-xs text-slate-500">尚未建立上线前交付标准。完成后再发给业务确认。</p>

    <div v-if="canEdit" class="mt-4 rounded-xl border border-emerald-200 bg-white p-4">
      <div class="flex flex-wrap items-center justify-between gap-2"><h3 class="text-sm font-semibold text-slate-800">{{ latest ? '创建下一版交付标准' : '建立第一版交付标准' }}</h3><span class="text-[11px] text-slate-400">{{ templateLabel }}</span></div>
      <div class="mt-3 grid gap-3">
        <label class="block text-xs text-slate-600">本次交付范围 <span class="text-rose-500">*</span><textarea v-model="draft.scope" rows="2" class="feishu-input mt-1 w-full resize-y text-xs" placeholder="只写本次 L3 实际交付的边界，不要重复业务原始需求" /></label>
        <label class="block text-xs text-slate-600">业务验证场景 <span class="text-rose-500">*</span><textarea v-model="draft.scenarios" rows="2" class="feishu-input mt-1 w-full resize-y text-xs" placeholder="业务人员按什么关键路径验证，覆盖哪些典型场景" /></label>
        <label class="block text-xs text-slate-600">功能验收通过标准 <span class="text-rose-500">*</span><textarea v-model="draft.expected" rows="2" class="feishu-input mt-1 w-full resize-y text-xs" placeholder="上线时必须看到什么功能结果，什么情况算通过" /></label>
        <div class="grid gap-3 sm:grid-cols-2">
          <label class="block text-xs text-slate-600">验证证据<textarea v-model="draft.evidence" rows="2" class="feishu-input mt-1 w-full resize-y text-xs" placeholder="截图、数据结果、流程记录或附件" /></label>
          <label class="block text-xs text-slate-600">不在本次范围<textarea v-model="draft.exclusions" rows="2" class="feishu-input mt-1 w-full resize-y text-xs" placeholder="明确本次不交付的内容" /></label>
        </div>
        <div class="grid gap-3 sm:grid-cols-2">
          <label class="block text-xs text-slate-600">业务确认人<input v-model="recipientName" class="feishu-input mt-1 w-full text-xs" maxlength="120" /></label>
          <label class="block text-xs text-slate-600">链接有效天数<input v-model.number="validDays" class="feishu-input mt-1 w-full text-xs" type="number" min="1" max="90" /></label>
        </div>
        <details class="rounded-lg border border-slate-200 px-3 py-2"><summary class="cursor-pointer text-xs font-medium text-slate-600">补充 {{ templateLabel }}专项验收项</summary><div class="mt-3 grid gap-3 sm:grid-cols-2"><label v-for="field in templateFields" :key="field.key" class="block text-xs text-slate-600">{{ field.label }}<textarea v-model="draft[field.key]" rows="2" class="feishu-input mt-1 w-full resize-y text-xs" :placeholder="field.placeholder" /></label></div></details>
      </div>
      <div class="mt-3 flex flex-wrap justify-end gap-2"><button v-if="latest?.status === 'confirmed'" type="button" class="feishu-btn-ghost text-xs" :disabled="saving" @click="sendVerification">发起业务验证</button><button type="button" class="feishu-btn-ghost text-xs" :disabled="saving" @click="save(false)">保存草稿</button><button type="button" class="feishu-btn-primary text-xs" :disabled="saving" @click="save(true)">{{ saving ? '处理中…' : '保存并发给业务确认' }}</button></div>
    </div>

    <details v-if="items.length > 1" class="mt-4 rounded-lg border border-slate-200 bg-white px-3 py-2"><summary class="cursor-pointer text-xs font-medium text-slate-600">查看历史版本（{{ items.length }}）</summary><div class="mt-2 space-y-2"><div v-for="item in items.slice(1)" :key="item.id" class="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-100 px-2 py-2 text-xs"><span>{{ item.versionLabel }} · {{ item.statusLabel }}</span><span class="text-slate-400">{{ item.createdAt }}</span></div></div></details>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api } from '../api/application-api'
import { deliveryStandardFields, normalizeDeliveryStandardType } from '../shared/deliveryStandards'

const props = defineProps<{ requirement: any }>()
const data = ref<any>({ items: [], canEdit: false, templateType: 'custom', templateLabel: '通用交付标准' })
const loading = ref(false), saving = ref(false), error = ref(''), notice = ref('')
const draft = ref<any>({ scope: '', scenarios: '', expected: '', evidence: '', exclusions: '' })
const recipientName = ref(''), validDays = ref(14)
const templateLabel = computed(() => data.value.templateLabel || '通用交付标准')
const items = computed(() => data.value.items || [])
const latest = computed(() => items.value[0] || null)
const canEdit = computed(() => !!data.value.canEdit)
const templateFields = computed(() => deliveryStandardFields(normalizeDeliveryStandardType(data.value.templateType)))
function resetDraft() {
  const source = latest.value?.content || {}
  const next: any = { scope: source.scope || '', scenarios: source.scenarios || '', expected: source.expected || '', evidence: source.evidence || '', exclusions: source.exclusions || '' }
  for (const field of templateFields.value) next[field.key] = source[field.key] || ''
  draft.value = next
  recipientName.value = latest.value?.recipientName || props.requirement.requester || ''
}
async function load() {
  loading.value = true; error.value = ''
  try { const result: any = await api.getDeliveryBaselines(props.requirement.id); if (result) { data.value = result; resetDraft() } }
  catch (e: any) { error.value = e?.message || '交付标准读取失败' }
  finally { loading.value = false }
}
async function save(send: boolean) {
  if (saving.value) return
  saving.value = true; error.value = ''; notice.value = ''
  try {
    const result: any = await api.createDeliveryBaseline(props.requirement.id, { templateType: data.value.templateType, content: draft.value, recipientName: recipientName.value, validDays: validDays.value, send })
    if (!result) throw new Error('交付标准保存失败')
    notice.value = send ? `${result.versionLabel} 已生成并发送业务确认链接` : `${result.versionLabel} 已保存为草稿`
    await load()
    if (result.link) { try { await navigator.clipboard.writeText(result.link); notice.value += '，链接已复制' } catch {} }
  } catch (e: any) { error.value = e?.message || '交付标准保存失败' }
  finally { saving.value = false }
}
async function sendVerification() {
  if (!latest.value || latest.value.status !== 'confirmed' || saving.value) return
  saving.value = true; error.value = ''; notice.value = ''
  const content = `请按 ${latest.value.versionLabel} 交付标准完成验证。\n交付范围：${latest.value.content?.scope || ''}\n验证场景：${latest.value.content?.scenarios || ''}\n预期结果：${latest.value.content?.expected || ''}`
  try {
    const result: any = await api.createCollaborationLink(props.requirement.id, { clientKey: crypto.randomUUID(), kind: 'verification', title: `业务验证：${props.requirement.title}`, content, recipientName: latest.value.recipientName || props.requirement.requester || '', validDays: validDays.value, attachmentIds: [], baselineId: latest.value.id })
    if (!result) throw new Error('业务验证链接生成失败')
    notice.value = '业务验证链接已发送，业务回复会回到下方共享动态'
    if (result.link) { try { await navigator.clipboard.writeText(result.link); notice.value += '，链接已复制' } catch {} }
  } catch (e: any) { error.value = e?.message || '业务验证链接生成失败' }
  finally { saving.value = false }
}
watch(() => props.requirement.id, load, { immediate: true })
</script>
