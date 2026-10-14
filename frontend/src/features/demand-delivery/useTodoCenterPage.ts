
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/application-api'
export function useTodoCenterPage() {


const route = useRoute()
const router = useRouter()
const todos = ref<any[]>([])
const allTodos = ref<any[]>([])
const requirements = ref<any[]>([])
const projects = ref<any[]>([])
const loading = ref(false)
const activeStatus = ref('all')
const selectedId = computed(() => String(route.query.id || ''))

const statusTabs = [
  { label: '全部', value: 'all' },
  { label: '待处理', value: 'unread' },
  { label: '已查看', value: 'read' },
  { label: '已完成', value: 'done' },
]

const summaryCards = computed(() => [
  { label: '待处理', value: statusCount('unread'), desc: '还未查看的行动事项', className: 'border-rose-100 bg-rose-50/60', valueClass: 'text-rose-600' },
  { label: '已查看', value: statusCount('read'), desc: '看过但尚未完成', className: 'border-blue-100 bg-blue-50/60', valueClass: 'text-blue-600' },
  { label: '行动总量', value: statusCount('unread') + statusCount('read'), desc: '当前仍需处理的待办', className: 'border-amber-100 bg-amber-50/60', valueClass: 'text-amber-600' },
  { label: '已完成', value: statusCount('done'), desc: '已完成的待办事项', className: 'border-emerald-100 bg-emerald-50/60', valueClass: 'text-emerald-600' },
])

function statusLabel(status: string) {
  return ({ unread: '待处理', read: '已查看', done: '已完成' } as Record<string, string>)[status] || status || '未设置'
}

function statusClass(status: string) {
  const base = 'rounded px-1.5 py-0.5 text-[10px] font-semibold'
  if (status === 'unread') return base + ' bg-red-50 text-red-500'
  if (status === 'done') return base + ' bg-emerald-50 text-emerald-600'
  return base + ' bg-blue-50 text-blue-600'
}

function impactClass(level: string) {
  if (level === '核心') return 'rounded bg-rose-50 px-1.5 py-0.5 text-[10px] font-semibold text-rose-600'
  if (level === '重要') return 'rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600'
  return 'rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600'
}

function formatTime(value: string) {
  return value ? String(value).slice(5, 16) : '-'
}

function dueLabel(value: string) {
  return value ? String(value).slice(0, 10) : '未设置'
}

function dueTone(value: string) {
  if (!value) return 'text-gray-400'
  const due = new Date(String(value).replace(/-/g, '/')).getTime()
  if (!Number.isFinite(due)) return 'text-gray-400'
  if (due < Date.now()) return 'text-rose-600'
  if (due <= Date.now() + 7 * 86400000) return 'text-amber-600'
  return 'text-gray-400'
}

function statusCount(status: string) {
  if (status === 'all') return allTodos.value.length
  return allTodos.value.filter(t => t.status === status).length
}

function enrichTodo(todo: any) {
  const requirement = requirements.value.find(item => String(item.id) === String(todo.requirementId)) || {}
  const project = projects.value.find(item => String(item.id) === String(todo.projectId || requirement.projectId)) || {}
  const enriched: any = {
    ...todo,
    requirementType: requirement.type || todo.requirementType || '',
    impactLevel: requirement.impactLevel || todo.impactLevel || '常规',
    workloadLevel: requirement.workloadLevel || todo.workloadLevel || '中',
    priority: requirement.priority || todo.priority || '',
    requirementStatus: requirement.status || todo.requirementStatus || '',
    expectedDeliveryTime: requirement.expectedDeliveryTime || todo.expectedDeliveryTime || '',
    projectName: todo.projectName || requirement.projectName || requirement.pname || project.name || '未归属项目',
  }
  enriched.dueTone = dueTone(enriched.expectedDeliveryTime)
  return enriched
}

const groupedTodos = computed(() => {
  const groups = new Map<string, any[]>()
  for (const todo of todos.value) {
    const name = todo.projectName || '未归属项目'
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name)!.push(todo)
  }
  return Array.from(groups.entries()).map(([name, items]) => ({ name, items }))
})

async function loadTodos() {
  loading.value = true
  const [all, filtered, reqs, projectRows] = await Promise.all([
    api.getTodos('all'),
    api.getTodos(activeStatus.value),
    api.getRequirements({}),
    api.getProjects(),
  ])
  if (reqs) requirements.value = reqs
  if (projectRows) projects.value = projectRows
  if (all) allTodos.value = all.map(enrichTodo)
  if (filtered) todos.value = filtered.map(enrichTodo)
  loading.value = false
  if (selectedId.value) {
    const hit = todos.value.find(t => String(t.id) === selectedId.value)
    if (hit?.status === 'unread') markRead(hit)
  }
}

async function markRead(todo: any) {
  const saved = await api.markTodoRead(todo.id)
  if (saved) {
    todo.status = saved.status
    todo.readAt = saved.readAt
    const all = allTodos.value.find(item => item.id === todo.id)
    if (all) { all.status = saved.status; all.readAt = saved.readAt }
    window.dispatchEvent(new CustomEvent('pm-todo-updated'))
  }
}

async function markDone(todo: any) {
  const saved = await api.markTodoDone(todo.id)
  if (saved) {
    todo.status = saved.status
    todo.doneAt = saved.doneAt
    window.dispatchEvent(new CustomEvent('pm-todo-updated'))
    await loadTodos()
  }
}

async function openRequirement(todo: any) {
  if (todo.status === 'unread') await markRead(todo)
  router.push({ path: '/requirements/' + todo.requirementId, query: { from: 'todos', todoId: todo.id } })
}

watch(() => [route.query.id, route.query.status], () => {
  if (route.query.status && statusTabs.some(item => item.value === route.query.status)) {
    activeStatus.value = String(route.query.status)
  }
  if (selectedId.value) loadTodos()
})

onMounted(loadTodos)
return { route, router, todos, allTodos, requirements, projects, loading, activeStatus, selectedId, statusTabs, summaryCards, statusLabel, statusClass, impactClass, formatTime, dueLabel, dueTone, statusCount, enrichTodo, groupedTodos, loadTodos, markRead, markDone, openRequirement }
}
