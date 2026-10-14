<template>
  <main class="min-h-full overflow-y-auto bg-slate-50 px-4 py-5 sm:px-6 sm:py-8">
    <div class="mx-auto w-full max-w-2xl">
      <div class="mb-5 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600 text-lg font-bold text-white shadow-sm">协</div>
          <div>
            <p class="text-sm font-semibold text-gray-900">业务协作</p>
            <p class="text-[11px] text-gray-500">钉钉卡片反馈与附件补充</p>
          </div>
        </div>
        <span class="rounded-full bg-white px-2.5 py-1 text-[10px] font-medium text-violet-600 shadow-sm">来自钉钉互动卡片</span>
      </div>

      <section v-if="successMessage" class="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm sm:p-8">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-2xl text-emerald-600">✓</div>
        <h1 class="mt-4 text-center text-lg font-semibold text-gray-900">{{ successMessage }}</h1>
        <p class="mt-2 text-center text-sm leading-6 text-gray-500">内容已经同步到对应的共享动态，协作对象会收到更新。</p>
        <div class="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-center">
          <button type="button" class="feishu-btn-primary justify-center" @click="openRequirement">{{ projectId ? '查看产品详情' : '查看需求详情' }}</button>
          <button type="button" class="feishu-btn-ghost justify-center" @click="goBack">返回钉钉</button>
        </div>
      </section>

      <section v-else class="overflow-hidden rounded-2xl border border-violet-100 bg-white shadow-sm">
        <div class="border-b border-violet-100 bg-gradient-to-r from-violet-50 via-white to-blue-50 px-5 py-5 sm:px-7">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold text-violet-600">反馈 / 补充</p>
              <h1 class="mt-1 text-lg font-semibold text-gray-900">把问题、资料或验收意见补充到同一条协作记录</h1>
              <p class="mt-2 text-xs leading-5 text-gray-500">文字、截图和文件会一起留在需求的共享动态中，开发人员和业务人员都能继续查看。</p>
            </div>
            <span v-if="contextLabel" class="rounded-full bg-white px-3 py-1.5 text-[11px] font-medium text-gray-600 shadow-sm">{{ contextLabel }}</span>
          </div>
        </div>

        <div v-if="loading" class="px-5 py-14 text-center text-sm text-gray-400">正在读取协作上下文...</div>
        <div v-else class="space-y-5 px-5 py-5 sm:px-7 sm:py-6">
          <div v-if="errorMessage" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2.5 text-xs leading-5 text-amber-700">{{ errorMessage }}</div>

          <div v-if="requirement" class="rounded-xl border border-gray-100 bg-gray-50/70 px-4 py-3">
            <div class="flex flex-wrap items-center gap-2">
              <span class="rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-semibold text-violet-600">{{ requirement.type || (projectId ? '产品' : '需求') }}</span>
              <span class="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-600">{{ requirement.status || '未设置' }}</span>
            </div>
            <p class="mt-2 text-sm font-semibold text-gray-900">{{ requirement.title || requirement.name }}</p>
            <p class="mt-1 text-[11px] text-gray-500">{{ requirement.projectName || requirement.pname || requirement.name || '未归属项目' }} · {{ projectId ? '产品编号' : '需求编号' }} {{ requirement.id }}</p>
          </div>

          <label v-if="collaborationOptions.length > 1" class="block">
            <span class="form-label">关联协作记录</span>
            <select v-model="selectedCollaborationId" class="feishu-input w-full">
              <option v-for="item in collaborationOptions" :key="item.id" :value="item.id">{{ item.title }} · {{ item.statusLabel }}</option>
            </select>
          </label>

          <label class="block">
            <span class="form-label">评论与补充</span>
            <textarea
              v-model="content"
              rows="6"
              maxlength="10000"
              class="feishu-input w-full resize-y text-sm leading-6"
              placeholder="描述你的疑问、需要配合的内容、上线问题或验收意见；可以直接粘贴图片"
              @paste="handlePaste"
            />
            <span class="mt-1 block text-right text-[10px] text-gray-400">{{ content.length }}/10000</span>
          </label>

          <AttachmentPicker :files="files" @add="addFiles" @remove="removeFile" />

          <div v-if="uploadError" class="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2 text-xs leading-5 text-amber-700">{{ uploadError }}</div>

          <div class="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-[11px] leading-5 text-gray-400">支持图片、视频、PDF、Office、文本和压缩包，单文件最大 50MB。</p>
            <button type="button" class="feishu-btn-primary justify-center px-5" :disabled="saving || !canSubmit" @click="submit">
              {{ saving ? '同步中...' : '发送反馈与附件' }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import AttachmentPicker from '../components/AttachmentPicker.vue'
import { useCollaborationUploadPage } from "../features/system-insights/useCollaborationUploadPage"
const { route, router, requirementId, projectId, activityId, requestedCollaborationId, scopeId, currentUser, requirement, activities, collaborations, selectedCollaborationId, content, files, loading, saving, errorMessage, uploadError, successMessage, collaborationOptions, selectedCollaboration, activityContext, contextLabel, canSubmit, readUser, waitForDingTalkSdk, ensureAuth, loadContext, addFiles, removeFile, handlePaste, submit, openRequirement, goBack }=useCollaborationUploadPage()
</script>
