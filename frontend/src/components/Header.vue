<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 flex-shrink-0">
    <div>
      <h2 class="text-lg font-semibold text-gray-900">{{ title }}</h2>
      <p class="text-xs text-gray-500 mt-0.5">{{ desc }}</p>
    </div>
    <div class="flex items-center gap-3">
      <a
        href="https://github.com/coldwind-fss/it-project-workspace#readme"
        target="_blank"
        rel="noopener noreferrer"
        class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-100"
        title="查看项目说明与工程文档"
      >
        项目说明
      </a>
      <div class="relative">
        <Search class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="搜索需求、项目..."
          class="w-48 xl:w-56 pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 transition-all duration-150"
        />
      </div>
      <button @click="router.push({ path: '/workspace', query: { focus: 'pending' } })" class="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all" title="待我处理">
        <Bell class="w-5 h-5" />
        <span v-if="todoUnread > 0" class="absolute -right-1 -top-1 min-w-[18px] rounded-full bg-red-500 px-1 text-center text-[10px] font-bold leading-[18px] text-white">
          {{ todoUnread > 99 ? '99+' : todoUnread }}
        </span>
      </button>
      <div @click="router.push('/operations')" class="flex items-center gap-2 pl-2 border-l border-gray-100 cursor-pointer hover:bg-gray-50 rounded-lg pr-2 py-1 transition-colors" title="查看操作记录">
        <div class="w-7 h-7 rounded-full bg-accent-50 text-accent-500 flex items-center justify-center text-xs font-bold">
          {{ currentUser?.name?.[0] || '钉' }}
        </div>
        <div class="leading-tight">
          <p class="text-xs font-medium text-gray-700">{{ currentUser?.name || loginLabel }}</p>
          <p class="text-[10px] text-gray-400">{{ roleLabel }}</p>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { SESSION_STORAGE_KEY } from '@/api/session-storage'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Bell } from 'lucide-vue-next'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const currentUser = ref<any>(null)
const loginLabel = ref('未识别')
const todoUnread = ref(0)

const pageTitles: Record<string, string> = {
  '/dashboard': '成果总览',
  '/products': '产品进展',
  '/poc-workbench': 'POC / AI 能力',
  '/requirements': '需求管理',
  '/changelog': '需求变更日志',
  '/sprints': '迭代管理',
  '/workspace': '工作台',
  '/intake': '业务协作',
  '/notifications': '通知配置',
  '/operations': '操作记录',
  '/system': '系统管理',
}
const pageDescs: Record<string, string> = {
  '/dashboard': '',
  '/products': '按 L2 产品聚合变化、当前工作与共享动态',
  '/poc-workbench': '开发验证、模型经验与可复用能力沉淀',
  '/requirements': '所有需求统一管理，全生命周期追踪',
  '/changelog': '每一次变更都有迹可循',
  '/sprints': '版本迭代规划与发布记录',
  '/workspace': '个人任务与快捷操作',
  '/intake': '业务协作者提交、反馈与处理回流',
  '/notifications': '钉钉群机器人、定时同步与主动推送',
  '/operations': 'L1/L2/L3 增删改审计与溯源',
  '/system': '人员配置、角色权限与系统级设置',
}

const title = computed(() => route.path.startsWith('/requirements/') ? 'L3需求详情' : (pageTitles[route.path] || '项目大盘'))
const desc = computed(() => route.path.startsWith('/requirements/') ? '需求详情、共享动态与开发/业务双方讨论' : (pageDescs[route.path] || ''))
const roleLabel = computed(() => ({ super_admin: '超级管理员', admin: '管理员', editor: '编辑者', viewer: '查看者' } as any)[currentUser.value?.role] || '钉钉用户')

function waitForDingTalkSdk(maxMs = 3000): Promise<any> {
  return new Promise(resolve => {
    const started = Date.now()
    const tick = () => {
      const dd = (window as any).dd
      if (dd) resolve(dd)
      else if (Date.now() - started >= maxMs) resolve(null)
      else window.setTimeout(tick, 120)
    }
    tick()
  })
}

function readCorpId(cfg: any) {
  const search = new URLSearchParams(window.location.search)
  const hashQuery = window.location.hash.includes('?') ? window.location.hash.split('?')[1] : ''
  const hashSearch = new URLSearchParams(hashQuery)
  const corpId = cfg?.corpId || search.get('corpId') || search.get('corpid') || hashSearch.get('corpId') || hashSearch.get('corpid') || localStorage.getItem('pm-corp-id') || ''
  if (corpId) localStorage.setItem('pm-corp-id', corpId)
  return corpId
}

async function requestDingTalkAuth(dd: any, corpId: string) {
  const doLogin = () => {
    const payload: any = {
      onSuccess: async (res: any) => {
        const code = res?.code
        if (!code) { loginLabel.value = '免登失败'; return }
        const login: any = await api.loginWithDingTalk(code)
        if (login?.user) {
          currentUser.value = login.user
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(login.user))
          window.dispatchEvent(new CustomEvent('pm-user-login', { detail: login.user }))
        } else {
          loginLabel.value = '免登失败'
        }
      },
      onFail: (err: any) => {
        console.warn('DingTalk auth failed:', err)
        loginLabel.value = '免登失败'
      },
    }
    if (corpId) payload.corpId = corpId
    dd.runtime.permission.requestAuthCode(payload)
  }
  if (typeof dd.ready === 'function') dd.ready(doLogin)
  else doLogin()
}

async function tryDingTalkLogin() {
  const cached = localStorage.getItem(SESSION_STORAGE_KEY)
  if (cached) {
    try { currentUser.value = JSON.parse(cached) } catch {}
  }
  if (!/DingTalk/i.test(navigator.userAgent)) {
    loginLabel.value = '浏览器访问'
    return
  }
  const cfg: any = await api.getDingTalkConfig()
  const dd = await waitForDingTalkSdk()
  const corpId = readCorpId(cfg)
  if (!dd?.runtime?.permission?.requestAuthCode) {
    loginLabel.value = cfg?.configured ? '浏览器访问' : '待配置'
    return
  }
  loginLabel.value = corpId ? '钉钉识别中' : '钉钉待授权'
  await requestDingTalkAuth(dd, corpId)
}

async function loadTodoUnread() {
  const r: any = await api.getTodoUnreadCount()
  todoUnread.value = Number(r?.count || 0)
}

onMounted(() => {
  tryDingTalkLogin().finally(loadTodoUnread)
  window.addEventListener('pm-user-login', loadTodoUnread)
  window.addEventListener('pm-todo-updated', loadTodoUnread)
})
</script>
