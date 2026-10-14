<template>
  <div class="flex h-full min-h-0 flex-col bg-gray-50">
    <div class="border-b border-gray-200 bg-white px-5 py-4">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <FlaskConical class="h-5 w-5 text-violet-600" />
            <h1 class="text-lg font-semibold text-gray-900">POC 与 AI 能力工作台</h1>
          </div>
          <p class="mt-1 text-xs text-gray-500">把开发过程中零散的验证、模型经验和可复用方法沉淀成可追踪记录。</p>
        </div>
        <button type="button" class="inline-flex items-center gap-1.5 rounded-lg bg-accent-500 px-3 py-2 text-sm font-medium text-white hover:bg-accent-600" @click="startCreate">
          <Plus class="h-4 w-4" />
          新建记录
        </button>
      </div>
      <div class="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
        <div class="rounded-lg border border-violet-100 bg-violet-50 px-3 py-2.5"><p class="text-[11px] text-violet-600">POC 验证</p><p class="mt-0.5 text-xl font-semibold text-violet-800">{{ countByType('poc') }}</p></div>
        <div class="rounded-lg border border-cyan-100 bg-cyan-50 px-3 py-2.5"><p class="text-[11px] text-cyan-600">AI 能力</p><p class="mt-0.5 text-xl font-semibold text-cyan-800">{{ countByType('ai_capability') }}</p></div>
        <div class="rounded-lg border border-amber-100 bg-amber-50 px-3 py-2.5"><p class="text-[11px] text-amber-600">进行中</p><p class="mt-0.5 text-xl font-semibold text-amber-800">{{ records.filter(item => ['planned', 'in_progress'].includes(item.status)).length }}</p></div>
        <div class="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2.5"><p class="text-[11px] text-emerald-600">已完成 / 可复用</p><p class="mt-0.5 text-xl font-semibold text-emerald-800">{{ records.filter(item => item.status === 'completed' || item.recordType === 'ai_capability').length }}</p></div>
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden p-4 xl:flex-row">
      <section class="flex min-h-0 w-full flex-col rounded-xl border border-gray-200 bg-white xl:w-[420px] xl:shrink-0">
        <div class="border-b border-gray-100 p-3">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input v-model="keyword" class="w-full rounded-lg border border-gray-200 py-2 pl-9 pr-3 text-sm outline-none focus:border-accent-500" placeholder="搜索标题、目标或结论" />
          </div>
          <div class="mt-2 flex gap-2">
            <select v-model="typeFilter" class="min-w-0 flex-1 rounded-lg border border-gray-200 px-2 py-2 text-xs text-gray-600 outline-none">
              <option value="">全部类型</option>
              <option value="poc">POC 验证</option>
              <option value="ai_capability">AI 能力</option>
            </select>
            <select v-model="statusFilter" class="min-w-0 flex-1 rounded-lg border border-gray-200 px-2 py-2 text-xs text-gray-600 outline-none">
              <option value="">全部状态</option>
              <option v-for="item in options.statuses" :key="item.key" :value="item.key">{{ item.label }}</option>
            </select>
          </div>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto p-2">
          <div v-if="loading" class="p-6 text-center text-sm text-gray-400">正在加载记录...</div>
          <div v-else-if="!filteredRecords.length" class="m-2 rounded-lg border border-dashed border-gray-200 p-6 text-center text-sm text-gray-400">
            暂无匹配记录<br /><span class="mt-1 inline-block text-xs">可以从一次开发验证或一个模型经验开始沉淀</span>
          </div>
          <button v-for="record in filteredRecords" :key="record.id" type="button" class="mb-2 w-full rounded-lg border p-3 text-left transition-colors" :class="selectedId === record.id ? 'border-accent-400 bg-accent-50/50' : 'border-gray-100 bg-white hover:border-gray-300 hover:bg-gray-50'" @click="selectRecord(record)">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-gray-900">{{ record.title }}</p>
                <div class="mt-1 flex flex-wrap items-center gap-1.5 text-[11px]">
                  <span class="rounded px-1.5 py-0.5" :class="record.recordType === 'ai_capability' ? 'bg-cyan-50 text-cyan-700' : 'bg-violet-50 text-violet-700'">{{ record.recordTypeLabel }}</span>
                  <span class="rounded bg-gray-100 px-1.5 py-0.5 text-gray-600">{{ record.statusLabel }}</span>
                  <span v-if="record.legacy" class="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700">历史需求池</span>
                </div>
              </div>
              <ChevronRight class="mt-1 h-4 w-4 shrink-0 text-gray-300" />
            </div>
            <p v-if="record.projectName || record.requirementTitle || record.demandTitle" class="mt-2 truncate text-[11px] text-gray-500">{{ relatedLabel(record) }}</p>
            <p class="mt-1 text-[11px] text-gray-400">{{ record.sourceLabel }} · {{ formatTime(record.updatedAt || record.createdAt) }}</p>
          </button>
        </div>
      </section>

      <section class="min-h-0 min-w-0 flex-1 overflow-y-auto rounded-xl border border-gray-200 bg-white">
        <div v-if="!isCreating && !selectedRecord" class="flex h-full min-h-[420px] items-center justify-center p-8 text-center text-gray-400">
          <div><FlaskConical class="mx-auto h-12 w-12 text-gray-200" /><p class="mt-3 text-sm">选择一条记录查看详情</p><p class="mt-1 text-xs">或新建一条开发过程中的 POC / AI 能力记录</p></div>
        </div>
        <form v-else class="p-4 md:p-5" @submit.prevent="saveRecord">
          <div class="flex flex-wrap items-start justify-between gap-3 border-b border-gray-100 pb-4">
            <div>
              <p class="text-xs font-medium text-violet-600">{{ isCreating ? '新建沉淀记录' : (form.legacy ? '历史需求池记录 · 只读' : '记录详情') }}</p>
              <h2 class="mt-1 text-lg font-semibold text-gray-900">{{ isCreating ? '记录一次 POC 或 AI 能力' : form.title }}</h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <button v-if="!isCreating && form.recordType === 'poc'" type="button" class="inline-flex items-center gap-1.5 rounded-lg border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs font-medium text-cyan-700 hover:bg-cyan-100" @click="deriveCapability">
                <BrainCircuit class="h-4 w-4" /> 沉淀为 AI 能力
              </button>
              <button v-if="!isCreating && form.requirementId" type="button" class="rounded-lg border border-gray-200 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50" @click="router.push('/requirements/' + form.requirementId)">打开关联需求</button>
              <button v-if="!isCreating && form.demandId" type="button" class="rounded-lg border border-gray-200 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50" @click="router.push('/demand-pool')">打开需求池</button>
            </div>
          </div>

          <div v-if="notice" class="mt-3 rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">{{ notice }}</div>
          <div v-if="errorMessage" class="mt-3 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-700">{{ errorMessage }}</div>
          <div v-if="form.legacy" class="mt-3 rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-800">这条记录来自需求池历史 POC，只在这里统一展示；如需继续沉淀，请新建独立记录或点击“沉淀为 AI 能力”。</div>

          <fieldset :disabled="!!form.legacy || saving" class="mt-4 space-y-4">
            <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <label class="xl:col-span-2"><span class="field-label">记录名称 <b>*</b></span><input v-model="form.title" class="field-input" placeholder="例如：客服看板意图识别模型验证" /></label>
              <label><span class="field-label">记录类型</span><select v-model="form.recordType" class="field-input"><option value="poc">POC 验证</option><option value="ai_capability">AI 能力</option></select></label>
              <label><span class="field-label">状态</span><select v-model="form.status" class="field-input"><option v-for="item in options.statuses" :key="item.key" :value="item.key">{{ item.label }}</option></select></label>
              <label><span class="field-label">验证结论</span><select v-model="form.conclusion" class="field-input"><option value="">未定结论</option><option v-for="item in options.conclusions" :key="item.key" :value="item.key">{{ item.label }}</option></select></label>
              <label><span class="field-label">负责人</span><input v-model="form.ownerName" class="field-input" placeholder="记录负责人" /></label>
            </div>

            <div class="rounded-lg border border-blue-100 bg-blue-50/40 p-3">
              <div class="mb-2 flex items-center gap-1.5 text-xs font-medium text-blue-800"><Link2 class="h-3.5 w-3.5" />关联业务上下文（可选）</div>
              <div class="grid gap-3 md:grid-cols-3">
                <label><span class="field-label">关联项目</span><select v-model="form.projectId" class="field-input"><option value="">未关联项目</option><option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name || item.title }}</option></select></label>
                <label><span class="field-label">关联正式需求</span><select v-model="form.requirementId" class="field-input"><option value="">未关联需求</option><option v-for="item in requirements" :key="item.id" :value="item.id">{{ item.title }}</option></select></label>
                <label><span class="field-label">关联需求池</span><select v-model="form.demandId" class="field-input"><option value="">未关联需求池</option><option v-for="item in demands" :key="item.id" :value="item.id">{{ item.title }}</option></select></label>
              </div>
              <p class="mt-2 text-[11px] text-blue-700">关联后可以从项目、正式需求或需求池回看这次验证；不要求每条开发经验都先有正式需求。</p>
            </div>

            <div class="grid gap-3 md:grid-cols-2">
              <label><span class="field-label">验证目标</span><textarea v-model="form.objective" class="field-input min-h-20" placeholder="想确认什么问题？"></textarea></label>
              <label><span class="field-label">验证假设</span><textarea v-model="form.hypothesis" class="field-input min-h-20" placeholder="在什么条件下，预期出现什么结果？"></textarea></label>
              <label><span class="field-label">验证范围</span><textarea v-model="form.scope" class="field-input min-h-20" placeholder="涉及的功能、流程或边界"></textarea></label>
              <label><span class="field-label">样品 / 样本数据</span><textarea v-model="form.sampleData" class="field-input min-h-20" placeholder="使用了什么数据、样品或测试场景？"></textarea></label>
              <label><span class="field-label">验证方法</span><textarea v-model="form.method" class="field-input min-h-20" placeholder="怎么做的，关键步骤是什么？"></textarea></label>
              <label><span class="field-label">验收 / 成功标准</span><textarea v-model="form.successCriteria" class="field-input min-h-20" placeholder="怎样算通过？"></textarea></label>
              <label><span class="field-label">验证结果</span><textarea v-model="form.result" class="field-input min-h-24" placeholder="实际结果、关键数据或观察"></textarea></label>
              <label><span class="field-label">局限与风险</span><textarea v-model="form.limitations" class="field-input min-h-24" placeholder="哪些条件下不能直接复用？"></textarea></label>
              <label class="md:col-span-2"><span class="field-label">下一步</span><textarea v-model="form.nextSteps" class="field-input min-h-20" placeholder="继续开发、补充验证或推广复用的动作"></textarea></label>
            </div>

            <div class="rounded-lg border border-cyan-100 bg-cyan-50/30 p-3">
              <div class="mb-2 flex items-center gap-1.5 text-xs font-medium text-cyan-800"><BrainCircuit class="h-3.5 w-3.5" />AI 能力补充信息</div>
              <div class="grid gap-3 md:grid-cols-2">
                <label><span class="field-label">模型 / 服务</span><input v-model="form.modelName" class="field-input" placeholder="例如：GPT、OCR、内部模型或规则引擎" /></label>
                <label><span class="field-label">版本</span><input v-model="form.modelVersion" class="field-input" placeholder="模型版本、接口版本或发布日期" /></label>
                <label class="md:col-span-2"><span class="field-label">Prompt / 技术方案</span><textarea v-model="form.promptOrApproach" class="field-input min-h-20" placeholder="关键 Prompt、调用方式、流程设计或实现要点"></textarea></label>
                <label class="md:col-span-2"><span class="field-label">复用说明</span><textarea v-model="form.reuseGuidance" class="field-input min-h-20" placeholder="适用场景、使用边界和复用时要注意什么"></textarea></label>
                <label><span class="field-label">指标 JSON（可选）</span><textarea v-model="form.metricText" class="field-input min-h-20 font-mono text-[11px]" placeholder="例如：{&quot;准确率&quot;: &quot;92%&quot;}"></textarea></label>
                <label><span class="field-label">标签（逗号分隔）</span><input v-model="form.tagsText" class="field-input" placeholder="OCR, 客服, 自动化" /></label>
              </div>
            </div>

            <AttachmentPicker :files="pendingFiles" @add="addFiles" @remove="removeFile" />
          </fieldset>

          <div class="mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-4">
            <div class="text-[11px] text-gray-400">{{ form.updatedAt ? `最近更新：${formatTime(form.updatedAt)}` : '保存后可继续上传验证材料' }}</div>
            <button v-if="!form.legacy" type="submit" class="inline-flex items-center gap-1.5 rounded-lg bg-accent-500 px-4 py-2 text-sm font-medium text-white hover:bg-accent-600 disabled:cursor-not-allowed disabled:opacity-60" :disabled="saving">
              <Save class="h-4 w-4" />{{ saving ? '保存中...' : '保存记录' }}
            </button>
          </div>

          <div v-if="form.attachments?.length" class="mt-4 rounded-lg border border-gray-100 bg-gray-50 p-3">
            <p class="text-xs font-medium text-gray-700">已上传材料</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <button v-for="file in form.attachments" :key="file.id" type="button" class="inline-flex max-w-full items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600 hover:text-accent-600" @click="downloadAttachment(file)">
                <Paperclip class="h-3.5 w-3.5" /><span class="max-w-[240px] truncate">{{ file.originalName || file.filename }}</span>
              </button>
            </div>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BrainCircuit, ChevronRight, FlaskConical, Link2, Paperclip, Plus, Save, Search } from 'lucide-vue-next'
import AttachmentPicker from '../components/AttachmentPicker.vue'
import { usePocWorkbenchPage } from "../features/system-insights/usePocWorkbenchPage"
const { router, records, projects, requirements, demands, pendingFiles, loading, saving, isCreating, selectedId, keyword, typeFilter, statusFilter, notice, errorMessage, options, blankForm, form, selectedRecord, filteredRecords, listOf, countByType, formatTime, relatedLabel, setMessage, copyIntoForm, selectRecord, startCreate, currentUserName, addFiles, removeFile, load, payloadFromForm, saveRecord, deriveCapability, downloadAttachment }=usePocWorkbenchPage()
</script>

<style scoped>
.field-label { display: block; margin-bottom: 0.35rem; font-size: 0.7rem; font-weight: 500; color: #4b5563; }
.field-label b { color: #ef4444; }
.field-input { width: 100%; border: 1px solid #e5e7eb; border-radius: 0.5rem; background: #fff; padding: 0.55rem 0.7rem; font-size: 0.8rem; color: #374151; outline: none; }
.field-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgb(59 130 246 / 0.1); }
textarea.field-input { resize: vertical; }
fieldset:disabled .field-input { cursor: not-allowed; background: #f9fafb; color: #6b7280; }
</style>
