<template>
  <section class="rounded-xl border border-gray-200 bg-white" :class="compact ? 'p-3' : 'p-4'">
    <div v-if="title || !compact" class="mb-3 flex flex-wrap items-start justify-between gap-2">
      <div>
        <h2 class="flex items-center gap-2 text-sm font-semibold text-gray-900">
          <MessagesSquare class="h-4 w-4 text-violet-500" />
          {{ title || '共享动态' }}
        </h2>
        <p class="mt-1 text-[11px] text-gray-400">{{ subtitle || '开发人员与业务人员围绕同一条产品动态直接评论，信息会同步出现在双方工作区。' }}</p>
      </div>
      <span class="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-medium text-violet-600">{{ scopeType === 'project' ? 'L2 产品生态' : 'L3 需求生态' }}</span>
    </div>

    <div v-if="errorMessage" class="mb-3 rounded-lg border border-amber-100 bg-amber-50/60 px-3 py-2 text-xs text-amber-700">
      {{ errorMessage }}
    </div>

    <div v-if="allowCompose" class="mb-4 rounded-lg border border-violet-100 bg-violet-50/30 p-3">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div class="flex flex-wrap gap-1.5">
          <button type="button" class="rounded-md border px-2.5 py-1.5 text-[11px] font-medium" :class="composeMode === 'activity' ? 'border-violet-500 bg-violet-500 text-white' : 'border-violet-200 bg-white text-violet-700'" @click="composeMode = 'activity'">发布动态</button>
          <button v-if="enableCollaboration && scopeType === 'requirement'" type="button" class="rounded-md border px-2.5 py-1.5 text-[11px] font-medium" :class="composeMode === 'materials' ? 'border-violet-500 bg-violet-500 text-white' : 'border-violet-200 bg-white text-violet-700'" @click="startMaterialsRequest">请补充资料</button>
        </div>
        <select v-if="composeMode === 'activity'" v-model="activityType" class="feishu-input h-8 w-auto text-[11px]">
          <option v-for="item in activityTypes" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
      </div>

      <template v-if="composeMode === 'activity'">
        <textarea v-model="activityDraft" rows="3" class="feishu-input w-full resize-y text-xs" placeholder="记录进展、提出问题、说明交付或补充业务反馈；也可以直接粘贴图片" @paste="handlePaste($event, 'activity')" />
        <AttachmentPicker :files="activityFiles" @add="files => addFiles(activityFiles, files)" @remove="index => activityFiles.splice(index, 1)" />
        <div class="mt-2 flex justify-end">
          <button class="feishu-btn-primary text-xs" :disabled="saving" @click="publishActivity">{{ saving ? '发布中...' : '发布动态' }}</button>
        </div>
      </template>

      <template v-else>
        <div class="mb-3 rounded-md border border-violet-100 bg-white px-3 py-2 text-[11px] leading-5 text-violet-800">
          业务人员打开链接后，只会看到这次资料请求和回复表单；回复会回到下面同一条协作记录。
        </div>
        <div class="grid gap-2 sm:grid-cols-2">
          <label class="block text-[11px] text-gray-600">业务回复人
            <input v-model="collaborationRecipient" class="feishu-input mt-1 w-full text-xs" maxlength="120" placeholder="例如：十叶-冯硕硕" />
          </label>
          <label class="block text-[11px] text-gray-600">链接有效天数
            <input v-model.number="collaborationValidDays" class="feishu-input mt-1 w-full text-xs" type="number" min="1" max="90" />
          </label>
        </div>
        <label class="mt-2 block text-[11px] text-gray-600">需要补充什么资料
          <textarea v-model="collaborationDraft" rows="3" maxlength="10000" class="feishu-input mt-1 w-full resize-y text-xs" placeholder="例如：请补充目前的业务流程、使用人员和历史样例。" />
        </label>
        <div v-if="collaborationLink" class="mt-2 rounded-md border border-emerald-100 bg-emerald-50 px-3 py-2 text-[11px] leading-5 text-emerald-800">
          资料请求已生成并发送。<button type="button" class="ml-1 font-medium underline" @click="copyCollaborationLink">复制业务链接</button>
        </div>
        <div class="mt-2 flex justify-end gap-2">
          <button type="button" class="feishu-btn-ghost text-xs" @click="composeMode = 'activity'">返回发布动态</button>
          <button type="button" class="feishu-btn-primary text-xs" :disabled="saving" @click="createMaterialsRequest">{{ saving ? '发送中...' : '生成链接并发送' }}</button>
        </div>
      </template>
    </div>

    <div v-if="loading" class="flex h-28 items-center justify-center">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
    </div>
    <div v-else-if="!activities.length" class="rounded-lg bg-gray-50 px-3 py-8 text-center text-xs text-gray-400">
      还没有共享动态；简单事项可以只发一条消息，复杂事项再继续评论。
    </div>
    <div v-else class="space-y-3">
      <article v-for="activity in activities" :key="activity.id" class="rounded-lg border border-gray-100 bg-gray-50/50 p-3">
        <div class="flex items-start gap-2">
          <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-100 text-[11px] font-bold text-violet-700">{{ (activity.actorName || '系')[0] }}</div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="text-xs font-semibold text-gray-800">{{ activity.actorName || '系统' }}</span>
              <span class="rounded bg-white px-1.5 py-0.5 text-[10px] font-medium text-violet-600">{{ activity.activityTypeLabel }}</span>
              <span class="text-[10px] text-gray-400">{{ formatTime(activity.createdAt) }}</span>
            </div>
            <p v-if="activity.title && activity.title !== activity.activityTypeLabel" class="mt-1 text-xs font-medium text-gray-700">{{ activity.title }}</p>
            <p class="mt-1 whitespace-pre-wrap text-xs leading-5 text-gray-700">{{ activity.content }}</p>
            <div class="mt-2 flex flex-wrap items-center gap-2 text-[10px]">
              <button v-if="activity.requirementId && scopeType === 'project'" class="text-accent-600 hover:text-accent-700" @click="openRequirement(activity.requirementId)">打开对应 L3 →</button>
              <span v-if="activity.commentCount" class="text-gray-400">{{ activity.commentCount }} 条评论</span>
            </div>
            <div v-if="activity.attachments?.length" class="mt-2 flex flex-wrap gap-1.5">
              <button v-for="attachment in activity.attachments" :key="attachment.id" class="rounded border border-gray-200 bg-white px-2 py-1 text-[10px] text-gray-600 hover:border-violet-300 hover:text-violet-600" @click="downloadAttachment(attachment)">
                {{ attachment.isImage ? '图片' : attachment.isVideo ? '视频' : '附件' }} · {{ attachment.originalName }}
              </button>
            </div>

            <div v-if="activity.comments?.length" class="mt-3 space-y-2 border-l-2 border-violet-100 pl-3">
              <div v-for="comment in activity.comments" :key="comment.id" class="rounded-md bg-white px-2.5 py-2">
                <div class="flex flex-wrap items-center gap-1.5"><span class="text-[11px] font-medium text-gray-700">{{ comment.commenterName || '协作方' }}</span><span class="text-[10px] text-gray-400">{{ formatTime(comment.createdAt) }}</span></div>
                <p class="mt-1 whitespace-pre-wrap text-xs leading-5 text-gray-600">{{ comment.content }}</p>
                <div v-if="comment.attachments?.length" class="mt-1.5 flex flex-wrap gap-1.5">
                  <button v-for="attachment in comment.attachments" :key="attachment.id" class="text-[10px] text-violet-600 hover:text-violet-700" @click="downloadAttachment(attachment)">{{ attachment.originalName }}</button>
                </div>
              </div>
            </div>
            <button class="mt-3 text-[11px] font-medium text-violet-600 hover:text-violet-700" @click="toggleComment(activity.id)">{{ openCommentId === activity.id ? '收起评论' : '评论这条动态' }}</button>
            <div v-if="openCommentId === activity.id" class="mt-2 rounded-md border border-violet-100 bg-white p-2">
              <textarea v-model="commentDrafts[activity.id]" rows="2" class="feishu-input w-full resize-y text-xs" placeholder="写下你的疑问、配合信息或验收意见；也可以粘贴图片" @paste="handlePaste($event, 'comment', activity.id)" />
              <AttachmentPicker :files="commentFiles[activity.id] || []" @add="files => addCommentFiles(activity.id, files)" @remove="index => removeCommentFile(activity.id, index)" />
              <div class="mt-2 flex justify-end"><button class="feishu-btn-primary text-[11px]" :disabled="commentSavingId === activity.id" @click="publishComment(activity)">{{ commentSavingId === activity.id ? '发送中...' : '发送评论' }}</button></div>
            </div>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { MessagesSquare } from 'lucide-vue-next'
import { api } from '../api/application-api'
import AttachmentPicker from './AttachmentPicker.vue'

const props = withDefaults(defineProps<{
  scopeType: 'project' | 'requirement'
  scopeId: string
  compact?: boolean
  title?: string
  subtitle?: string
  allowCompose?: boolean
  enableCollaboration?: boolean
  collaborationRecipient?: string
  collaborationTitle?: string
}>(), { compact: false, title: '', subtitle: '', allowCompose: true })
const emit = defineEmits<{ (event: 'activity-created'): void }>()
const router = useRouter()
const activities = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const commentSavingId = ref('')
const errorMessage = ref('')
const activityDraft = ref('')
const activityType = ref('work_progress')
const activityFiles = ref<File[]>([])
const composeMode = ref<'activity' | 'materials'>('activity')
const collaborationDraft = ref('')
const collaborationRecipient = ref('')
const collaborationValidDays = ref(14)
const collaborationLink = ref('')
const commentDrafts = reactive<Record<string, string>>({})
const commentFiles = reactive<Record<string, File[]>>({})
const openCommentId = ref('')
const activityTypes = [
  { value: 'work_progress', label: '工作进展' },
  { value: 'issue', label: '遇到问题' },
  { value: 'delivery', label: '交付回执' },
  { value: 'next_step', label: '下一步' },
  { value: 'feedback', label: '业务反馈' },
]

function startMaterialsRequest() {
  composeMode.value = 'materials'
  collaborationLink.value = ''
  collaborationDraft.value = ''
  collaborationRecipient.value = props.collaborationRecipient || ''
  collaborationValidDays.value = 14
}

async function load() {
  if (!props.scopeId) return
  loading.value = true
  errorMessage.value = ''
  const rows: any = props.scopeType === 'project'
    ? await api.getProjectSharedActivities(props.scopeId)
    : await api.getRequirementSharedActivities(props.scopeId)
  if (Array.isArray(rows)) activities.value = rows
  else errorMessage.value = '请在钉钉内登录，并确认自己是该产品或需求的参与者。'
  loading.value = false
}

function formatTime(value: string) { return value ? String(value).replace('T', ' ').slice(0, 16) : '刚刚' }
function addFiles(target: File[], files: File[]) {
  for (const file of files) {
    if (file.size > 50 * 1024 * 1024) { alert(`附件「${file.name}」超过50MB，未添加`); continue }
    if (!target.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) target.push(file)
  }
}
function addCommentFiles(activityId: string, files: File[]) {
  if (!commentFiles[activityId]) commentFiles[activityId] = []
  addFiles(commentFiles[activityId], files)
}
function removeCommentFile(activityId: string, index: number) { commentFiles[activityId]?.splice(index, 1) }
function handlePaste(event: ClipboardEvent, target: 'activity' | 'comment', activityId = '') {
  const files = Array.from(event.clipboardData?.items || []).filter(item => item.kind === 'file').map(item => item.getAsFile()).filter(Boolean) as File[]
  if (!files.length) return
  event.preventDefault()
  const renamed = files.map((file, index) => new File([file], `clipboard-${Date.now()}-${index}.${file.type.split('/')[1] || 'bin'}`, { type: file.type }))
  if (target === 'activity') addFiles(activityFiles.value, renamed)
  else addCommentFiles(activityId, renamed)
}
async function uploadFiles(ownerType: string, ownerId: string, files: File[]) {
  for (const file of files) {
    const saved: any = await api.uploadBusinessAttachment(ownerType, ownerId, file)
    if (!saved) alert(`动态已保存，但附件「${file.name}」上传失败`)
  }
}
async function publishActivity() {
  const content = activityDraft.value.trim()
  if (!content && !activityFiles.value.length) { alert('请填写动态内容或添加附件'); return }
  saving.value = true
  const createActivity = props.scopeType === 'project' ? api.createProjectSharedActivity : api.createRequirementSharedActivity
  const saved: any = await createActivity(props.scopeId, { activityType: activityType.value, content: content || '补充附件' })
  if (saved?.id && activityFiles.value.length) await uploadFiles('shared_activity', saved.id, activityFiles.value)
  saving.value = false
  if (!saved) { alert('动态发布失败，请检查登录状态和参与权限'); return }
  activityDraft.value = ''
  activityFiles.value = []
  await load()
  emit('activity-created')
}
async function createMaterialsRequest() {
  const content = collaborationDraft.value.trim()
  const recipientName = collaborationRecipient.value.trim()
  if (!recipientName) { alert('请填写业务回复人'); return }
  if (!content) { alert('请说明需要补充什么资料'); return }
  saving.value = true
  let saved: any = null
  try {
    saved = await api.createCollaborationLink(props.scopeId, {
      clientKey: crypto.randomUUID(),
      kind: 'materials',
      title: props.collaborationTitle || `资料请求：${props.scopeId}`,
      recipientName,
      validDays: collaborationValidDays.value,
      content,
      attachmentIds: [],
    })
  } catch (error: any) {
    alert(error?.message || '资料请求发送失败，请检查登录状态或需求权限')
    return
  } finally {
    saving.value = false
  }
  if (!saved) { alert('资料请求发送失败，请检查登录状态或需求权限'); return }
  collaborationLink.value = saved.link || ''
  collaborationDraft.value = ''
  await load()
  emit('activity-created')
}
async function copyCollaborationLink() {
  if (!collaborationLink.value) return
  try { await navigator.clipboard.writeText(collaborationLink.value); alert('业务链接已复制') }
  catch { window.prompt('请复制业务链接', collaborationLink.value) }
}
function toggleComment(id: string) { openCommentId.value = openCommentId.value === id ? '' : id }
async function publishComment(activity: any) {
  const files = commentFiles[activity.id] || []
  const content = String(commentDrafts[activity.id] || '').trim()
  if (!content && !files.length) { alert('请填写评论或添加附件'); return }
  commentSavingId.value = activity.id
  const saved: any = await api.createSharedActivityComment(activity.id, { content: content || '补充附件' })
  if (saved?.id && files.length) await uploadFiles('shared_activity_comment', saved.id, files)
  commentSavingId.value = ''
  if (!saved) { alert('评论发送失败，请检查登录状态和参与权限'); return }
  commentDrafts[activity.id] = ''
  commentFiles[activity.id] = []
  await load()
}
async function downloadAttachment(attachment: any) {
  const blob = await api.getBusinessAttachmentBlob(attachment.id)
  if (!blob) { alert('附件读取失败，请刷新后重试'); return }
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a'); link.href = url; link.download = attachment.originalName || 'attachment'; link.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 30000)
}
function openRequirement(id: string) { router.push('/requirements/' + id) }
watch(() => [props.scopeType, props.scopeId], load, { immediate: true })
watch(() => props.collaborationRecipient, value => {
  if (composeMode.value === 'activity' || !collaborationRecipient.value) collaborationRecipient.value = value || ''
})
</script>
