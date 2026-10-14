<template>
  <section class="collaboration-panel mt-6 overflow-hidden rounded-xl border border-violet-100 bg-white shadow-sm" @paste.stop="handlePaste('active', $event)">
    <div class="border-b border-violet-100 bg-gradient-to-r from-violet-50 via-white to-blue-50 px-5 py-4">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div class="flex items-start gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-600 text-white shadow-sm">
            <MessagesSquare class="h-5 w-5" />
          </div>
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="text-base font-semibold text-gray-900">业务协作</h3>
              <span class="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-semibold text-violet-700">围绕当前 L3</span>
            </div>
            <p class="mt-1 text-xs leading-5 text-gray-500">业务与 IT 在这里持续沟通、补充资料、反馈问题和完成验收。</p>
          </div>
        </div>
        <div class="flex items-center gap-2 text-[11px] text-gray-500">
          <span class="rounded-full bg-white px-2.5 py-1 shadow-sm">{{ threads.length }} 个协作主题</span>
          <span class="rounded-full bg-white px-2.5 py-1 shadow-sm">{{ openCount }} 项进行中</span>
        </div>
      </div>
      <div class="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-violet-100 bg-white/80 px-3 py-2.5">
        <p class="text-xs text-gray-500">把每个问题拆成一个主题，沟通、截图和交付结果都会跟着当前 L3 留存。</p>
        <button v-if="isAuthenticated" type="button" class="inline-flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-violet-700" @click="newThreadOpen = !newThreadOpen">
          <Plus class="h-3.5 w-3.5" /> {{ newThreadOpen ? '收起发起区' : '发起协作主题' }}
        </button>
        <span v-else class="text-[11px] text-amber-600">请在钉钉内登录后参与协作</span>
      </div>
    </div>

    <div v-if="newThreadOpen" class="border-b border-violet-100 bg-violet-50/40 px-5 py-4">
      <div class="mb-3 flex items-center justify-between">
        <div>
          <h4 class="text-sm font-semibold text-gray-900">发起一个新的协作主题</h4>
          <p class="mt-1 text-[11px] text-gray-500">例如“请提供测试数据”“确认发票规则”或“反馈上线后的问题”。</p>
        </div>
        <button type="button" class="text-lg text-gray-400 hover:text-gray-700" @click="newThreadOpen = false">×</button>
      </div>
      <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
        <label class="block">
          <span class="form-label">协作事项</span>
          <select v-model="newThread.kind" class="feishu-input w-full">
            <option v-for="item in kindOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
          </select>
        </label>
        <label class="block">
          <span class="form-label">协作对象 <span class="font-normal text-gray-400">（可留空自动匹配）</span></span>
          <input v-model="newThread.recipientName" class="feishu-input w-full" placeholder="例如：业务负责人或 IT 负责人" />
        </label>
        <label class="block md:col-span-2">
          <span class="form-label">主题标题</span>
          <input v-model="newThread.title" maxlength="300" class="feishu-input w-full" placeholder="例如：请确认发票金额取整规则" />
        </label>
        <label class="block md:col-span-2">
          <span class="form-label">第一条消息</span>
          <textarea v-model="newThread.content" rows="4" maxlength="10000" class="feishu-input w-full resize-y" placeholder="说明需要对方提供什么、确认什么或反馈什么问题；也可以直接粘贴图片" @paste.stop="handlePaste('new', $event)" />
        </label>
      </div>
      <AttachmentPicker :files="newFiles" @add="addFiles('new', $event)" @remove="removeFile('new', $event)" />
      <div class="mt-3 flex justify-end gap-2">
        <button type="button" class="feishu-btn-ghost text-xs" @click="newThreadOpen = false">取消</button>
        <button type="button" class="feishu-btn-primary text-xs" :disabled="saving === 'new'" @click="createThread">{{ saving === 'new' ? '提交中...' : '创建协作主题' }}</button>
      </div>
    </div>

    <div v-if="loading" class="px-5 py-12 text-center text-sm text-gray-400">业务协作加载中...</div>
    <div v-else-if="threads.length === 0" class="px-5 py-12 text-center">
      <MessageCircle class="mx-auto h-8 w-8 text-violet-200" />
      <p class="mt-3 text-sm text-gray-500">当前 L3 还没有业务协作主题</p>
      <p class="mt-1 text-xs text-gray-400">可以从上方发起协作，也可以在全局“业务协作”入口提交。</p>
    </div>
    <div v-else class="divide-y divide-gray-100">
      <article v-for="thread in threads" :key="thread.id" class="bg-white">
        <button type="button" class="flex w-full items-start justify-between gap-4 px-5 py-4 text-left transition hover:bg-gray-50/70" @click="setActiveThread(thread.id)">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span :class="kindClass(thread.kind)">{{ thread.kindLabel }}</span>
              <span :class="statusClass(thread.status)">{{ thread.statusLabel }}</span>
              <span class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">{{ thread.direction === 'it_to_business' ? 'IT → 业务' : '业务 → IT' }}</span>
            </div>
            <h4 class="mt-2 truncate text-sm font-semibold text-gray-900">{{ thread.title }}</h4>
            <p class="mt-1 text-[11px] text-gray-400">{{ thread.requesterName || '-' }} → {{ thread.recipientName || '-' }} · {{ thread.messageCount || thread.messages?.length || 0 }} 条消息 · 最近更新 {{ thread.updatedAt || thread.createdAt }}</p>
          </div>
          <ChevronDown :class="['mt-1 h-4 w-4 shrink-0 text-gray-400 transition-transform', activeThreadId === thread.id ? 'rotate-180 text-violet-600' : '']" />
        </button>

        <div v-if="activeThreadId === thread.id" class="border-t border-gray-100 bg-gray-50/50 px-5 pb-5 pt-4">
          <div class="space-y-3">
            <div v-for="message in (thread.messages || [])" :key="message.id" :class="['flex gap-2.5', isMine(message) ? 'justify-end' : 'justify-start']">
              <div :class="['max-w-[88%] sm:max-w-[76%]', isMine(message) ? 'order-1' : 'order-2']">
                <div :class="['mb-1 flex items-center gap-2 text-[10px] text-gray-400', isMine(message) ? 'justify-end' : '']">
                  <span>{{ message.senderName || '协作成员' }}</span>
                  <span>{{ message.messageTypeLabel }}</span>
                  <span>{{ message.createdAt }}</span>
                </div>
                <div :class="['rounded-xl border px-3 py-2.5 shadow-sm', isMine(message) ? 'border-violet-200 bg-violet-600 text-white' : 'border-gray-200 bg-white text-gray-700']">
                  <p class="whitespace-pre-wrap text-sm leading-6">{{ message.content }}</p>
                  <div v-if="message.attachments?.length" class="mt-2 flex flex-wrap gap-1.5 border-t border-white/20 pt-2">
                    <button v-for="attachment in message.attachments" :key="attachment.id" type="button" class="inline-flex max-w-[220px] items-center gap-1 rounded-md border border-current/20 px-2 py-1 text-[11px] opacity-90 hover:opacity-100" @click.stop="previewAttachment(attachment)">
                      <span>{{ attachment.isImage ? '图' : attachment.isVideo ? '视' : '件' }}</span>
                      <span class="truncate">{{ attachment.originalName }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="isAuthenticated && !['resolved', 'closed'].includes(thread.status)" class="mt-4 rounded-xl border border-violet-100 bg-white p-3 shadow-sm">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-xs font-semibold text-gray-700">继续讨论</span>
              <div class="flex flex-wrap gap-2">
                <select v-model="draftFor(thread).messageType" class="rounded-md border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-600">
                  <option v-for="item in messageTypeOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
                </select>
                <select v-model="draftFor(thread).status" class="rounded-md border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-600">
                  <option v-for="item in statusOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
                </select>
              </div>
            </div>
            <textarea v-model="draftFor(thread).content" rows="3" class="feishu-input mt-2 w-full resize-y" placeholder="输入回复、资料说明、交付回执或问题反馈；支持直接粘贴图片" @paste.stop="handlePaste(thread.id, $event)" />
            <AttachmentPicker :files="filesFor(thread.id)" @add="addFiles(thread.id, $event)" @remove="removeFile(thread.id, $event)" />
            <div class="mt-2 flex items-center justify-between gap-3">
              <p class="text-[11px] text-gray-400">发送后会通知协作对象，并在当前 L3 动态中留下记录。</p>
              <button type="button" class="feishu-btn-primary shrink-0 text-xs" :disabled="saving === thread.id" @click="sendMessage(thread)">{{ saving === thread.id ? '发送中...' : '发送消息' }}</button>
            </div>
          </div>
          <div v-else-if="['resolved', 'closed'].includes(thread.status)" class="mt-4 rounded-lg border border-emerald-100 bg-emerald-50/70 px-3 py-2 text-xs text-emerald-700">该协作主题已完成，可以从上方重新发起新的问题主题。</div>
        </div>
      </article>
    </div>

    <div v-if="attachmentPreview.open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" @click.self="closeAttachmentPreview">
      <div class="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-xl bg-white shadow-xl">
        <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
          <p class="truncate text-sm font-semibold text-gray-800">{{ attachmentPreview.name }}</p>
          <button type="button" class="text-xl text-gray-400 hover:text-gray-700" @click="closeAttachmentPreview">×</button>
        </div>
        <div class="flex max-h-[72vh] items-center justify-center overflow-auto bg-gray-50 p-4">
          <img v-if="attachmentPreview.isImage" :src="attachmentPreview.url" class="max-h-[65vh] max-w-full object-contain" />
          <video v-else-if="attachmentPreview.isVideo" :src="attachmentPreview.url" controls class="max-h-[65vh] max-w-full" />
          <div v-else class="py-16 text-center text-sm text-gray-500">该文件类型不支持内嵌预览，请下载后打开。</div>
        </div>
        <div class="flex justify-end border-t border-gray-100 px-4 py-3">
          <a :href="attachmentPreview.url" :download="attachmentPreview.name" class="feishu-btn-primary">下载文件</a>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { SESSION_STORAGE_KEY } from '@/api/session-storage'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ChevronDown, MessageCircle, MessagesSquare, Plus } from 'lucide-vue-next'
import { api } from '../api/application-api'
import AttachmentPicker from './AttachmentPicker.vue'

const props = defineProps<{ requirementId: string }>()

const kindOptions = [
  { key: 'resource_request', label: '资料提供' },
  { key: 'clarification', label: '规则确认' },
  { key: 'business_feedback', label: '意见反馈' },
  { key: 'issue', label: '问题反馈' },
  { key: 'acceptance', label: '测试验收' },
]
const statusOptions = [
  { key: 'waiting_business', label: '待业务回复' },
  { key: 'waiting_it', label: '待 IT 处理' },
  { key: 'resolved', label: '已完成' },
  { key: 'closed', label: '已关闭' },
]
const messageTypeOptions = [
  { key: 'message', label: '讨论消息' },
  { key: 'delivery', label: '交付回执' },
  { key: 'issue', label: '问题反馈' },
  { key: 'acceptance', label: '验收确认' },
]

const currentUser = ref<any>({})
const threads = ref<any[]>([])
const loading = ref(false)
const saving = ref('')
const newThreadOpen = ref(false)
const activeThreadId = ref('')
const newThread = ref({ kind: 'clarification', title: '', content: '', recipientName: '', dueDate: '' })
const drafts = ref<Record<string, any>>({})
const fileMap = ref<Record<string, File[]>>({ new: [] })
const previewUrls = new Map<File, string>()
const attachmentPreview = ref<any>({ open: false, url: '', name: '', isImage: false, isVideo: false })

const isAuthenticated = computed(() => !!currentUser.value.sessionToken)
const openCount = computed(() => threads.value.filter(item => !['resolved', 'closed'].includes(item.status)).length)
const newFiles = computed(() => fileMap.value.new || [])

function readUser() {
  try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} }
}

function draftFor(thread: any) {
  if (!drafts.value[thread.id]) {
    drafts.value[thread.id] = { content: '', messageType: 'message', status: defaultReplyStatus(thread) }
  }
  return drafts.value[thread.id]
}
function defaultReplyStatus(thread: any) {
  return thread.direction === 'it_to_business' ? 'waiting_it' : 'waiting_business'
}
function filesFor(owner: string) {
  if (!fileMap.value[owner]) fileMap.value[owner] = []
  return fileMap.value[owner]
}
function setActiveThread(id: string) {
  activeThreadId.value = activeThreadId.value === id ? '' : id
  const thread = threads.value.find(item => item.id === id)
  if (thread) draftFor(thread)
}
function isMine(message: any) {
  const userId = currentUser.value.dingUserId || currentUser.value.userid || ''
  return (userId && userId === message.senderUserId) || (!!currentUser.value.name && currentUser.value.name === message.senderName)
}
function addFiles(owner: string, files: File[]) {
  const current = filesFor(owner)
  for (const file of files) {
    if (file.size > 50 * 1024 * 1024) { alert(`附件「${file.name}」超过50MB，未添加`); continue }
    if (current.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) continue
    current.push(file)
    if (file.type.startsWith('image/')) previewUrls.set(file, URL.createObjectURL(file))
  }
}
function handlePaste(owner: string, event: ClipboardEvent) {
  const items = Array.from(event.clipboardData?.items || [])
  const images = items.filter(item => item.type.startsWith('image/')).map(item => item.getAsFile()).filter(Boolean) as File[]
  if (!images.length) return
  event.preventDefault()
  addFiles(owner === 'active' ? activeThreadId.value || 'new' : owner, images.map((file, index) => new File([file], `clipboard-${Date.now()}-${index}.${file.type.split('/')[1] || 'png'}`, { type: file.type })))
}
function removeFile(owner: string, index: number) {
  const files = filesFor(owner)
  const file = files[index]
  if (file) {
    const url = previewUrls.get(file)
    if (url) URL.revokeObjectURL(url)
    previewUrls.delete(file)
  }
  files.splice(index, 1)
}
async function uploadFiles(ownerType: string, ownerId: string, owner: string) {
  const files = filesFor(owner)
  for (const file of files) await api.uploadBusinessAttachment(ownerType, ownerId, file)
}
async function createThread() {
  if (!newThread.value.title.trim() || (!newThread.value.content.trim() && !newFiles.value.length)) { alert('请填写协作主题标题和第一条消息'); return }
  saving.value = 'new'
  const result: any = await api.createRequirementBusinessCollaboration(props.requirementId, { ...newThread.value })
  if (!result) { saving.value = ''; alert('协作主题创建失败，请检查登录状态和参与人权限'); return }
  const messageId = result.messageId || result.messages?.[0]?.id
  if (messageId && newFiles.value.length) await uploadFiles('collaboration_message', messageId, 'new')
  clearOwnerFiles('new')
  newThread.value = { kind: 'clarification', title: '', content: '', recipientName: '', dueDate: '' }
  newThreadOpen.value = false
  saving.value = ''
  await load()
  activeThreadId.value = result.id
  alert('协作主题已创建')
}
async function sendMessage(thread: any) {
  const draft = draftFor(thread)
  if (!draft.content.trim() && !filesFor(thread.id).length) { alert('请输入消息或添加附件'); return }
  saving.value = thread.id
  const result: any = await api.createBusinessCollaborationMessage(thread.id, {
    content: draft.content,
    messageType: draft.messageType,
    status: draft.status,
  })
  if (!result) { saving.value = ''; alert('消息发送失败，请检查协作权限'); return }
  const messageId = result.messageId || result.messages?.[result.messages.length - 1]?.id
  if (messageId && filesFor(thread.id).length) await uploadFiles('collaboration_message', messageId, thread.id)
  clearOwnerFiles(thread.id)
  drafts.value[thread.id] = { content: '', messageType: 'message', status: defaultReplyStatus(thread) }
  saving.value = ''
  await load()
  activeThreadId.value = thread.id
}
async function load() {
  if (!props.requirementId) return
  loading.value = true
  const result: any = await api.getRequirementBusinessCollaborations(props.requirementId)
  if (result) {
    threads.value = result
    for (const thread of result) draftFor(thread)
    if (!activeThreadId.value && result.length) activeThreadId.value = result[0].id
  }
  loading.value = false
}
function clearOwnerFiles(owner: string) {
  for (const file of filesFor(owner)) {
    const url = previewUrls.get(file)
    if (url) URL.revokeObjectURL(url)
    previewUrls.delete(file)
  }
  fileMap.value[owner] = []
}
function previewAttachment(attachment: any) {
  api.getBusinessAttachmentBlob(attachment.id).then(blob => {
    if (!blob) { alert('附件读取失败，请刷新后重试'); return }
    const url = URL.createObjectURL(blob)
    if (!attachment.isImage && !attachment.isVideo) {
      const link = document.createElement('a'); link.href = url; link.download = attachment.originalName || 'attachment'; link.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 30000)
      return
    }
    closeAttachmentPreview()
    attachmentPreview.value = { open: true, url, name: attachment.originalName, isImage: attachment.isImage, isVideo: attachment.isVideo }
  })
}
function closeAttachmentPreview() {
  if (attachmentPreview.value.url) URL.revokeObjectURL(attachmentPreview.value.url)
  attachmentPreview.value = { open: false, url: '', name: '', isImage: false, isVideo: false }
}
function kindClass(kind: string) { return ['resource_request', 'issue'].includes(kind) ? 'rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-600' : 'rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-semibold text-violet-600' }
function statusClass(status: string) {
  if (['resolved', 'closed'].includes(status)) return 'rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-600'
  if (['waiting_business', 'waiting_it'].includes(status)) return 'rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600'
  return 'rounded bg-rose-50 px-1.5 py-0.5 text-[10px] font-semibold text-rose-600'
}

onMounted(() => { readUser(); load() })
onUnmounted(() => {
  for (const owner of Object.keys(fileMap.value)) clearOwnerFiles(owner)
  closeAttachmentPreview()
})
</script>

<style scoped>
.form-label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.7rem;
  color: #6b7280;
}
</style>
