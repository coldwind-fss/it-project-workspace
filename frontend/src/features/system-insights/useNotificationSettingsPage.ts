import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { Edit3, Plus, Send, Trash2 } from 'lucide-vue-next'
import { api } from '../../api/application-api'
import { sessionAccess } from '../access/session-access'
import { showConfirm } from '../../utils/feedback'
export function useNotificationSettingsPage(){


const targets = ref<any[]>([])
const deliveries = ref<any[]>([])
const developers = ref<any[]>([])
const people = ref<any[]>([])
const projects = ref<any[]>([])
const requirements = ref<any[]>([])
const loadingTargets = ref(false)
const showModal = ref(false)
const editing = ref<any>(null)
const form = ref<any>({})
const canManage = ref(false)
const previewOpen = ref(false)
const previewLoading = ref(false)
const previewTitle = ref('')
const previewMarkdown = ref('')
const developerModes = [
  { value: 'self', label: '仅同步我自己' },
  { value: 'all', label: '全部开发者' },
  { value: 'custom', label: '指定开发者' },
]
const weekDays = [
  { value: 1, label: '周一' }, { value: 2, label: '周二' }, { value: 3, label: '周三' },
  { value: 4, label: '周四' }, { value: 5, label: '周五' }, { value: 6, label: '周六' }, { value: 7, label: '周日' },
]
const triggerEvents = [
  { value: 'project_created', label: '新增项目' },
  { value: 'project_updated', label: '项目资料更新' },
  { value: 'requirement_created', label: '新增需求' },
  { value: 'requirement_updated', label: '需求内容更新' },
  { value: 'requirement_assigned', label: '需求负责人变更' },
  { value: 'requirement_delivered', label: '需求交付/上线' },
  { value: 'todo_created', label: '生成待办' },
  { value: 'shared_activity_created', label: '发布共享动态' },
  { value: 'shared_activity_comment_created', label: '评论共享动态' },
]
const contentOptions = [
  { value: 'productDigest', label: '管理层产品简报', desc: '按产品归纳重点变化、交付结果和产品阶段，不展示流水账' },
  { value: 'workSummary', label: '工作记录与开发者成果', desc: '保留 L3 工作量、开发者成果和当前负责事项' },
  { value: 'ledgerTrace', label: 'L3 台账追溯入口', desc: '只展示记录数量和底库入口，需要时再查看完整明细' },
  { value: 'custom', label: '自定义内容', desc: '发送下方自由编辑区的文字' },
]
const contentOptionValues = new Set(contentOptions.map(opt => opt.value))

function normalizeContentTypes(types: string[] = []) {
  const normalized = new Set<string>()
  ;(types || []).forEach(type => {
    if (type === 'dashboard' || type === 'compactSummary') normalized.add('productDigest')
    else if (type === 'developerProgress') normalized.add('workSummary')
    else if (type === 'todayActivities') normalized.add('workSummary')
    else if (type === 'activities' || type === 'changelogs' || type === 'recentChangelogs') normalized.add('ledgerTrace')
    else if (contentOptionValues.has(type)) normalized.add(type)
  })
  return Array.from(normalized)
}

const currentUser = ref<any>({})
const summaryCards = computed(() => {
  const enabled = targets.value.filter(target => target.enabled)
  const scheduled = enabled.filter(target => target.triggerType !== 'event' && target.scheduleTime)
  const latest = targets.value.map(target => target.lastSentAt || target.lastSentDate).filter(Boolean).sort().pop()
  return [
    { label: '通知规则', value: targets.value.length, desc: '已配置的消息出口', className: 'border-blue-100 bg-blue-50/60', valueClass: 'text-blue-600' },
    { label: '已启用', value: enabled.length, desc: '当前可主动或定时发送', className: 'border-emerald-100 bg-emerald-50/60', valueClass: 'text-emerald-600' },
    { label: '定时发送', value: scheduled.length, desc: '已设置发送时间的规则', className: 'border-amber-100 bg-amber-50/60', valueClass: 'text-amber-600' },
    { label: '最近发送', value: latest ? lastSentLabel({ lastSentDate: latest }) : '—', desc: '现有发送记录中的最近日期', className: 'border-violet-100 bg-violet-50/60', valueClass: 'text-violet-600' },
  ]
})

const currentDeveloperName = computed(() => currentUser.value?.devOwnerName || '')
const currentUserId = computed(() => currentUser.value?.dingUserId || currentUser.value?.userid || '')
const developerHint = computed(() => {
  if (form.value.developerMode === 'all') return '会同步系统管理中配置的全部开发者需求进度。'
  if (form.value.developerMode === 'custom') return form.value.developer ? `当前绑定：${form.value.developer}` : '请选择一个开发者。'
  return currentDeveloperName.value ? `当前绑定：${currentDeveloperName.value}` : '当前账号还没有识别到开发者身份，可切换为“指定开发者”。'
})

function blankForm() {
  return {
    name: '', webhook: '', secret: '', scope: 'dashboard',
    deliveryChannel: 'group', recipientName: '', recipientUserId: '',
    cardTargetType: 'personal', cardConversationId: '',
    cardTemplateId: '1dbfda44-9e08-4743-805b-a638831a3bd9.schema', cardRobotCode: '',
    targetType: 'global', projectId: '', requirementId: '',
    triggerType: 'schedule', triggerEvents: [],
    developerMode: currentDeveloperName.value ? 'self' : 'custom',
    developer: currentDeveloperName.value || '',
    developerUserId: currentUserId.value || '',
    ownerUserId: currentUserId.value || '',
    ownerName: currentUser.value?.name || '',
    scheduleTime: '', scheduleCycle: 'daily', scheduleDay: 1, scheduleWeekdays: [1, 2, 3, 4, 5, 6, 7],
    contentRange: 'today', customRangeStart: '', customRangeEnd: '', reportScene: 'daily', enabled: true,
    contentTypes: ['productDigest', 'workSummary'], customContent: '',
  }
}
function openCreate() { editing.value = null; form.value = blankForm(); showModal.value = true }
function editTarget(t: any) {
  editing.value = t
  const targetType = t.targetType || (t.scope === 'developer' ? 'developer' : 'global')
  const mode = !t.developer ? 'all' : (t.developerUserId && currentUserId.value && t.developerUserId === currentUserId.value ? 'self' : 'custom')
  form.value = {
    ...t,
    targetType,
    deliveryChannel: t.deliveryChannel || 'group',
    cardTargetType: t.cardTargetType || 'personal',
    cardConversationId: t.cardConversationId || '',
    cardTemplateId: t.cardTemplateId || '1dbfda44-9e08-4743-805b-a638831a3bd9.schema',
    cardRobotCode: t.cardRobotCode || '',
    scheduleWeekdays: Array.isArray(t.scheduleWeekdays) && t.scheduleWeekdays.length ? t.scheduleWeekdays : [1, 2, 3, 4, 5],
    triggerType: t.triggerType || 'schedule',
    triggerEvents: Array.isArray(t.triggerEvents) ? t.triggerEvents : [],
    developerMode: mode,
    contentTypes: normalizeContentTypes(t.contentTypes || []),
    customContent: t.customContent || '',
  }
  showModal.value = true
}
function closeModal() { showModal.value = false; editing.value = null; form.value = {} }

function scopeLabel(scope: string) {
  return scope === 'developer' ? '开发者工作' : '管理层产品总览'
}

function channelLabel(channel: string) {
  if (channel === 'personal') return '个人机器人（Markdown）'
  if (channel === 'card') return '历史互动卡片（已停用）'
  return '群机器人（Markdown）'
}

function targetTypeLabel(target: any) {
  const type = target.targetType || (target.scope === 'developer' ? 'developer' : 'global')
  if (type === 'developer') return target.developer ? `开发者：${target.developer}` : '全部开发者'
  if (type === 'project') {
    const project = projects.value.find(item => item.id === target.projectId)
    return `项目：${project?.name || target.projectId || '未指定'}`
  }
  if (type === 'requirement') {
    const requirement = requirements.value.find(item => item.id === target.requirementId)
    return `需求：${requirement?.title || target.requirementId || '未指定'}`
  }
  return '全局产品与工作'
}

function audienceLabel(target: any) {
  if (target.deliveryChannel === 'card') {
    const targetName = target.recipientName || target.cardConversationId || '未指定'
    return target.cardTargetType === 'group' ? `卡片群：${targetName}` : `卡片个人：${targetName}`
  }
  const targetName = target.recipientName || (target.deliveryChannel === 'personal' ? '未指定个人' : '配置的群机器人')
  return target.deliveryChannel === 'personal' ? `个人：${targetName}` : `群：${targetName}`
}

function scheduleLabel(target: any) {
  if (!target.scheduleTime) return '未设置'
  if (target.scheduleCycle === 'weekly') return `每周${weekDays.find(day => day.value === Number(target.scheduleDay || 1))?.label || '周一'} ${target.scheduleTime}`
  if (target.scheduleCycle === 'monthly') return `每月 ${target.scheduleDay || 1} 日 ${target.scheduleTime}`
  if (target.scheduleCycle === 'custom') {
    const days = weekDays.filter(day => (target.scheduleWeekdays || []).map(Number).includes(day.value)).map(day => day.label.replace('周', ''))
    return `${days.length ? days.join('、') : '自定义日期'} ${target.scheduleTime}`
  }
  return `每天 ${target.scheduleTime}`
}

function triggerLabel(target: any) {
  if (target.triggerType === 'event') {
    const labels = triggerEvents.filter(event => (target.triggerEvents || []).includes(event.value)).map(event => event.label)
    return labels.length ? `事件：${labels.join('、')}` : '业务事件'
  }
  return scheduleLabel(target)
}

function rangeLabel(target: any) {
  const labels: Record<string, string> = { today: '今天', last7days: '近 7 天', thisMonth: '本月', lastMonth: '上月' }
  if (target.contentRange === 'custom') return `${target.customRangeStart || '-'} 至 ${target.customRangeEnd || '-'}`
  return labels[target.contentRange || 'today'] || '今天'
}

function sceneLabel(scene: string) {
  const labels: Record<string, string> = { daily: '每日工作同步', weekly: '每周工作与产品动态', milestone: '重要产品事件' }
  return labels[scene || 'daily'] || labels.daily
}

function lastSentLabel(target: any) {
  const raw = String(target.lastSentAt || target.lastSentDate || '')
  if (!raw) return '尚未发送'
  if (raw.includes('-') && raw.length >= 10) return raw.slice(0, 10)
  return raw
}

function contentLabel(types: string[] = []) {
  const normalized = new Set(normalizeContentTypes(types))
  const labels = contentOptions.filter(opt => normalized.has(opt.value)).map(opt => opt.label)
  return labels.length ? labels.join('、') : '未选择'
}

async function loadData() {
  loadingTargets.value = true
  const [rows, projectRows, requirementRows] = await Promise.all([
    api.getNotificationTargets(),
    api.getProjects(),
    api.getRequirements(),
  ])
  targets.value = Array.isArray(rows) ? rows : []
  projects.value = Array.isArray(projectRows) ? projectRows : []
  requirements.value = Array.isArray(requirementRows) ? requirementRows : []
  canManage.value = Boolean(sessionAccess.value?.actions.some(action=>action==='*'||action==='notification.manage')||targets.value.some(target => target.canManage))
  loadingTargets.value = false
  await Promise.all([loadDevelopers(), loadDeliveries()])
}

async function loadDeliveries() {
  const rows: any = await api.getNotificationDeliveries(50)
  deliveries.value = Array.isArray(rows) ? rows : []
}

function readCurrentUser() {
  try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} }
}

async function loadDevelopers() {
  const opts = await api.getDingTalkOptions()
  const normalizePerson = (person: any, role = '') => ({
    name: person.name || person.devOwnerName || person.nick || '',
    userId: person.userId || person.userid || person.dingUserId || '',
    role: person.role || role,
  })
  developers.value = (opts?.developers || [])
    .map((d: any) => normalizePerson(d, 'developer'))
    .filter((d: any) => d.name)
  const allPeople = [...(opts?.users || []), ...(opts?.developers || [])]
  const seen = new Set<string>()
  people.value = allPeople
    .map((person: any) => normalizePerson(person))
    .filter((person: any) => person.name && person.userId && !seen.has(person.userId) && seen.add(person.userId))
}

function selectDeveloperMode(mode: string) {
  form.value.developerMode = mode
  if (mode === 'all') {
    form.value.developer = ''
    form.value.developerUserId = ''
  } else if (mode === 'self') {
    form.value.developer = currentDeveloperName.value || ''
    form.value.developerUserId = currentUserId.value || ''
  } else {
    syncDeveloperUserId()
  }
}

async function previewTarget(target: any) {
  previewOpen.value = true
  previewLoading.value = true
  previewTitle.value = target.name || '通知规则'
  previewMarkdown.value = ''
  const result: any = await api.getNotificationPreview({
    ...target,
    webhook: '',
    secret: '',
  })
  if (result) previewMarkdown.value = result.markdown || ''
  else previewMarkdown.value = '当前账号没有预览权限，或预览生成失败。'
  previewLoading.value = false
}

function syncDeveloperUserId() {
  const dev = developers.value.find(d => d.name === form.value.developer)
  form.value.developerUserId = dev?.userId || ''
}

function syncRecipientName() {
  const person = people.value.find(item => item.userId === form.value.recipientUserId)
  form.value.recipientName = person?.name || ''
}

function applySceneDefaults() {
  const scene = form.value.reportScene || 'daily'
  if (scene === 'weekly') {
    form.value.triggerType = 'schedule'
    form.value.scheduleCycle = 'weekly'
    form.value.scheduleDay = 5
    form.value.contentRange = 'last7days'
  } else if (scene === 'milestone') {
    form.value.triggerType = 'event'
    form.value.contentRange = 'today'
    if (!form.value.triggerEvents?.length) form.value.triggerEvents = ['requirement_created', 'requirement_delivered']
  } else {
    form.value.triggerType = 'schedule'
    form.value.scheduleCycle = 'daily'
    form.value.contentRange = 'today'
  }
}

watch(() => form.value.scope, scope => {
  if (scope === 'developer') {
    if (form.value.targetType !== 'developer') form.value.targetType = 'developer'
    if (!form.value.developerMode) selectDeveloperMode(currentDeveloperName.value ? 'self' : 'custom')
    const types = new Set(form.value.contentTypes || [])
    if (!types.has('workSummary')) {
      types.add('workSummary')
      form.value.contentTypes = Array.from(types)
    }
  }
  if (scope === 'dashboard') {
    if (form.value.targetType === 'developer') {
      form.value.targetType = 'global'
      form.value.developer = ''
      form.value.developerUserId = ''
    }
  }
})

watch(() => form.value.targetType, targetType => {
  if (targetType === 'developer') {
    form.value.scope = 'developer'
  } else if (form.value.scope === 'developer') {
    form.value.scope = 'dashboard'
  }
  if (targetType !== 'project') form.value.projectId = ''
  if (targetType !== 'requirement') form.value.requirementId = ''
})

async function saveTarget() {
  if (!form.value.name) { alert('请填写通知规则名称'); return }
  if (form.value.deliveryChannel === 'group' && !form.value.webhook) { alert('请填写 IT 项目协同空间群机器人 Webhook'); return }
  if (form.value.deliveryChannel === 'personal' && !form.value.recipientUserId) { alert('请选择个人通知接收人'); return }
  if (form.value.targetType === 'project' && !form.value.projectId) { alert('请选择要通知的项目'); return }
  if (form.value.targetType === 'requirement' && !form.value.requirementId) { alert('请选择要通知的需求'); return }
  if (form.value.triggerType === 'event' && !form.value.triggerEvents?.length) { alert('请至少选择一个触发事件'); return }
  if (form.value.triggerType === 'schedule' && form.value.scheduleCycle === 'custom' && !form.value.scheduleWeekdays?.length) { alert('自定义频率至少选择一个发送日'); return }
  form.value.contentTypes = normalizeContentTypes(form.value.contentTypes || [])
  if (!form.value.contentTypes?.length) { alert('请至少选择一个同步内容'); return }
  if (form.value.contentRange === 'custom' && (!form.value.customRangeStart || !form.value.customRangeEnd)) { alert('请补齐自定义开始和结束日期'); return }
  if (form.value.scope === 'developer') {
    if (form.value.developerMode === 'self' && !form.value.developer) {
      alert('当前账号未识别到开发者身份，请选择“指定开发者”')
      return
    }
    if (form.value.developerMode === 'custom' && !form.value.developer) {
      alert('请选择要同步的开发者')
      return
    }
  }
  if (!form.value.ownerUserId) form.value.ownerUserId = currentUserId.value || ''
  if (!form.value.ownerName) form.value.ownerName = currentUser.value?.name || ''
  const saved = editing.value
    ? await api.updateNotificationTarget(editing.value.id, form.value)
    : await api.createNotificationTarget(form.value)
  if (!saved) { alert('保存失败，请确认当前账号有通知配置权限'); return }
  closeModal(); loadData()
}
async function removeTarget(t: any) {
  if (!await showConfirm(`确定删除通知目标「${t.name}」？`)) return
  await api.deleteNotificationTarget(t.id)
  loadData()
}
async function sendNow(t: any) {
  const r = await api.syncNotification({ targetId: t.id })
  await loadDeliveries()
  alert(r ? `已通过当前规则的${t.deliveryChannel === 'personal' ? '个人机器人' : '群机器人'}发送` : '发送失败，请检查当前规则的通知出口和权限')
}

function deliveryTriggerLabel(item: any) {
  if (item.triggerType === 'event') return `事件：${triggerEvents.find(event => event.value === item.eventType)?.label || item.eventType || '业务事件'}`
  if (item.triggerType === 'schedule') return '定时同步'
  return '手动发送'
}

onMounted(() => {
  readCurrentUser()
  window.addEventListener('pm-user-login', ((e: any) => {
    currentUser.value = e.detail || {}
    loadData()
  }) as EventListener)
  loadData()
})
onActivated(loadData)
return { targets, deliveries, developers, people, projects, requirements, loadingTargets, showModal, editing, form, canManage, previewOpen, previewLoading, previewTitle, previewMarkdown, developerModes, weekDays, triggerEvents, contentOptions, contentOptionValues, normalizeContentTypes, currentUser, summaryCards, currentDeveloperName, currentUserId, developerHint, blankForm, openCreate, editTarget, closeModal, scopeLabel, channelLabel, targetTypeLabel, audienceLabel, scheduleLabel, triggerLabel, rangeLabel, sceneLabel, lastSentLabel, contentLabel, loadData, loadDeliveries, readCurrentUser, loadDevelopers, selectDeveloperMode, previewTarget, syncDeveloperUserId, syncRecipientName, applySceneDefaults, saveTarget, removeTarget, sendNow, deliveryTriggerLabel }
}
