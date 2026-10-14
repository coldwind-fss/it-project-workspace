<template>
  <div v-if="detailLoading" class="page-transition max-w-4xl rounded-xl border border-gray-100 bg-white px-6 py-16 text-center">
    <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
    <p class="mt-4 text-sm text-gray-500">正在加载需求详情...</p>
  </div>

  <div v-else-if="detailError" class="page-transition max-w-4xl rounded-xl border border-amber-100 bg-white px-6 py-12 text-center">
    <h2 class="text-base font-semibold text-gray-900">需求详情暂时打不开</h2>
    <p class="mx-auto mt-2 max-w-xl text-sm leading-6 text-gray-500">{{ detailError }}</p>
    <div class="mt-5 flex justify-center gap-2">
      <button type="button" class="feishu-btn-ghost text-sm" @click="router.push('/requirements')">返回需求列表</button>
      <button type="button" class="feishu-btn-primary text-sm" @click="loadDetail">重新加载</button>
    </div>
  </div>

  <div v-else-if="!req" class="page-transition max-w-4xl rounded-xl border border-gray-100 bg-white px-6 py-12 text-center">
    <h2 class="text-base font-semibold text-gray-900">没有找到这条需求</h2>
    <p class="mt-2 text-sm text-gray-500">需求编号可能已变更或已被移入回收站。</p>
    <button type="button" class="feishu-btn-primary mt-5 text-sm" @click="router.push('/requirements')">返回需求列表</button>
  </div>

  <div v-else class="page-transition max-w-4xl" @paste="handleImagePaste">
    <div class="flex items-center justify-between mb-5">
      <button @click="router.push('/requirements')" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors">
        <ArrowLeft class="w-4 h-4" /> 返回需求列表
      </button>
      <div class="flex items-center gap-2">
        <template v-if="editing">
          <button @click="cancelEdit" class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">
            <X class="w-4 h-4" /> 取消
          </button>
          <button @click="saveEdit" :disabled="saving" class="btn-primary flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm">
            <Save class="w-4 h-4" /> {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </template>
        <button v-else @click="startEdit" class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-accent-500 hover:bg-accent-50 rounded-lg">
          <Edit3 class="w-4 h-4" /> 编辑
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-100">
      <div class="p-6 border-b border-gray-100">
        <div class="flex items-start justify-between mb-4">
          <div>
            <div class="flex items-center gap-3 mb-3">
              <!-- Type -->
              <select v-if="editing" v-model="form.type" class="badge text-white px-2 py-0.5 text-xs border-0" :style="{ backgroundColor: typeColors[form.type] || '#6b7280' }">
                <option v-for="t in TYPE_OPTS" :key="t" :value="t" style="color:#333;background:#fff">{{ t }}</option>
              </select>
              <span v-else class="badge text-white" :style="{ backgroundColor: typeColors[req.type] || '#6b7280' }">{{ req.type }}</span>
              <!-- Status -->
              <div class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-2 py-1 shadow-sm">
                <span class="text-[10px] font-medium text-gray-400">当前状态</span>
                <span v-if="editing" class="text-xs font-semibold" :style="{ color: statusColors[form.status] }">{{ form.status }}</span>
                <span v-else class="text-xs font-semibold" :style="{ color: statusColors[req.status] }">{{ req.status }}</span>
              </div>
              <!-- Priority -->
              <select v-if="editing" v-model="form.priority" class="text-xs font-bold px-2 py-0.5 rounded border-0"
                :style="{ backgroundColor: priorityColors[form.priority] + '15', color: priorityColors[form.priority] }">
                <option v-for="p in PRIORITY_OPTS" :key="p" :value="p" style="color:#333;background:#fff">{{ p }}</option>
              </select>
              <span v-else class="text-xs font-bold px-2 py-0.5 rounded" :style="{ backgroundColor: priorityColors[req.priority] + '15', color: priorityColors[req.priority] }">{{ req.priority }}</span>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
              <span class="rounded bg-slate-100 px-2 py-1">{{ req.itemKindLabel || 'L3 工作单元' }}</span>
              <span v-if="req.versionTarget" class="rounded bg-blue-50 px-2 py-1 text-blue-700">版本 {{ req.versionTarget }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs text-gray-400 bg-gray-50 px-2 py-1 rounded">{{ req.id }}</span>
              <input v-if="editing" v-model="form.title" class="text-xl font-bold text-gray-900 border border-gray-200 rounded-lg px-3 py-1 flex-1" />
              <h2 v-else class="text-xl font-bold text-gray-900">{{ req.title }}</h2>
            </div>
          </div>
        </div>

        <PriorityAssessment v-if="editing" v-model="form.priorityEvaluation" :priority="form.priority || 'P2'" :project-priority="assessmentProjectPriority" class="mb-4" @adopt="form.priority = $event" />

        <div class="mb-4 grid grid-cols-3 gap-3 rounded-lg border border-slate-100 bg-slate-50/70 p-3 text-sm">
          <div>
            <span class="text-[11px] text-gray-400">变更对象</span>
            <select v-if="editing" v-model="form.changeObject" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm bg-white">
              <option v-for="item in CHANGE_OBJECT_OPTS" :key="item" :value="item">{{ item }}</option>
            </select>
            <p v-else class="mt-1 font-medium text-gray-700">{{ req.changeObject || '功能' }}</p>
          </div>
          <div>
            <span class="text-[11px] text-gray-400">产品影响</span>
            <select v-if="editing" v-model="form.impactLevel" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm bg-white">
              <option v-for="item in IMPACT_OPTS" :key="item" :value="item">{{ item }}</option>
            </select>
            <p v-else class="mt-1 font-bold" :style="{ color: impactColors[req.impactLevel || '常规'] }">{{ req.impactLevel || '常规' }}</p>
          </div>
          <div>
            <span class="text-[11px] text-gray-400">工作量</span>
            <select v-if="editing" v-model="form.workloadLevel" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm bg-white">
              <option v-for="item in WORKLOAD_OPTS" :key="item" :value="item">{{ item }}</option>
            </select>
            <p v-else class="mt-1 font-medium text-gray-700">{{ req.workloadLevel || '中' }}</p>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-6 text-sm mt-4">
          <div>
            <span class="text-gray-400">L3 工作单元</span>
            <select v-if="editing" v-model="form.itemKind" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm bg-white"><option v-for="item in ITEM_KIND_OPTS" :key="item.key" :value="item.key">{{ item.label }}</option></select>
            <p v-else class="text-gray-700 font-medium mt-1">{{ req.itemKindLabel || '新功能 / 模块' }}</p>
          </div>
          <div>
            <span class="text-gray-400">目标版本</span>
            <input v-if="editing" v-model="form.versionTarget" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm" placeholder="例如 v1.1.0" />
            <p v-else class="text-gray-700 font-medium mt-1">{{ req.versionTarget || '未设置' }}</p>
          </div>
          <div>
            <span class="text-gray-400">所属项目</span>
            <select v-if="editing" v-model="form.projectId" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm bg-white">
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
            <p v-else class="text-gray-700 font-medium mt-1">{{ projName }}</p>
          </div>
          <div>
            <span class="text-gray-400">提出方</span>
            <SearchableMultiSelect v-if="editing" v-model="form.requester" :options="peopleOpts" />
            <p v-else class="text-gray-700 font-medium mt-1">{{ req.requester }}</p>
          </div>
          <div>
            <span class="text-gray-400">负责人</span>
            <SearchableMultiSelect v-if="editing" v-model="form.assignee" :options="devOpts" placeholder="搜索或选择开发负责人" />
            <div v-else class="flex items-center gap-2 mt-1">
              <div class="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-bold"
                :style="{ backgroundColor: getAssignee(req.assignee).color }">{{ getAssignee(req.assignee).initials }}</div>
              <span class="text-gray-700 font-medium">{{ req.assignee }}</span>
            </div>
          </div>
          <div>
            <span class="text-gray-400">归属部门</span>
            <select v-if="editing" v-model="form.department" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm bg-white">
              <option value="">请选择</option>
              <option v-for="d in deptOpts" :key="d" :value="d">{{ d }}</option>
            </select>
            <p v-else class="text-gray-700 font-medium mt-1">{{ req.department || req.projectDepartment || '未设置' }}</p>
          </div>
          <div><span class="text-gray-400">创建时间</span><p class="text-gray-700 mt-1">{{ req.createdAt }}</p></div>
          <div><span class="text-gray-400">最后更新</span><p class="text-gray-700 mt-1">{{ req.updatedAt }}</p></div>
          <div>
            <span class="text-gray-400">预计交付时间</span>
            <input v-if="editing" v-model="form.expectedDeliveryTime" type="date" class="w-full mt-1 px-2 py-1 border border-gray-200 rounded text-sm" />
            <p v-else class="text-gray-700 font-medium mt-1">{{ req.expectedDeliveryTime || '未设置' }}</p>
          </div>
          <div>
            <span class="text-gray-400">完成时间</span>
            <p class="text-gray-700 font-medium mt-1">{{ req.completedAt || '未完成' }}</p>
          </div>
        </div>
      </div>

      <div class="p-6 border-b border-gray-100">
        <h3 class="font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText class="w-4 h-4 text-gray-400" /> 需求描述</h3>
        <textarea v-if="editing" v-model="form.description" rows="4"
          class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:border-accent-500" />
        <p v-else class="text-sm text-gray-600 leading-relaxed">{{ req.description }}</p>
      </div>

      <div class="p-6 border-b border-gray-100">
        <h3 class="font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText class="w-4 h-4 text-gray-400" /> 备注 / 验收标准</h3>
        <textarea v-if="editing" v-model="form.acceptanceCriteria" rows="3"
          class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:border-accent-500" />
        <p v-else class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{{ req.acceptanceCriteria || '暂无备注' }}</p>
      </div>

      <div class="p-6 border-b border-gray-100">
        <h3 class="font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText class="w-4 h-4 text-gray-400" /> 交付进度反馈截图</h3>
        <div v-if="editing">
          <input type="file" accept="image/*" multiple class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white"
            @change="handleImageUpload($event)" />
          <p class="mt-1 text-[11px] text-gray-400">也可直接按 Ctrl + V 粘贴剪贴板中的图片</p>
          <div v-if="form.images?.length" class="mt-3 flex flex-wrap gap-3">
            <div v-for="(img, i) in form.images" :key="i" class="relative group">
              <img :src="imageSrc(img)" class="w-24 h-24 rounded-lg object-cover border border-gray-200 cursor-pointer" @click="previewImages(form.images, i)" />
              <button type="button" class="absolute -right-1.5 -top-1.5 hidden group-hover:flex w-5 h-5 items-center justify-center rounded-full bg-red-500 text-white text-xs"
                @click.stop="removeImage(i)">×</button>
            </div>
          </div>
        </div>
        <div v-else>
          <button v-if="req.images?.length && !showDeliveryImages" type="button" class="feishu-btn-ghost text-xs text-accent-600" @click="showDeliveryImages = true">
            查看 {{ req.imageCount || req.images.length }} 张交付截图
          </button>
          <div v-else-if="req.images?.length" class="flex flex-wrap gap-3">
            <img v-for="(img, i) in req.images" :key="i" :src="imageSrc(img)"
              class="w-24 h-24 rounded-lg object-cover border border-gray-200 cursor-pointer hover:border-accent-300"
              @click="previewImages(req.images, i)" />
          </div>
          <p v-else class="text-sm text-gray-400">暂无截图</p>
        </div>
      </div>

      <DeliveryBaselinePanel v-if="req" :requirement="req" />

      <RequirementPhases v-if="req" :requirement="req" :revision="activityRevision" />

      <div v-if="canManageOutcome" class="p-6 border-b border-gray-100">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold text-gray-900 flex items-center gap-2"><Target class="w-4 h-4 text-emerald-500" /> 上线回执与价值验证 <span class="text-[10px] font-normal text-emerald-600 rounded bg-emerald-50 px-1.5 py-0.5">3 天 + 30 天</span></h3>
            <p class="mt-1 text-xs leading-5 text-gray-500">上线前目标只作为参照；上线后保留 3 天使用回执和 30 天价值验证两次业务反馈。交付是否合格以上方的上线前交付标准为准。</p>
          </div>
          <span v-if="postlaunchOutcomeRequests.length" class="text-[11px] text-emerald-600">{{ postlaunchOutcomeRequests.some(item => item.status === 'submitted') ? '已收到业务反馈' : '已安排待填写' }}</span>
        </div>
        <div v-if="canSendOutcomeGoal" class="mt-4 rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
            <label class="block"><span class="text-xs text-gray-500">业务目标确认人 <span class="font-normal text-gray-400">（默认提出方）</span></span><select v-if="outcomeContacts.length" v-model="outcomeRecipientUserId" class="feishu-input w-full mt-1"><option value="">请选择联系人</option><option v-for="person in outcomeContacts" :key="person.userId || person.userid || person.name" :value="person.userId || person.userid || person.dingUserId">{{ person.name }}</option></select><input v-else v-model="outcomeRecipientName" class="feishu-input w-full mt-1" maxlength="120" placeholder="填写业务负责人姓名" /></label>
            <button type="button" class="feishu-btn-primary justify-center" :disabled="sendingOutcome || (!outcomeRecipientName && !outcomeRecipientUserId)" @click="sendOutcomeGoal">{{ sendingOutcome ? '发送中...' : '发起上线前目标确认' }}</button>
          </div>
          <p class="mt-2 text-[11px] leading-5 text-emerald-700">{{ outcomeHint }}</p>
        </div>
        <div v-else class="mt-4 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2.5 text-xs leading-5 text-gray-500">当前状态为「{{ req.status }}」，上线前目标确认只在正式开发/交付前发起。如需补录，请在项目协作记录中说明。</div>
        <div v-if="postlaunchOutcomeRequests.length" class="mt-4 space-y-2">
          <div v-for="outcome in postlaunchOutcomeRequests" :key="outcome.id" class="rounded-lg border border-emerald-100 bg-white px-3 py-2.5 text-xs"><div class="flex flex-wrap items-center justify-between gap-2"><span class="text-emerald-800">{{ outcome.stageLabel }} · {{ outcome.recipientName || '业务负责人' }} · {{ outcome.statusLabel }}</span><button v-if="outcome.link" type="button" class="text-emerald-700 hover:text-emerald-900" @click="copyOutcomeLink(outcome.link)">{{ outcome.status === 'submitted' ? '复制链接' : '复制待填写链接' }}</button></div><p v-if="outcome.status === 'submitted' && outcome.responseSnapshot" class="mt-1 text-[11px] leading-5 text-gray-500">{{ outcome.stage === 'day7' ? [outcome.responseSnapshot.useStatus, outcome.responseSnapshot.goalStatus, outcome.responseSnapshot.satisfaction].filter(Boolean).join(' · ') : [outcome.responseSnapshot.effectStatus, outcome.responseSnapshot.changeTypes?.join('、')].filter(Boolean).join(' · ') }}</p><p v-if="outcome.status === 'submitted' && outcome.responseSnapshot?.summary" class="mt-1 text-[11px] leading-5 text-gray-600">{{ outcome.responseSnapshot.summary }}</p></div>
        </div>
      </div>

      <SharedActivityFeed v-if="req" :key="id + ':' + activityRevision" scope-type="requirement" :scope-id="id" :enable-collaboration="true" :collaboration-recipient="req.requester || ''" :collaboration-title="'资料请求：' + req.title" title="L3 共享动态与讨论" subtitle="开发和业务的进展、资料请求、回复和交付讨论都保留在同一条动态时间线中。" />

      <RequirementLifecycle v-if="req" :key="'delivery:' + id" :requirement="req" :revision="activityRevision" :delivery-only="true" read-only @changed="refreshLifecycleRelated" />

      <ImagePreviewModal v-model="previewModal.open" :images="previewModal.images" :start-index="previewModal.index" />

      <div v-if="editing && statusChanged" class="p-6 border-b border-gray-100 bg-amber-50/40">
        <h3 class="font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <Clock class="w-4 h-4 text-amber-500" /> 状态调整说明
        </h3>
        <p class="text-xs text-gray-500 mb-3">状态从「{{ req.status }}」变更为「{{ form.status }}」，请记录本次做了什么调整，保存后会同步到变更历史。</p>
        <textarea v-model="form.reason" rows="3"
          class="w-full px-3 py-2 border border-amber-200 rounded-lg text-sm resize-none focus:outline-none focus:border-amber-400 bg-white"
          placeholder="例如：开发完成，已提交测试环境验证；或：业务确认范围，进入开发中。" />
      </div>

      <div class="p-6">
        <h3 class="font-semibold text-gray-900 mb-5 flex items-center gap-2">
          <Clock class="w-4 h-4 text-gray-400" /> 变更历史时间线
          <span class="text-xs text-gray-400 font-normal ml-1">({{ changelogs.length }} 次变更)</span>
        </h3>
        <p v-if="changelogs.length === 0" class="text-sm text-gray-400 text-center py-8">暂无变更记录</p>
        <div v-else class="relative">
          <div class="absolute left-[5px] top-1 bottom-1 w-px bg-gray-200" />
          <div class="space-y-0">
            <div v-for="(cl, i) in changelogs" :key="cl.id" class="flex gap-4 py-3 relative animate-slide-in" :style="{ animationDelay: (i * 50) + 'ms' }">
              <div class="timeline-dot" :style="{ backgroundColor: getConfig(cl.changeType).color }" />
              <div class="flex-1 bg-gray-50 rounded-lg p-4 border border-gray-100">
                <div class="flex items-center gap-2 mb-2">
                  <span class="badge text-white text-[10px]" :style="{ backgroundColor: getConfig(cl.changeType).color }">{{ cl.changeType }}</span>
                  <span class="text-[11px] text-gray-400">{{ cl.createdAt }}</span>
                </div>
                <p class="text-sm text-gray-700">
                  <strong class="text-gray-900">{{ cl.fieldName }}</strong> 变更：<br />
                  <span class="text-red-500 line-through">{{ cl.oldValue }}</span>
                  <span class="text-gray-300 mx-2">→</span>
                  <span class="text-green-600">{{ cl.newValue }}</span>
                </p>
                <p class="text-xs text-gray-400 mt-2">原因：{{ cl.reason }}<span class="ml-3">操作人：{{ cl.operator }}</span></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, Clock, FileText, Edit3, Save, X, Target } from 'lucide-vue-next'
import ImagePreviewModal from '../components/ImagePreviewModal.vue'
import SharedActivityFeed from '../components/SharedActivityFeed.vue'
import RequirementLifecycle from '../components/RequirementLifecycle.vue'
import DeliveryBaselinePanel from '../components/DeliveryBaselinePanel.vue'
import RequirementPhases from '../components/RequirementPhases.vue'
import SearchableMultiSelect from '../components/SearchableMultiSelect.vue'
import PriorityAssessment from '../components/PriorityAssessment.vue'
import { useRequirementDetailPage } from "../features/project-work/useRequirementDetailPage"
const { route, router, id, STATUS_OPTS, TYPE_OPTS, ITEM_KIND_OPTS, CHANGE_OBJECT_OPTS, IMPACT_OPTS, WORKLOAD_OPTS, impactColors, PRIORITY_OPTS, req, activityRevision, refreshLifecycleRelated, changelogs, detailLoading, detailError, projects, editing, saving, form, previewModal, showDeliveryImages, peopleOpts, devOpts, deptOpts, currentUser, outcomeRequests, postlaunchOutcomeRequests, outcomeContacts, outcomeRecipientUserId, outcomeRecipientName, sendingOutcome, canManageOutcome, canSendOutcomeGoal, outcomeHint, projName, assessmentProjectPriority, statusChanged, statusOnlyEdit, getAssignee, getConfig, startEdit, cancelEdit, saveEdit, imageSrc, previewImages, handleImageUpload, handleImagePaste, appendImageFiles, removeImage, outcomeContactById, sendOutcomeGoal, copyOutcomeLink, detailLoadSequence, loadDetail, typeColors, priorityColors, statusColors, assigneeMap, changeTypeConfig } = useRequirementDetailPage()
</script>
