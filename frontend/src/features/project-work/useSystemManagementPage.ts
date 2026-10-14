
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api/application-api'
import { showConfirm } from '../../utils/feedback'
export function useSystemManagementPage() {


const loading = ref(true), saving = ref(false), loadError = ref('')
const activeTab = ref('users'), keyword = ref('')
const users = ref<any[]>([]), assignments = ref<any[]>([]), accessRoles = ref<any[]>([]), permissionGroups = ref<any[]>([]), customRoles = ref<any[]>([])
const todoSettings = ref({ skipSelfAssignedTodo: false, notifyRequesterOnOnline: true })
const recycleItems = ref<any[]>([]), recycleLoading = ref(false)
const tabs = [{ key: 'users', label: '人员与角色' }, { key: 'roles', label: '角色权限' }, { key: 'recycle', label: '回收站' }, { key: 'policies', label: '系统策略' }]
const customActionOptions = [{ key: 'project.create', label: '新增项目' }, { key: 'project.update.own', label: '修改本人项目' }, { key: 'requirement.create', label: '新增需求' }, { key: 'requirement.update.own', label: '修改本人需求' }, { key: 'sprint.update.own', label: '维护本人迭代' }, { key: 'notification.self', label: '个人通知配置' }, { key: 'operation.view', label: '查看操作记录' }]

const filteredContacts = computed(() => { const q = keyword.value.trim().toLowerCase(); return users.value.filter(u => u?.name && (!q || String(u.name).toLowerCase().includes(q))).slice(0, 80) })
const personKey = (person: any) => person.userId || person.userid || person.dingUserId || person.name
const pageLabel = (key: string) => permissionGroups.value.find(item => item.key === key)?.label || key

function addPerson(person: any) { if (assignments.value.some(item => personKey(item) === personKey(person) || item.name === person.name)) return; assignments.value.push({ name: person.name, userId: person.userId || person.userid || person.dingUserId || '', accessRole: 'viewer', isDeveloper: false, enabled: true }) }
async function removeAssignment(item: any) { if (!await showConfirm(`移除「${item.name}」的系统访问配置？历史记录不会删除。`)) return; assignments.value = assignments.value.filter(row => row !== item) }
function addCustomRole() { const key = `custom_${Date.now().toString(36)}`; customRoles.value.push({ key, label: '新角色', description: '', pages: [], actions: [] }) }

async function load() { loading.value = true; loadError.value = ''; const cfg: any = await api.getPersonnelConfig(); if (!cfg) { loadError.value = '没有系统管理权限，或请在钉钉内重新登录。'; loading.value = false; return }; users.value = cfg.users || []; assignments.value = (cfg.assignments || []).map((item: any) => ({ ...item })); accessRoles.value = cfg.accessRoles || []; permissionGroups.value = cfg.permissionGroups || []; customRoles.value = (cfg.customRoles || []).map((item: any) => ({ ...item, pages: [...(item.pages || [])], actions: [...(item.actions || [])] })); todoSettings.value = { ...todoSettings.value, ...(cfg.todoSettings || {}) }; loading.value = false }
async function save() { saving.value = true; const result: any = await api.updatePersonnelConfig({ assignments: assignments.value, customRoles: customRoles.value, todoSettings: todoSettings.value }); saving.value = false; if (!result) { alert('保存失败，请确认仍以超级管理员身份登录'); return }; await load(); alert('人员、角色与系统策略已保存。相关人员下次请求会按新权限生效。') }
async function loadRecycle() { recycleLoading.value = true; const rows: any = await api.getRecycleBin(); recycleItems.value = rows || []; recycleLoading.value = false }
async function restoreRecycle(item: any) { if (!await showConfirm(`恢复「${item.name}」？`)) return; const result = await api.restoreRecycleItem(item.type, item.id); if (!result) { alert('恢复失败，请先恢复上级记录或确认未超过 30 天'); return }; await loadRecycle() }
async function purgeRecycle(item: any) { if (!await showConfirm(`彻底删除「${item.name}」？此操作不可恢复。`)) return; const result = await api.purgeRecycleItem(item.type, item.id); if (!result) { alert('彻底删除失败，请先处理下级记录'); return }; await loadRecycle() }
onMounted(async () => { await load(); await loadRecycle() })
return { loading, saving, loadError, activeTab, keyword, users, assignments, accessRoles, permissionGroups, customRoles, todoSettings, recycleItems, recycleLoading, tabs, customActionOptions, filteredContacts, personKey, pageLabel, addPerson, removeAssignment, addCustomRole, load, save, loadRecycle, restoreRecycle, purgeRecycle }
}
