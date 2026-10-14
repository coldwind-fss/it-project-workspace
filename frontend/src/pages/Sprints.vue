<template>
  <div class="page-transition space-y-6">
    <div v-if="currentSprint" class="bg-white rounded-xl border border-gray-100 p-6">
      <div class="flex items-center justify-between mb-5">
        <div>
          <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <h3 class="font-semibold text-gray-900">当前迭代</h3>
            <span class="badge bg-green-50 text-green-600 border border-green-100">进行中</span>
          </div>
          <div class="flex items-center gap-4 mt-2">
            <span class="text-lg font-bold text-gray-900">{{ currentSprint.name }}</span>
            <span class="text-sm text-gray-400 flex items-center gap-1">
              <Calendar class="w-3.5 h-3.5" />
              {{ currentSprint.startDate }} ~ {{ currentSprint.endDate }}
            </span>
          </div>
        </div>
        <div class="text-right">
          <div class="text-2xl font-bold text-accent-500">{{ currentSprint.completedTasks }}/{{ currentSprint.totalTasks }}</div>
          <p class="text-xs text-gray-400">已完成任务</p>
        </div>
      </div>
      <div class="progress-bar h-3 mb-6">
        <div class="progress-fill bg-accent-500" :style="{ width: (currentSprint.totalTasks > 0 ? currentSprint.completedTasks / currentSprint.totalTasks * 100 : 0) + '%' }" />
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <h4 class="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <CheckCircle2 class="w-4 h-4 text-green-500" /> 迭代内需求 ({{ sprintReqs.length }})
          </h4>
          <div class="space-y-2">
            <div v-for="r in sprintReqs" :key="r.id"
              class="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2.5 cursor-pointer hover:bg-accent-50/50 transition-all"
              @click="router.push('/requirements/' + r.id)"
            >
              <div class="flex items-center gap-2.5">
                <span :class="['w-2 h-2 rounded-full', ['已交付', '已关闭', '已上线'].includes(r.status) ? 'bg-green-500' : ['进行中', '开发中', '联调中', '测试中', '迭代中', '待交付', '待上线'].includes(r.status) ? 'bg-amber-500' : 'bg-gray-300']" />
                <span class="text-sm text-gray-700">{{ r.title }}</span>
              </div>
              <span class="badge text-[10px]" :style="{ backgroundColor: (['问题修复', 'Bug修复'].includes(r.type) ? '#ef4444' : '#3b82f6') + '15', color: ['问题修复', 'Bug修复'].includes(r.type) ? '#ef4444' : '#3b82f6' }">{{ r.type }}</span>
            </div>
          </div>
        </div>
        <div>
          <h4 class="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <AlertTriangle class="w-4 h-4 text-amber-500" /> 即将到来
          </h4>
          <div class="flex items-center justify-center h-[calc(100%-24px)] bg-gray-50 rounded-lg">
            <p class="text-xs text-gray-400">距离迭代结束还有 <strong class="text-gray-600" v-if="currentSprint.endDate">{{ daysLeft }}</strong> 天</p>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-100 p-6">
      <div class="flex items-center justify-between mb-5">
        <h3 class="font-semibold text-gray-900 flex items-center gap-2">
          <GitBranch class="w-4 h-4 text-gray-400" /> 版本发布历史
        </h3>
      </div>
      <div class="space-y-4">
        <div v-for="l in releases" :key="l.id" class="flex gap-4 p-4 bg-gray-50 rounded-xl hover:bg-accent-50/20 transition-all">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            :style="{ backgroundColor: getProjectColor(l.projectId) + '15' }">
            <Star class="w-5 h-5" :style="{ color: getProjectColor(l.projectId) }" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 mb-1">
              <span class="font-mono font-bold text-gray-900">{{ l.version }}</span>
              <span :class="['badge text-white text-[10px]', l.type === 'hotfix' ? 'bg-red-500' : l.type === 'patch' ? 'bg-amber-500' : 'bg-accent-500']">
                {{ l.type === 'hotfix' ? '紧急修复' : l.type === 'patch' ? '补丁' : '常规版本' }}
              </span>
              <span class="text-xs text-gray-400">{{ l.projectName }}</span>
            </div>
            <div class="flex flex-wrap gap-2 mt-2">
              <span v-for="(item, i) in safeSummary(l.summary)" :key="i"
                class="inline-flex items-center gap-1 text-xs text-gray-600 bg-white px-2.5 py-1 rounded-md border border-gray-100">
                <span class="w-1.5 h-1.5 rounded-full bg-green-500" /> {{ item }}
              </span>
            </div>
            <p class="text-xs text-gray-400 mt-2 flex items-center gap-1">
              <Clock class="w-3 h-3" /> {{ l.releaseDate }} 发布
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { GitBranch, Calendar, CheckCircle2, AlertTriangle, Star, Clock } from 'lucide-vue-next'
import { useSprintsPage } from "../features/project-work/useSprintsPage"
const { router, currentSprint, sprints, releases, sprintReqs, projects, projectColors, getProjectColor, daysLeft, safeSummary } = useSprintsPage()
</script>
