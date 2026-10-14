<template>
  <aside class="h-full min-h-0 w-52 shrink-0 overflow-y-auto bg-primary-900 flex flex-col">
    <div class="px-4 pt-5 pb-3">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 bg-accent-500 rounded-lg flex items-center justify-center">
          <FileText class="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 class="text-white font-semibold text-sm">项目协作空间</h1>
          <p class="text-primary-300 text-xs mt-0.5">IT管理平台</p>
        </div>
      </div>
    </div>

    <nav class="flex-1 px-2 py-2">
      <div v-for="(section, sectionIndex) in navSections" :key="section.label" :class="sectionIndex ? 'mt-5 border-t border-primary-700/50 pt-4' : ''">
        <p class="px-3 pb-2 text-[10px] font-semibold tracking-wider text-primary-400">{{ section.label }}</p>
        <div class="space-y-1">
          <div
            v-for="item in section.items"
            :key="item.path"
            @click="navigate(item.path)"
            :class="['nav-item', isActive(item.path) ? 'nav-item-active' : 'nav-item-inactive']"
          >
            <component :is="item.icon" class="w-5 h-5" :class="isActive(item.path) ? 'text-accent-500' : ''" />
            <span>{{ item.label }}</span>
          </div>
        </div>
      </div>
    </nav>

    <div class="px-4 py-4 border-t border-primary-700/50 space-y-2">
      <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary-800/50">
        <div class="w-8 h-8 bg-accent-500 rounded-full flex items-center justify-center text-white text-xs font-bold">管</div>
        <div class="text-sm">
          <p class="text-white text-sm font-medium">{{ currentUser?.name || '钉钉用户' }}</p>
          <p class="text-primary-400 text-xs">{{ roleLabel }}</p>
        </div>
      </div>
      <button v-if="isSuperAdmin" @click="navigate('/system')"
        :class="['w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all', isActive('/system') ? 'bg-white text-accent-600' : 'text-primary-300 hover:bg-primary-800 hover:text-white']">
        <Settings class="w-4 h-4" />
        <span>系统管理</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { SESSION_STORAGE_KEY } from '@/api/session-storage'
import { useRoute, useRouter } from 'vue-router'
import { computed, onMounted, ref } from 'vue'
import { canVisitPage } from '../features/access/session-access'
import {
  LayoutDashboard, ClipboardList, GitBranch,
  UserCircle, History, FileText, BookOpen, BarChart3, Send,
  Settings, MessageSquarePlus, Inbox, Activity, FlaskConical,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const currentUser = ref<any>(null)

const baseNavSections = [
  {
    label: '核心工作',
    items: [
      { path: '/dashboard', label: '成果总览', icon: BarChart3 },
      { path: '/workspace', label: '工作台', icon: UserCircle },
      { path: '/intake', label: '业务协作', icon: MessageSquarePlus },
      { path: '/demand-pool', label: '需求池', icon: Inbox },
      { path: '/requirements', label: '需求列表', icon: ClipboardList },
    ],
  },
    {
    label: '项目管理',
    items: [
      { path: '/products', label: '产品进展', icon: BarChart3 },
      { path: '/poc-workbench', label: 'POC / AI 能力', icon: FlaskConical },
      { path: '/postlaunch/dashboard', label: '上线后管理看板', icon: LayoutDashboard },
      { path: '/postlaunch/operations', label: '上线后运营记录', icon: Activity },
      { path: '/changelog', label: '变更日志', icon: History },
    ],
  },
  {
    label: '资料与配置',
    items: [
      { path: '/notifications', label: '通知配置', icon: Send },
      { path: '/knowledge', label: '知识库', icon: BookOpen },
      { path: '/sprints', label: '迭代管理', icon: GitBranch },
    ],
  },
]

const navSections = computed(() => baseNavSections.map(section=>({...section,items:section.items.filter(item=>canVisitPage(item.path))})).filter(section=>section.items.length))

function isActive(path: string) {
  if (path === '/requirements') return route.path === '/requirements' || route.path.startsWith('/requirements/') && route.path !== '/requirements/kanban'
  if (path === '/requirements/kanban') return route.path === '/requirements/kanban'
  if (path === '/knowledge') return route.path.startsWith('/knowledge')
  if (path === '/intake') return route.path.startsWith('/intake')
  if (path === '/demand-pool') return route.path.startsWith('/demand-pool')
  if (path === '/postlaunch/dashboard') return route.path === '/postlaunch/dashboard' || route.path === '/operations-dashboard'
  if (path === '/postlaunch/operations') return route.path.startsWith('/postlaunch/operations')
  if (path === '/system') return route.path.startsWith('/system')
  return route.path === path
}

function navigate(path: string) {
  void router.push(path).catch(() => {})
}

const roleLabel = computed(() => ({ super_admin: '超级管理员', admin: '管理员', editor: '编辑者', viewer: '查看者' } as any)[currentUser.value?.role] || '钉钉用户')
const isSuperAdmin = computed(() => currentUser.value?.role === 'super_admin')
function readUser() {
  try { currentUser.value = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || '{}') } catch { currentUser.value = null }
}

onMounted(() => {
  readUser()
  window.addEventListener('pm-user-login', readUser)
})
</script>
