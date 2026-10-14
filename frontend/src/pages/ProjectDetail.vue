<template>
  <div class="space-y-6">
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full" />
    </div>
    <template v-else-if="!project">
      <div class="text-center py-12 text-gray-400">项目未找到</div>
    </template>
    <template v-else>
      <div class="flex items-center gap-3">
        <button @click="router.push('/dashboard')" class="p-2 rounded-lg hover:bg-gray-100">
          <ArrowLeft class="w-5 h-5 text-gray-500" />
        </button>
        <h1 class="text-xl font-bold text-gray-900">{{ project.name }}</h1>
        <span class="font-mono text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">{{ project.currentVersion }}</span>
        <span class="badge bg-green-100 text-green-700 text-xs">进行中</span>
      </div>

      <div class="grid grid-cols-4 gap-4">
        <div class="stat-card">
          <p class="text-xs text-gray-500">总体进度</p>
          <div class="mt-2">
            <div class="flex justify-between items-center text-xs mb-1">
              <span class="font-semibold text-gray-700">{{ project.progress?.label || '项目进度' }}</span>
              <span class="font-bold tabular-nums">{{ projectProgressPercent(project) }}%</span>
            </div>
            <div class="progress-bar h-2.5"><div class="progress-fill" :style="{ width: projectProgressPercent(project) + '%', backgroundColor: projectProgressColor(project) }" /></div>
            <p class="text-[10px] text-gray-400 mt-1 truncate">{{ project.progress?.subLabel || '按 L3 状态自动汇总' }}</p>
          </div>
        </div>
        <div class="stat-card"><p class="text-xs text-gray-500">需求总数</p><p class="text-2xl font-bold text-gray-900 mt-2">{{ reqs.length }}</p></div>
        <div class="stat-card"><p class="text-xs text-gray-500">问题修复</p><p class="text-2xl font-bold text-red-600 mt-2">{{ reqs.filter(r => ['问题修复', 'Bug修复'].includes(r.type)).length }}</p></div>
        <div class="stat-card"><p class="text-xs text-gray-500">已交付</p><p class="text-2xl font-bold text-green-600 mt-2">{{ reqs.filter(r => ['已交付', '已关闭', '已上线'].includes(r.status)).length }}</p></div>
      </div>

      <div class="stat-card">
        <h3 class="font-semibold text-gray-900 flex items-center gap-2 mb-3"><FileText class="w-4 h-4 text-gray-400" />项目描述</h3>
        <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{{ project.description || '暂无描述' }}</p>
      </div>

      <div v-if="canManageOutcome" class="stat-card border border-emerald-100">
        <div class="flex flex-wrap items-start justify-between gap-3"><div><h3 class="font-semibold text-gray-900 flex items-center gap-2"><Target class="w-4 h-4 text-emerald-500" />上线前业务目标确认 <span class="text-[10px] font-normal text-emerald-600 rounded bg-emerald-50 px-1.5 py-0.5">按需</span></h3><p class="mt-1 text-xs leading-5 text-gray-500">L2 项目建立后，可选发给业务负责人确认希望看到的变化；不要求填写数字，也不影响项目流转。</p></div><span v-if="projectOutcomeRequests.length" class="text-[11px] text-emerald-600">{{ projectOutcomeRequests.some(item => item.status === 'submitted') ? '已收到业务确认' : '已发起待填写' }}</span></div>
        <div v-if="canSendProjectOutcome" class="mt-4 rounded-xl border border-emerald-100 bg-emerald-50/50 p-4"><div class="grid grid-cols-1 gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end"><label class="block"><span class="text-xs text-gray-500">业务目标确认人 <span class="font-normal text-gray-400">（默认项目业务负责人）</span></span><select v-if="outcomeContacts.length" v-model="outcomeRecipientUserId" class="feishu-input w-full mt-1"><option value="">请选择联系人</option><option v-for="person in outcomeContacts" :key="person.userId || person.userid || person.name" :value="person.userId || person.userid || person.dingUserId">{{ person.name }}</option></select><input v-else v-model="outcomeRecipientName" class="feishu-input w-full mt-1" maxlength="120" placeholder="填写业务负责人姓名" /></label><button type="button" class="feishu-btn-primary justify-center" :disabled="sendingProjectOutcome || (!outcomeRecipientName && !outcomeRecipientUserId)" @click="sendProjectOutcome">{{ sendingProjectOutcome ? '发送中...' : '发起目标确认' }}</button></div><p class="mt-2 text-[11px] leading-5 text-emerald-700">如果是软件评测、问题修复等类型，可直接跳过这一步。</p></div>
        <div v-else class="mt-4 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2.5 text-xs leading-5 text-gray-500">项目当前状态为「{{ project.status }}」，上线前目标确认仅在正式交付前发起。</div>
        <div v-if="projectOutcomeRequests.length" class="mt-4 space-y-2"><div v-for="outcome in projectOutcomeRequests" :key="outcome.id" class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-emerald-100 bg-white px-3 py-2.5 text-xs"><span class="text-emerald-800">{{ outcome.stageLabel }} · {{ outcome.recipientName || '业务负责人' }} · {{ outcome.statusLabel }}</span><button v-if="outcome.link" type="button" class="text-emerald-700 hover:text-emerald-900" @click="copyProjectOutcomeLink(outcome.link)">复制链接</button></div></div>
      </div>

      <div class="stat-card">
        <h3 class="font-semibold text-gray-900 flex items-center gap-2 mb-4"><FileText class="w-4 h-4 text-gray-400" />交付进度反馈截图</h3>
        <div v-if="project.images?.length" class="flex flex-wrap gap-3">
          <img v-for="(img, i) in project.images" :key="i" :src="imageSrc(img)"
            class="w-24 h-24 rounded-lg object-cover border border-gray-200 cursor-pointer hover:border-accent-300"
            @click="previewImages(project.images, i)" />
        </div>
        <p v-else class="text-sm text-gray-400">暂无截图，可在需求列表中编辑项目后上传。</p>
      </div>

      <ImagePreviewModal v-model="previewModal.open" :images="previewModal.images" :start-index="previewModal.index" />

      <div class="grid grid-cols-3 gap-6">
        <div class="col-span-2 space-y-6">
          <div class="stat-card">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-900 flex items-center gap-2"><GitBranch class="w-4 h-4 text-gray-400" />需求列表</h3>
              <div class="flex bg-gray-100 rounded-lg p-0.5">
                <button @click="activeTab = 'list'" :class="['px-3 py-1 rounded-md text-xs font-medium', activeTab === 'list' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500']">列表</button>
                <button @click="activeTab = 'kanban'" :class="['px-3 py-1 rounded-md text-xs font-medium', activeTab === 'kanban' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500']">看板</button>
              </div>
            </div>
            <!-- List view -->
            <table v-if="activeTab === 'list'" class="w-full text-sm">
              <thead class="bg-gray-50 text-xs text-gray-500">
                <tr><th class="text-left px-3 py-2">标题</th><th class="text-left px-3 py-2">工作类型</th><th class="text-left px-3 py-2">变更对象</th><th class="text-left px-3 py-2">产品价值</th><th class="text-left px-3 py-2">优先级</th><th class="text-left px-3 py-2">状态</th><th class="text-left px-3 py-2">负责人</th></tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="r in reqs" :key="r.id" class="hover:bg-gray-50/50 cursor-pointer" @click="router.push('/requirements/' + r.id)">
                  <td class="px-3 py-2 font-medium text-gray-900">{{ r.title }}</td>
                  <td class="px-3 py-2 text-xs"><span class="badge" :style="{ backgroundColor: typeColor(r.type) + '18', color: typeColor(r.type) }">{{ r.type }}</span></td>
                  <td class="px-3 py-2 text-xs text-gray-600">{{ r.changeObject || '功能' }}</td>
                  <td class="px-3 py-2 text-xs"><span class="font-semibold" :style="{ color: impactColor(r.impactLevel) }">{{ r.impactLevel || '常规' }}</span><span class="ml-1 text-gray-400">· {{ r.workloadLevel || '中' }}工作量</span></td>
                  <td class="px-3 py-2"><span class="text-xs font-bold" :style="{ color: pc(r.priority) }">{{ r.priority }}</span></td>
                  <td class="px-3 py-2"><span class="text-xs px-2 py-0.5 rounded-full" :style="{ backgroundColor: sc(r.status) + '20', color: sc(r.status) }">{{ r.status }}</span></td>
                  <td class="px-3 py-2 text-xs text-gray-500">{{ r.assignee }}</td>
                </tr>
              </tbody>
            </table>
            <!-- Kanban view -->
            <div v-else class="grid grid-cols-4 gap-2">
              <div v-for="col in ['待处理','进行中','待交付','已交付','已关闭']" :key="col" class="bg-gray-50 rounded-lg p-2">
                <p class="text-xs font-semibold text-gray-500 mb-2">{{ col }} ({{ reqs.filter(r => r.status === col).length }})</p>
                <div class="space-y-2">
                  <div v-for="r in reqs.filter(r => r.status === col)" :key="r.id"
                    class="bg-white rounded-md p-2 border border-gray-100 text-xs cursor-pointer hover:border-accent-300"
                    @click="router.push('/requirements/' + r.id)">
                    <p class="font-medium text-gray-900 mb-1">{{ r.title }}</p>
                    <div class="flex items-center gap-2"><span :style="{ color: pc(r.priority) }" class="font-bold">{{ r.priority }}</span><span class="text-gray-400">{{ r.assignee }}</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="space-y-6">
          <div class="stat-card">
            <h3 class="font-semibold text-gray-900 flex items-center gap-2 mb-4"><Clock class="w-4 h-4 text-gray-400" />迭代动态</h3>
            <div class="space-y-0 overflow-hidden" style="max-height: 20em">
              <div v-for="cl in changelogs.slice(0, 8)" :key="cl.id"
                class="border-l-[3px] border-l-transparent hover:border-l-accent-400 pl-3 py-2 hover:bg-gray-50/70 rounded-r-md transition-all">
                <p class="text-xs text-gray-600 truncate">{{ cl.operator }} · {{ cl.changeType }}</p>
                <p class="text-xs text-gray-500 mt-0.5 truncate">{{ cl.requirementTitle }}: {{ cl.oldValue }} → {{ cl.newValue }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ cl.createdAt?.slice(0, 16) }}</p>
              </div>
            </div>
          </div>
          <div class="stat-card">
            <h3 class="font-semibold text-gray-900 flex items-center gap-2 mb-4"><BookOpen class="w-4 h-4 text-gray-400" />知识库</h3>
            <div class="space-y-2">
              <p v-if="docs.length === 0" class="text-xs text-gray-400">暂无文档</p>
              <div v-for="d in docs" :key="d.id" class="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                <div class="w-7 h-7 rounded bg-blue-50 flex items-center justify-center">
                  <component :is="getDocIcon(d.type)" class="w-3.5 h-3.5 text-blue-500" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-gray-900 truncate">{{ d.title }}</p>
                  <p class="text-xs text-gray-400">{{ d.type }}</p>
                </div>
              </div>
            </div>
            <button @click="router.push('/knowledge')" class="mt-3 text-xs text-accent-500 hover:text-accent-600">查看全部 →</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, Clock, GitBranch, BookOpen, FileText, Palette, Database, Target } from 'lucide-vue-next'
import ImagePreviewModal from '../components/ImagePreviewModal.vue'
import { useProjectDetailPage } from "../features/project-work/useProjectDetailPage"
const { route, router, id, loading, project, reqs, changelogs, activeTab, previewModal, currentUser, projectOutcomeRequests, outcomeContacts, outcomeRecipientUserId, outcomeRecipientName, sendingProjectOutcome, canManageOutcome, canSendProjectOutcome, MOCK_DOCS, docs, sc, typeColor, impactColor, pc, projectProgressPercent, projectProgressColor, getDocIcon, imageSrc, previewImages, projectContactById, sendProjectOutcome, copyProjectOutcomeLink } = useProjectDetailPage()
</script>
