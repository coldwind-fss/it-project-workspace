import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BrainCircuit, ChevronRight, FlaskConical, Link2, Paperclip, Plus, Save, Search } from 'lucide-vue-next'
import { api } from '../../api/application-api'
export function usePocWorkbenchPage(){


const router = useRouter()
const records = ref<any[]>([])
const projects = ref<any[]>([])
const requirements = ref<any[]>([])
const demands = ref<any[]>([])
const pendingFiles = ref<File[]>([])
const loading = ref(false)
const saving = ref(false)
const isCreating = ref(false)
const selectedId = ref('')
const keyword = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const notice = ref('')
const errorMessage = ref('')
const options = ref<any>({ statuses: [], conclusions: [] })

function blankForm() {
  return {
    id: '', title: '', recordType: 'poc', status: 'draft', conclusion: '', ownerUserId: '', ownerName: '',
    projectId: '', projectName: '', requirementId: '', requirementTitle: '', demandId: '', demandTitle: '',
    sourceType: 'development', sourceRef: '', derivedFromId: '', objective: '', hypothesis: '', scope: '', sampleData: '',
    method: '', successCriteria: '', result: '', limitations: '', nextSteps: '', modelName: '', modelVersion: '',
    promptOrApproach: '', metrics: {}, metricText: '', reuseGuidance: '', tags: [], tagsText: '', artifactType: 'text',
    createdAt: '', updatedAt: '', completedAt: '', archivedAt: '', attachments: [], legacy: false, readOnly: false,
  }
}
const form = reactive<any>(blankForm())

const selectedRecord = computed(() => records.value.find(item => item.id === selectedId.value) || null)
const filteredRecords = computed(() => {
  const needle = keyword.value.trim().toLowerCase()
  return records.value.filter(item => {
    if (typeFilter.value && item.recordType !== typeFilter.value) return false
    if (statusFilter.value && item.status !== statusFilter.value) return false
    if (!needle) return true
    return [item.title, item.objective, item.result, item.reuseGuidance, item.demandTitle].some(value => String(value || '').toLowerCase().includes(needle))
  })
})

function listOf(value: any) {
  return Array.isArray(value) ? value : Array.isArray(value?.items) ? value.items : Array.isArray(value?.data) ? value.data : []
}
function countByType(type: string) { return records.value.filter(item => item.recordType === type).length }
function formatTime(value: string) { return value ? String(value).replace('T', ' ').slice(0, 16) : '未记录时间' }
function relatedLabel(record: any) { return [record.projectName, record.requirementTitle, record.demandTitle].filter(Boolean).join(' · ') }
function setMessage(message: string, error = false) { notice.value = error ? '' : message; errorMessage.value = error ? message : ''; window.setTimeout(() => { notice.value = ''; errorMessage.value = '' }, 4000) }

function copyIntoForm(record: any) {
  Object.assign(form, blankForm(), record || {})
  form.metricText = JSON.stringify(record?.metrics || {}, null, 2)
  form.tagsText = Array.isArray(record?.tags) ? record.tags.join(', ') : ''
}
function selectRecord(record: any) {
  isCreating.value = false
  selectedId.value = record.id
  pendingFiles.value = []
  copyIntoForm(record)
  notice.value = ''
  errorMessage.value = ''
}
function startCreate() {
  isCreating.value = true
  selectedId.value = ''
  pendingFiles.value = []
  copyIntoForm({ ownerName: currentUserName(), sourceType: 'development' })
  notice.value = ''
  errorMessage.value = ''
}
function currentUserName() {
  try { return JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}')?.name || '' } catch { return '' }
}
function addFiles(files: File[]) { pendingFiles.value = [...pendingFiles.value, ...files].slice(0, 10) }
function removeFile(index: number) { pendingFiles.value.splice(index, 1) }

async function load() {
  loading.value = true
  const [optionResult, recordResult, projectResult, requirementResult, demandResult] = await Promise.all([
    api.getPocWorkbenchOptions(), api.getPocWorkbenchRecords(), api.getProjects(), api.getRequirements({}), api.getDemandPool(),
  ])
  options.value = optionResult || { statuses: [], conclusions: [] }
  records.value = listOf(recordResult)
  projects.value = listOf(projectResult)
  requirements.value = listOf(requirementResult)
  demands.value = listOf(demandResult)
  loading.value = false
  if (selectedId.value) {
    const refreshed = records.value.find(item => item.id === selectedId.value)
    if (refreshed) copyIntoForm(refreshed)
  }
}

function payloadFromForm() {
  let metrics = {}
  if (form.metricText.trim()) {
    try {
      const parsed = JSON.parse(form.metricText)
      if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error('指标必须是 JSON 对象')
      metrics = parsed
    } catch (error: any) { throw new Error(error?.message || '指标 JSON 格式不正确') }
  }
  return {
    ...form,
    metrics,
    tags: form.tagsText.split(/[,，]/).map((item: string) => item.trim()).filter(Boolean),
  }
}

async function saveRecord() {
  if (form.legacy) return
  if (!form.title.trim()) { setMessage('请先填写记录名称', true); return }
  saving.value = true
  try {
    const payload = payloadFromForm()
    const result: any = isCreating.value ? await api.createPocWorkbenchRecord(payload) : await api.updatePocWorkbenchRecord(form.id, payload)
    if (!result?.id) throw new Error('保存失败，请刷新后重试')
    for (const file of pendingFiles.value) {
      const uploaded = await api.uploadBusinessAttachment('poc_workbench', result.id, file)
      if (!uploaded) throw new Error(`附件“${file.name}”上传失败`)
    }
    pendingFiles.value = []
    isCreating.value = false
    selectedId.value = result.id
    await load()
    const refreshed = records.value.find(item => item.id === result.id)
    if (refreshed) copyIntoForm(refreshed)
    setMessage('记录已保存')
  } catch (error: any) { setMessage(error?.message || '保存失败，请重试', true) }
  finally { saving.value = false }
}

async function deriveCapability() {
  if (!form.id || form.legacy) return
  saving.value = true
  try {
    const result: any = await api.derivePocWorkbenchCapability(form.id, { reuseGuidance: form.reuseGuidance })
    if (!result?.id) throw new Error('沉淀失败，请刷新后重试')
    await load()
    selectRecord(result)
    setMessage('已生成一条 AI 能力记录，可以继续补充复用边界')
  } catch (error: any) { setMessage(error?.message || '沉淀失败，请重试', true) }
  finally { saving.value = false }
}

async function downloadAttachment(file: any) {
  const blob = await api.getBusinessAttachmentBlob(file.id)
  if (!blob) { setMessage('附件下载失败', true); return }
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = file.originalName || file.filename || 'attachment'; anchor.click(); URL.revokeObjectURL(url)
}

onMounted(load)
return { router, records, projects, requirements, demands, pendingFiles, loading, saving, isCreating, selectedId, keyword, typeFilter, statusFilter, notice, errorMessage, options, blankForm, form, selectedRecord, filteredRecords, listOf, countByType, formatTime, relatedLabel, setMessage, copyIntoForm, selectRecord, startCreate, currentUserName, addFiles, removeFile, load, payloadFromForm, saveRecord, deriveCapability, downloadAttachment }
}
