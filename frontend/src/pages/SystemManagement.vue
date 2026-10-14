<template>
  <div class="page-transition space-y-5">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-gray-900">系统管理</h1>
        <p class="mt-1 text-sm text-gray-500">仅超级管理员可维护人员身份、访问角色、权限模板和回收站。</p>
      </div>
      <button class="feishu-btn-primary" :disabled="saving" @click="save">
        <Save class="h-3.5 w-3.5" /> {{ saving ? '保存中' : '保存配置' }}
      </button>
    </div>

    <div v-if="loading" class="flex h-64 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
    </div>
    <div v-else-if="loadError" class="feishu-card py-12 text-center text-sm text-red-500">{{ loadError }}</div>

    <template v-else>
      <div class="flex gap-2 border-b border-gray-100">
        <button v-for="tab in tabs" :key="tab.key" class="border-b-2 px-3 py-2 text-sm transition-colors"
          :class="activeTab === tab.key ? 'border-accent-500 text-accent-600' : 'border-transparent text-gray-500 hover:text-gray-800'"
          @click="activeTab = tab.key">{{ tab.label }}</button>
      </div>

      <section v-if="activeTab === 'users'" class="grid grid-cols-3 gap-4">
        <div class="feishu-card">
          <h2 class="mb-3 text-sm font-semibold text-gray-900">添加人员</h2>
          <div class="relative mb-3">
            <Search class="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
            <input v-model="keyword" class="feishu-input w-full pl-8" placeholder="搜索钉钉人员" />
          </div>
          <div class="max-h-[560px] space-y-1 overflow-y-auto">
            <div v-for="person in filteredContacts" :key="personKey(person)" class="flex items-center justify-between gap-2 rounded-lg border border-gray-100 px-3 py-2">
              <div class="min-w-0"><p class="truncate text-sm font-medium text-gray-900">{{ person.name }}</p><p class="text-[11px] text-gray-400">{{ person.source || '钉钉通讯录' }}</p></div>
              <button class="rounded-md bg-blue-50 px-2 py-1 text-[11px] font-medium text-blue-600 hover:bg-blue-100" @click="addPerson(person)">加入</button>
            </div>
            <p v-if="filteredContacts.length === 0" class="py-8 text-center text-sm text-gray-400">暂无匹配人员</p>
          </div>
        </div>

        <div class="feishu-card col-span-2">
          <div class="mb-3 flex items-center justify-between"><div><h2 class="text-sm font-semibold text-gray-900">人员与访问角色</h2><p class="mt-1 text-xs text-gray-400">开发者身份只控制负责人可选范围和待办，不代表删除或管理权限。</p></div><span class="text-xs text-gray-400">{{ assignments.length }} 人</span></div>
          <div class="space-y-2">
            <div v-for="item in assignments" :key="personKey(item)" class="rounded-lg border border-gray-100 p-3" :class="!item.enabled ? 'opacity-55' : ''">
              <div class="grid grid-cols-[minmax(140px,1fr)_160px_130px_auto] items-center gap-3">
                <div class="min-w-0"><p class="truncate text-sm font-semibold text-gray-900">{{ item.name }}</p><p class="truncate text-[11px] text-gray-400">{{ item.userId || '未绑定钉钉 UserId' }}</p></div>
                <select v-model="item.accessRole" class="feishu-input h-8 text-xs"><option v-for="role in accessRoles" :key="role.key" :value="role.key">{{ role.label }}</option></select>
                <label class="flex items-center gap-2 text-xs text-gray-600"><input v-model="item.isDeveloper" type="checkbox" class="rounded border-gray-300 text-accent-500" /> 开发者身份</label>
                <div class="flex justify-end gap-2"><button class="text-xs text-gray-500 hover:text-accent-600" @click="item.enabled = !item.enabled">{{ item.enabled ? '停用访问' : '恢复访问' }}</button><button class="text-xs text-red-400 hover:text-red-600" @click="removeAssignment(item)">移除</button></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-else-if="activeTab === 'roles'" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div v-for="role in accessRoles" :key="role.key" class="feishu-card">
            <div class="flex items-start justify-between"><div><h2 class="text-sm font-semibold text-gray-900">{{ role.label }}</h2><p class="mt-1 text-xs text-gray-400">{{ role.description }}</p></div><span class="rounded-full bg-gray-50 px-2 py-0.5 text-[11px] text-gray-500">{{ role.builtIn ? '内置角色' : '自定义角色' }}</span></div>
            <div class="mt-3 flex flex-wrap gap-1.5"><span v-for="page in role.pages" :key="page" class="rounded bg-blue-50 px-2 py-1 text-[11px] text-blue-600">{{ pageLabel(page) }}</span></div>
            <p class="mt-3 text-xs text-gray-500">操作：{{ role.actions?.includes('*') ? '全部系统权限' : (role.actions || []).join('、') || '仅查看' }}</p>
          </div>
        </div>
        <div class="feishu-card">
          <div class="mb-3 flex items-center justify-between"><div><h2 class="text-sm font-semibold text-gray-900">新建自定义角色</h2><p class="mt-1 text-xs text-gray-400">自定义角色不能获得人员角色管理、全局删除或超级管理员权限。</p></div><button class="feishu-btn-primary" @click="addCustomRole">添加角色</button></div>
          <div v-for="(role, index) in customRoles" :key="role.key" class="mb-3 rounded-lg border border-gray-100 p-3">
            <div class="mb-3 grid grid-cols-[180px_1fr_auto] gap-3"><input v-model="role.label" class="feishu-input" placeholder="角色名称" /><input v-model="role.description" class="feishu-input" placeholder="角色说明" /><button class="text-xs text-red-400" @click="customRoles.splice(index, 1)">删除角色</button></div>
            <p class="mb-2 text-xs font-medium text-gray-600">可见页面</p><div class="grid grid-cols-3 gap-2"><label v-for="page in permissionGroups" :key="page.key" class="flex items-center gap-2 text-xs text-gray-600"><input v-model="role.pages" :value="page.key" type="checkbox" class="rounded border-gray-300 text-accent-500" />{{ page.label }}</label></div>
            <p class="mb-2 mt-3 text-xs font-medium text-gray-600">可执行操作</p><div class="grid grid-cols-3 gap-2"><label v-for="action in customActionOptions" :key="action.key" class="flex items-center gap-2 text-xs text-gray-600"><input v-model="role.actions" :value="action.key" type="checkbox" class="rounded border-gray-300 text-accent-500" />{{ action.label }}</label></div>
          </div>
          <p v-if="customRoles.length === 0" class="py-5 text-center text-sm text-gray-400">暂无自定义角色</p>
        </div>
      </section>

      <section v-else-if="activeTab === 'recycle'" class="feishu-card">
        <div class="mb-3 flex items-center justify-between"><div><h2 class="text-sm font-semibold text-gray-900">回收站</h2><p class="mt-1 text-xs text-gray-400">删除的 L1/L2/L3 保留 30 天，可恢复；彻底删除仅限超级管理员。</p></div><button class="feishu-btn-ghost text-xs" @click="loadRecycle">刷新</button></div>
        <div v-if="recycleLoading" class="py-8 text-center text-sm text-gray-400">加载中…</div>
        <div v-else class="space-y-2"><div v-for="item in recycleItems" :key="item.type + item.id" class="flex items-center justify-between gap-3 rounded-lg border border-gray-100 px-3 py-2"><div><p class="text-sm font-medium text-gray-900">{{ item.name }} <span class="ml-1 text-xs font-normal text-gray-400">{{ item.entityType }}</span></p><p class="mt-0.5 text-[11px] text-gray-400">{{ item.deletedAt }} 由 {{ item.deletedByName || '系统' }} 删除，恢复截止 {{ item.expiresAt || '-' }}</p></div><div class="flex gap-2"><button class="text-xs text-accent-600" @click="restoreRecycle(item)">恢复</button><button class="text-xs text-red-400" @click="purgeRecycle(item)">彻底删除</button></div></div><p v-if="recycleItems.length === 0" class="py-8 text-center text-sm text-gray-400">回收站为空</p></div>
      </section>

      <section v-else class="grid grid-cols-2 gap-4">
        <div class="feishu-card"><h2 class="mb-1 text-sm font-semibold text-gray-900">待办与通知策略</h2><p class="mb-3 text-xs text-gray-400">控制需求指派、完成状态和钉钉通知。</p><label class="mb-2 flex items-start gap-3 rounded-lg border border-gray-100 p-3"><input v-model="todoSettings.skipSelfAssignedTodo" type="checkbox" class="mt-1 rounded border-gray-300 text-accent-500" /><span><span class="block text-sm font-medium">操作人等于负责人时不生成待办</span><span class="text-xs text-gray-400">避免给自己重复创建待办。</span></span></label><label class="flex items-start gap-3 rounded-lg border border-gray-100 p-3"><input v-model="todoSettings.notifyRequesterOnOnline" type="checkbox" class="mt-1 rounded border-gray-300 text-accent-500" /><span><span class="block text-sm font-medium">需求上线后通知创建人</span><span class="text-xs text-gray-400">状态变为“已上线”时发送钉钉工作通知。</span></span></label></div>
        <div class="feishu-card"><h2 class="mb-2 text-sm font-semibold text-gray-900">权限规则</h2><ul class="space-y-2 text-sm text-gray-600"><li>• 编辑者只能维护本人创建、负责或被分配的 L2/L3。</li><li>• 编辑者不能修改负责人、提出方，也不能删除或批量删除。</li><li>• L1 大类仅管理员及超级管理员可维护。</li><li>• 开发者身份与访问角色独立维护。</li></ul></div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Save, Search } from 'lucide-vue-next'
import { useSystemManagementPage } from "../features/project-work/useSystemManagementPage"
const { loading, saving, loadError, activeTab, keyword, users, assignments, accessRoles, permissionGroups, customRoles, todoSettings, recycleItems, recycleLoading, tabs, customActionOptions, filteredContacts, personKey, pageLabel, addPerson, removeAssignment, addCustomRole, load, save, loadRecycle, restoreRecycle, purgeRecycle } = useSystemManagementPage()
</script>
