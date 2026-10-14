import { SESSION_STORAGE_KEY } from '@/api/session-storage'

import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
import { hasAction } from '../access/session-access'
import type { Project, Requirement, Changelog, KnowledgeDoc } from '../../types'
import { FileText, BookOpen, Palette, Database } from 'lucide-vue-next'
export function useProjectDetailPage() {


const route = useRoute()
const router = useRouter()
const id = route.params.id as string
const loading = ref(true)
const project = ref<Project | null>(null)
const reqs = ref<Requirement[]>([])
const changelogs = ref<Changelog[]>([])
const activeTab = ref<'list' | 'kanban'>('list')
const previewModal = ref({ images: [] as any[], index: 0, open: false })
const currentUser = ref<any>({})
const projectOutcomeRequests = ref<any[]>([])
const outcomeContacts = ref<any[]>([])
const outcomeRecipientUserId = ref('')
const outcomeRecipientName = ref('')
const sendingProjectOutcome = ref(false)
const canManageOutcome = computed(() => hasAction('demand_pool.manage'))
const canSendProjectOutcome = computed(() => !!project.value && !['已上线', '已关闭', '已归档'].includes(String(project.value.status || '')))

const MOCK_DOCS: KnowledgeDoc[] = [
  { id: 'd1', title: 'API文档', type: 'api', projectId: 'p1', projectName: '订单管理系统', url: '#', description: 'Swagger 3.0', uploadedBy: '张三', createdAt: '2025-06-15' },
]
const docs = ref(MOCK_DOCS.filter(d => d.projectId === id))

function sc(s: string) {
  const m: Record<string, string> = {
    '待处理': '#64748b', '进行中': '#3b82f6', '待交付': '#f59e0b', '已交付': '#10b981',
    '待评估': '#9ca3af', '已排期': '#3b82f6', '已立项': '#3b82f6', '需求确认中': '#6366f1',
    '设计中': '#8b5cf6', '开发中': '#f59e0b', '联调中': '#06b6d4', '测试中': '#a855f7',
    '迭代中': '#0ea5e9', '待上线': '#14b8a6', '已上线': '#10b981', '维护中': '#64748b',
    '暂停中': '#f97316', '已关闭': '#6b7280', '已归档': '#94a3b8',
  }
  return m[s] || '#9ca3af'
}
function typeColor(type: string) {
  const m: Record<string, string> = {
    '业务确认': '#0ea5e9', '产品设计': '#8b5cf6', '技术建设': '#64748b',
    '新增功能': '#2563eb', '功能优化': '#d97706', '问题修复': '#dc2626', '验证交付': '#0f766e',
  }
  return m[type] || '#6b7280'
}
function impactColor(level?: string) {
  return ({ '核心': '#dc2626', '重要': '#d97706', '常规': '#64748b' } as Record<string, string>)[level || ''] || '#64748b'
}
function pc(p: string) { const m: Record<string, string> = { P0: '#ef4444', P1: '#f59e0b', P2: '#3b82f6', P3: '#9ca3af', P4: '#cbd5e1' }; return m[p] || '#9ca3af' }
function projectProgressPercent(p: any) {
  const val = p?.progress?.progress ?? p?.progress?.currentProgress ?? 0
  return Math.max(0, Math.min(100, Math.round(Number(val) || 0)))
}
function projectProgressColor(p: any) {
  if (p?.progress?.mode === 'released' || projectProgressPercent(p) >= 100) return '#10b981'
  if (p?.progress?.mode === 'empty') return '#d1d5db'
  if ((p?.progress?.subLabel || '').includes('暂停')) return '#f97316'
  if (projectProgressPercent(p) >= 70) return '#14b8a6'
  return p?.categoryColor || '#3b82f6'
}
function getDocIcon(type: string) {
  const icons: Record<string, any> = { api: FileText, prd: BookOpen, design: Palette, database: Database }
  return icons[type] || FileText
}
function imageSrc(img: any) { return img?.data || img }
function previewImages(imgs: any[], index = 0) { previewModal.value = { images: imgs || [], index, open: true } }
function projectContactById(userId: string) { return outcomeContacts.value.find(person => (person.userId || person.userid || person.dingUserId) === userId) || {} }
async function sendProjectOutcome() {
  if (!project.value || sendingProjectOutcome.value) return
  const person = projectContactById(outcomeRecipientUserId.value)
  const recipientName = String(person.name || outcomeRecipientName.value || project.value.businessOwner || '').trim()
  if (!recipientName) { alert('请指定业务目标确认人'); return }
  sendingProjectOutcome.value = true
  const result: any = await api.createProjectOutcomeRequest(id, { stage: 'goal', recipientUserId: outcomeRecipientUserId.value, recipientName })
  sendingProjectOutcome.value = false
  if (!result?.id) { alert(result?.error || '目标确认链接发送失败，请检查联系人和权限'); return }
  if (!projectOutcomeRequests.value.some(item => item.id === result.id)) projectOutcomeRequests.value.unshift(result)
  alert(result.notificationStatus === 'failed' ? '链接已生成，但钉钉发送失败，可复制链接手动发送' : '上线前目标确认链接已发送')
}
async function copyProjectOutcomeLink(link: string) { if (!link) return; try { await navigator.clipboard.writeText(link); alert('链接已复制') } catch { alert(link) } }

onMounted(async () => {
  if (!id) return
  try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = {} }
  const [p, r, c] = await Promise.all([
    api.getProject(id),
    api.getRequirements({ projectId: id }),
    api.getChangelogs(),
  ])
  if (p) project.value = p
  if (r) reqs.value = r
  if (c) changelogs.value = c
  const outcomes: any = await api.getProjectOutcomeRequests(id)
  if (Array.isArray(outcomes)) projectOutcomeRequests.value = outcomes
  outcomeRecipientName.value = String((p as any)?.businessOwner || '').trim()
  const contacts: any = await api.getDingTalkOptions()
  if (Array.isArray(contacts?.users)) {
    outcomeContacts.value = contacts.users
    const matched = outcomeContacts.value.find(person => String(person.name || '').trim() === outcomeRecipientName.value)
    if (matched) outcomeRecipientUserId.value = matched.userId || matched.userid || matched.dingUserId || ''
  }
  loading.value = false
})
return { route, router, id, loading, project, reqs, changelogs, activeTab, previewModal, currentUser, projectOutcomeRequests, outcomeContacts, outcomeRecipientUserId, outcomeRecipientName, sendingProjectOutcome, canManageOutcome, canSendProjectOutcome, MOCK_DOCS, docs, sc, typeColor, impactColor, pc, projectProgressPercent, projectProgressColor, getDocIcon, imageSrc, previewImages, projectContactById, sendProjectOutcome, copyProjectOutcomeLink }
}
