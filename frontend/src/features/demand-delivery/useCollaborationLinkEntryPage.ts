
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/application-api'
export function useCollaborationLinkEntryPage() {

const token = String(useRoute().query.token || '')
const context = ref<any>(null), loading = ref(true), saving = ref(false), error = ref(''), outcome = ref(''), content = ref(''), feedbackType = ref(''), requestedTitle = ref('')
const files = ref<File[]>([])
const uploadKeys = new Map<File, string>(), uploaded = new Set<File>()
const copy = computed(() => {
  const kind = context.value?.kind
  if (kind === 'materials') return {
    title: '请补充资料',
    intro: '开发人员需要你补充以下资料，填写说明或上传文件后直接提交即可。',
    showCriteria: false,
    criteriaTitle: '',
    choiceTitle: '',
    responseLabel: '资料说明',
    responsePlaceholder: '请写明资料内容、来源或补充说明；也可以直接上传文件',
    attachmentHint: '最多 10 个附件，单个不超过 50MB。',
    submitLabel: '提交资料',
    submittedTitle: '资料已提交',
  }
  if (kind === 'baseline') return {
    title: '请确认上线前交付标准',
    intro: '请确认本次交付如何验收；如需调整，请选择“需要修改”。',
    showCriteria: true,
    criteriaTitle: '本次需要确认的内容',
    choiceTitle: '交付标准确认结果',
    responseLabel: '确认说明',
    responsePlaceholder: '确认通过可不填写；如需修改，请写明需要调整的内容',
    attachmentHint: '如有范围补充，可上传附件。单个不超过 50MB。',
    submitLabel: '提交交付标准确认',
    submittedTitle: '交付标准确认已提交',
  }
  return {
    title: '请确认本次交付',
    intro: '请根据已确认的上线前验收标准检查本次交付结果；确认通过后，IT 将完成上线记录。',
    showCriteria: true,
    criteriaTitle: '本次交付标准',
    choiceTitle: '交付确认结果',
    responseLabel: '确认说明',
    responsePlaceholder: '确认交付可不填写；如需修改，请写明问题、复现步骤或补充要求',
    attachmentHint: '可上传验证截图或报告。单个不超过 50MB。',
    submitLabel: '提交交付确认',
    submittedTitle: '交付确认已提交',
  }
})
const choices = computed(() => [
  { value: context.value?.kind === 'baseline' ? 'confirmed' : 'passed', label: context.value?.kind === 'baseline' ? '确认按此范围与标准推进' : '确认交付，符合上线标准' },
  { value: 'changes', label: '需要修改或补充' },
])
const feedbackTypeChoices = [
  { value: 'original_gap', label: '原验收标准未达标 / 问题修复' },
  { value: 'improvement', label: '现有功能优化' },
  { value: 'new_feature', label: '新增功能或扩大范围' },
  { value: 'requirement_change', label: '业务目标或需求重构' },
  { value: 'other', label: '其他，需要 IT 判断' },
]
function addFiles(incoming: File[]) {
  for (const file of incoming) {
    if (file.size > 50 * 1024 * 1024) { error.value = '单个附件不能超过 50MB'; continue }
    if (files.value.some(f => f.name === file.name && f.size === file.size)) continue
    if (files.value.length + (context.value?.draftAttachments.length || 0) >= 10) { error.value = '最多 10 个附件'; break }
    files.value.push(file); uploadKeys.set(file, crypto.randomUUID())
  }
}
function removeFile(index: number) {
  if (uploaded.has(files.value[index])) { error.value = '该附件已上传，将随本轮提交；请在说明中注明更正内容'; return }
  files.value.splice(index, 1)
}
async function submit() {
  if (saving.value) return
  if (context.value.kind !== 'materials' && !outcome.value) { error.value = '请选择确认结果'; return }
  if (outcome.value === 'changes' && !content.value.trim()) { error.value = '请说明需要修改的内容'; return }
  if (context.value.kind === 'verification' && outcome.value === 'changes' && !feedbackType.value) { error.value = '请选择修改类型'; return }
  saving.value = true; error.value = ''
  try {
    for (const file of files.value) if (!uploaded.has(file)) { await api.uploadCollaborationLinkFile(token, file, uploadKeys.get(file)!); uploaded.add(file) }
    context.value = await api.submitCollaborationLink(token, { outcome: context.value.kind === 'materials' ? 'provided' : outcome.value, content: content.value, feedbackType: feedbackType.value, requestedTitle: requestedTitle.value })
    files.value = []
  } catch (e: any) { error.value = e.message || '保存失败，已填写内容保留，可重试' }
  finally { saving.value = false }
}
async function download(attachment: any) {
  try { const blob = await api.downloadCollaborationLinkFile(token, attachment.id); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = attachment.originalName; a.click(); setTimeout(() => URL.revokeObjectURL(url), 30000) }
  catch (e: any) { error.value = e.message }
}
onMounted(async () => {
  try { if (!token) throw new Error('链接缺少有效凭证，请联系 IT'); context.value = await api.getCollaborationLinkContext(token) }
  catch (e: any) { error.value = e.message }
  finally { loading.value = false }
})
return { token, context, loading, saving, error, outcome, content, feedbackType, requestedTitle, files, uploadKeys, uploaded, copy, choices, feedbackTypeChoices, addFiles, removeFile, submit, download }
}
