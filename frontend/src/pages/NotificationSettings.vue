<template>
  <div class="page-transition max-w-6xl space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">通知配置</h1>
        <p class="text-sm text-gray-500 mt-1">配置个人与群组通知出口；日报、周报和重要产品事件统一只发送三层内容：实际工作进展、产品里程碑、当前在研产品。</p>
      </div>
      <button v-if="canManage" @click="openCreate" class="feishu-btn-primary">
        <Plus class="w-3.5 h-3.5" /> 新增通知目标
      </button>
    </div>

    <div class="grid grid-cols-4 gap-4">
      <div v-for="card in summaryCards" :key="card.label" :class="['rounded-xl border p-4', card.className]">
        <p class="text-xs text-gray-500">{{ card.label }}</p>
        <p class="mt-1 text-2xl font-bold tabular-nums" :class="card.valueClass">{{ card.value }}</p>
        <p class="mt-1 text-[11px] text-gray-400">{{ card.desc }}</p>
      </div>
    </div>

    <div v-if="!canManage" class="rounded-lg border border-blue-100 bg-blue-50/60 px-4 py-3 text-xs text-blue-700">
      当前为只读视角，可以查看通知规则和投递状态；Webhook、Secret、编辑、删除和发送操作仅限管理员或通知配置负责人。
    </div>

    <div class="grid grid-cols-3 gap-4">
      <div v-for="target in targets" :key="target.id" class="feishu-card">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h3 class="text-sm font-semibold text-gray-900">{{ target.name }}</h3>
            <p class="text-xs text-gray-400 mt-1">{{ scopeLabel(target.scope) }}</p>
          </div>
          <span :class="['text-[10px] px-1.5 py-0.5 rounded-full', target.enabled ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400']">
            {{ target.enabled ? '启用' : '停用' }}
          </span>
        </div>
        <div class="mt-3 space-y-1 text-xs text-gray-500">
          <p>发送渠道：{{ channelLabel(target.deliveryChannel) }}</p>
          <p>数据对象：{{ targetTypeLabel(target) }}</p>
          <p>发送对象：{{ audienceLabel(target) }}</p>
          <p>规则负责人：{{ target.ownerName || '未记录' }}</p>
          <p>触发方式：{{ triggerLabel(target) }}</p>
          <p>数据范围：{{ rangeLabel(target) }}</p>
          <p>汇报场景：{{ sceneLabel(target.reportScene) }}</p>
          <p class="truncate">最近发送：{{ lastSentLabel(target) }}</p>
          <p class="truncate">{{ target.deliveryChannel === 'personal' ? '接收人' : target.deliveryChannel === 'card' ? (target.cardTargetType === 'group' ? '卡片群会话' : '卡片接收人') : 'Webhook' }}：{{ target.deliveryChannel === 'personal' ? (target.recipientName || '未指定') : target.deliveryChannel === 'card' ? (target.cardTargetType === 'group' ? (target.recipientName || target.cardConversationId || '未指定') : (target.recipientName || '未指定')) : (target.webhookMasked || '-') }}</p>
        </div>
        <div class="flex items-center justify-end gap-2 mt-4">
          <button v-if="canManage" @click="previewTarget(target)" class="feishu-btn-ghost text-accent-500">预览</button>
          <button v-if="canManage" @click="sendNow(target)" class="feishu-btn-ghost text-accent-500"><Send class="w-3.5 h-3.5" /> 立即发送</button>
          <button v-if="canManage" @click="editTarget(target)" class="feishu-icon-btn" title="编辑"><Edit3 class="w-3 h-3" /></button>
          <button v-if="canManage" @click="removeTarget(target)" class="feishu-icon-btn text-red-400" title="删除"><Trash2 class="w-3 h-3" /></button>
        </div>
      </div>

      <div v-if="loadingTargets" class="col-span-3 text-center py-12 text-sm text-gray-400 bg-white rounded-lg border border-dashed border-gray-200">
        通知目标加载中...
      </div>

      <div v-else-if="targets.length === 0" class="col-span-3 text-center py-12 text-sm text-gray-400 bg-white rounded-lg border border-dashed border-gray-200">
        暂无通知规则，新增一个钉钉群机器人后即可主动或定时同步。
      </div>
    </div>

    <section v-if="canManage" class="feishu-card">
      <div class="flex items-center justify-between">
        <div><h2 class="text-sm font-semibold text-gray-900">最近投递记录</h2><p class="mt-1 text-[11px] text-gray-400">用于区分定时、事件和手动发送，并保留失败原因；同一业务事件不会向同一规则重复发送。</p></div>
        <button class="text-xs text-accent-600" @click="loadDeliveries">刷新</button>
      </div>
      <div v-if="!deliveries.length" class="mt-4 rounded-lg bg-gray-50 px-3 py-5 text-center text-xs text-gray-400">暂无投递记录。</div>
      <div v-else class="mt-3 overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="text-gray-400"><tr><th class="px-2 py-2">规则</th><th class="px-2 py-2">触发</th><th class="px-2 py-2">结果</th><th class="px-2 py-2">时间</th><th class="px-2 py-2">错误</th></tr></thead>
          <tbody><tr v-for="item in deliveries" :key="item.id" class="border-t border-gray-100"><td class="px-2 py-2 text-gray-700">{{ item.targetName || item.targetId }}</td><td class="px-2 py-2 text-gray-500">{{ deliveryTriggerLabel(item) }}</td><td class="px-2 py-2" :class="item.status === 'success' ? 'text-emerald-600' : 'text-rose-600'">{{ item.status === 'success' ? '成功' : '失败' }}</td><td class="px-2 py-2 text-gray-500">{{ item.createdAt || '-' }}</td><td class="max-w-sm truncate px-2 py-2 text-gray-400">{{ item.error || '-' }}</td></tr></tbody>
        </table>
      </div>
    </section>

    <div v-if="showModal" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center" @click.self="closeModal">
      <div class="bg-white rounded-xl shadow-xl w-[720px] max-h-[90vh] overflow-y-auto p-6 animate-scale-in">
        <h3 class="font-semibold text-gray-900 mb-4">{{ editing ? '编辑通知目标' : '新增通知目标' }}</h3>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div><label class="text-xs text-gray-500">名称 *</label><input v-model="form.name" class="feishu-input w-full mt-1" /></div>
            <div>
              <label class="text-xs text-gray-500">通知范围</label>
              <select v-model="form.scope" class="feishu-input w-full mt-1">
                <option value="dashboard">项目大盘</option>
                <option value="developer">开发者需求进度</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-gray-500">发送渠道</label>
              <select v-model="form.deliveryChannel" class="feishu-input w-full mt-1">
                <option value="group">钉钉群机器人（Markdown）</option>
                <option value="personal">钉钉个人机器人（Markdown）</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-500">数据对象范围</label>
              <select v-model="form.targetType" class="feishu-input w-full mt-1">
                <option value="global">全局产品与工作</option>
                <option value="developer">指定开发者工作</option>
                <option value="project">指定单个项目</option>
                <option value="requirement">指定单条需求</option>
              </select>
            </div>
          </div>
          <div v-if="form.targetType === 'project'">
            <label class="text-xs text-gray-500">指定项目 *</label>
            <select v-model="form.projectId" class="feishu-input w-full mt-1">
              <option value="">请选择项目</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
            </select>
          </div>
          <div v-else-if="form.targetType === 'requirement'">
            <label class="text-xs text-gray-500">指定需求 *</label>
            <select v-model="form.requirementId" class="feishu-input w-full mt-1">
              <option value="">请选择需求</option>
              <option v-for="requirement in requirements" :key="requirement.id" :value="requirement.id">{{ requirement.title }} · {{ requirement.projectName || requirement.pname || '未关联项目' }}</option>
            </select>
          </div>
          <div v-if="form.deliveryChannel === 'personal'">
            <label class="text-xs text-gray-500">接收人 *</label>
            <select v-model="form.recipientUserId" class="feishu-input w-full mt-1" @change="syncRecipientName">
              <option value="">请选择接收人</option>
              <option v-for="person in people" :key="person.userId" :value="person.userId">{{ person.name }}{{ person.role ? ` · ${person.role}` : '' }}</option>
            </select>
            <p class="mt-1 text-[11px] text-gray-400">个人通知使用钉钉机器人接口发送 Markdown，不需要填写群 Webhook。</p>
          </div>
          <div class="rounded-lg border border-blue-100 bg-blue-50/60 px-3 py-2 text-[11px] leading-5 text-blue-700">
            通知内容由汇报场景固定生成，不再从“当前负责事项”等历史字段推导。需求池提报和业务评估链接属于定向应用消息，不使用这里的通知规则。
          </div>
          <div v-if="form.scope === 'developer'" class="space-y-2">
            <label class="text-xs text-gray-500">同步对象</label>
            <div class="grid grid-cols-3 gap-2">
              <button type="button" v-for="mode in developerModes" :key="mode.value"
                class="rounded-lg border px-3 py-2 text-xs font-medium transition-colors"
                :class="form.developerMode === mode.value ? 'border-accent-300 bg-accent-50 text-accent-600' : 'border-gray-200 text-gray-600 hover:border-accent-200'"
                @click="selectDeveloperMode(mode.value)">
                {{ mode.label }}
              </button>
            </div>
            <select v-if="form.developerMode === 'custom'" v-model="form.developer" class="feishu-input w-full mt-1" @change="syncDeveloperUserId">
              <option value="">请选择开发者</option>
              <option v-for="d in developers" :key="d.name" :value="d.name">{{ d.name }}</option>
            </select>
            <p class="text-[11px] text-gray-400">{{ developerHint }}</p>
          </div>
          <div v-if="form.deliveryChannel === 'group'"><label class="text-xs text-gray-500">机器人 Webhook *</label><input v-model="form.webhook" class="feishu-input w-full mt-1" placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." /></div>
          <div v-if="form.deliveryChannel === 'group'"><label class="text-xs text-gray-500">加签 Secret</label><input v-model="form.secret" class="feishu-input w-full mt-1" placeholder="SEC..." /></div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-gray-500">触发方式</label>
              <select v-model="form.triggerType" class="feishu-input w-full mt-1">
                <option value="schedule">按时间周期发送</option>
                <option value="event">按业务事件触发</option>
              </select>
            </div>
            <label class="flex items-end gap-2 text-sm text-gray-600 pb-1">
              <input v-model="form.enabled" type="checkbox" class="rounded border-gray-300" />
              启用此通知规则
            </label>
          </div>
          <div v-if="form.triggerType === 'event'" class="rounded-lg border border-blue-100 bg-blue-50/50 p-3">
            <label class="text-xs text-gray-500">触发事件（可多选）</label>
            <div class="mt-2 grid grid-cols-2 gap-2">
              <label v-for="event in triggerEvents" :key="event.value" class="flex items-center gap-2 rounded-md border border-blue-100 bg-white px-2.5 py-2 text-xs text-gray-700 cursor-pointer">
                <input v-model="form.triggerEvents" :value="event.value" type="checkbox" class="rounded border-gray-300 text-accent-500 focus:ring-accent-400" />
                {{ event.label }}
              </label>
            </div>
          </div>
          <template v-else>
            <div class="grid grid-cols-2 gap-3">
              <div><label class="text-xs text-gray-500">发送时间</label><input v-model="form.scheduleTime" type="time" class="feishu-input w-full mt-1" /></div>
              <div>
                <label class="text-xs text-gray-500">同步频率</label>
                <select v-model="form.scheduleCycle" class="feishu-input w-full mt-1">
                  <option value="daily">每天</option>
                  <option value="weekly">每周</option>
                  <option value="monthly">每月</option>
                  <option value="custom">自定义发送日</option>
                </select>
              </div>
            </div>
            <div v-if="form.scheduleCycle !== 'daily'" class="grid grid-cols-2 gap-3">
              <div v-if="form.scheduleCycle === 'weekly'">
                <label class="text-xs text-gray-500">每周发送日</label>
                <select v-model.number="form.scheduleDay" class="feishu-input w-full mt-1">
                  <option v-for="day in weekDays" :key="day.value" :value="day.value">{{ day.label }}</option>
                </select>
              </div>
              <div v-else-if="form.scheduleCycle === 'monthly'">
                <label class="text-xs text-gray-500">每月发送日</label>
                <select v-model.number="form.scheduleDay" class="feishu-input w-full mt-1">
                  <option v-for="day in 31" :key="day" :value="day">每月 {{ day }} 日</option>
                </select>
              </div>
              <div v-else class="col-span-2 rounded-lg border border-blue-100 bg-blue-50/50 p-3">
                <div class="flex items-center justify-between gap-3">
                  <label class="text-xs text-gray-500">自定义发送日（可多选）</label>
                  <div class="flex gap-2">
                    <button type="button" class="text-[11px] text-accent-600 hover:underline" @click="form.scheduleWeekdays = [1, 2, 3, 4, 5]">工作日</button>
                    <button type="button" class="text-[11px] text-accent-600 hover:underline" @click="form.scheduleWeekdays = [1, 2, 3, 4, 5, 6, 7]">每天</button>
                  </div>
                </div>
                <div class="mt-2 grid grid-cols-7 gap-2">
                  <label v-for="day in weekDays" :key="day.value" class="flex items-center justify-center gap-1 rounded-md border border-blue-100 bg-white px-1 py-2 text-xs text-gray-700 cursor-pointer">
                    <input v-model="form.scheduleWeekdays" :value="day.value" type="checkbox" class="rounded border-gray-300 text-accent-500 focus:ring-accent-400" />
                    {{ day.label }}
                  </label>
                </div>
                <p class="mt-2 text-[11px] text-gray-400">只在选中的星期发送。例如双休工作制可选择周一至周五，周末不会推送。</p>
              </div>
            </div>
          </template>
          <div>
            <label class="text-xs text-gray-500">汇报场景</label>
            <select v-model="form.reportScene" class="feishu-input w-full mt-1" @change="applySceneDefaults">
              <option value="daily">每日工作同步</option>
              <option value="weekly">每周工作与产品动态</option>
              <option value="milestone">重要产品事件</option>
            </select>
            <p class="mt-1 text-[11px] text-gray-400">三种场景都使用相同三层结构；日报看当天，周报汇总近 7 天，重要事件按事件触发。</p>
          </div>
          <div>
            <label class="text-xs text-gray-500">统计时间范围</label>
            <select v-model="form.contentRange" class="feishu-input w-full mt-1">
              <option value="today">今天</option>
              <option value="last7days">近 7 天</option>
              <option value="thisMonth">本月</option>
              <option value="lastMonth">上月</option>
              <option value="custom">自定义日期</option>
            </select>
            <div v-if="form.contentRange === 'custom'" class="mt-2 grid grid-cols-2 gap-3">
              <div><label class="text-[11px] text-gray-400">开始日期</label><input v-model="form.customRangeStart" type="date" class="feishu-input w-full mt-1" /></div>
              <div><label class="text-[11px] text-gray-400">结束日期</label><input v-model="form.customRangeEnd" type="date" class="feishu-input w-full mt-1" /></div>
            </div>
          </div>
          <div class="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-600">
            固定发送三层内容：实际工作进展、产品里程碑、当前在研产品。当前在研产品只展示新流程登记的 L3，不会再把历史“当前负责事项”带入通知。
          </div>
          <div>
            <label class="text-xs text-gray-500">自定义同步内容</label>
            <textarea v-model="form.customContent" class="feishu-input w-full mt-1" rows="4"
              placeholder="可填写本次想额外同步的说明、风险提醒、下一步计划。勾选“自定义内容”后会发送到群里。"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-5">
          <button @click="closeModal" class="feishu-btn-ghost text-sm">取消</button>
          <button @click="saveTarget" class="feishu-btn-primary text-sm">保存</button>
        </div>
      </div>
    </div>

    <div v-if="previewOpen" class="fixed inset-0 bg-black/30 z-[55] flex items-center justify-center" @click.self="previewOpen = false">
      <div class="bg-white rounded-xl shadow-xl w-[720px] max-h-[88vh] overflow-hidden p-6 animate-scale-in">
        <div class="flex items-start justify-between border-b border-gray-100 pb-4">
          <div>
            <h3 class="font-semibold text-gray-900">消息预览</h3>
            <p class="mt-1 text-xs text-gray-400">{{ previewTitle }} · 只生成预览，不会发送到钉钉。</p>
          </div>
          <button class="feishu-icon-btn" title="关闭" @click="previewOpen = false">×</button>
        </div>
        <div v-if="previewLoading" class="flex h-64 items-center justify-center text-sm text-gray-400">正在生成预览...</div>
        <pre v-else class="mt-4 max-h-[60vh] overflow-auto rounded-lg bg-slate-50 p-4 text-xs leading-6 whitespace-pre-wrap text-gray-700">{{ previewMarkdown || '暂无预览内容' }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Edit3, Plus, Send, Trash2 } from 'lucide-vue-next'
import { useNotificationSettingsPage } from "../features/system-insights/useNotificationSettingsPage"
const { targets, deliveries, developers, people, projects, requirements, loadingTargets, showModal, editing, form, canManage, previewOpen, previewLoading, previewTitle, previewMarkdown, developerModes, weekDays, triggerEvents, contentOptions, contentOptionValues, normalizeContentTypes, currentUser, summaryCards, currentDeveloperName, currentUserId, developerHint, blankForm, openCreate, editTarget, closeModal, scopeLabel, channelLabel, targetTypeLabel, audienceLabel, scheduleLabel, triggerLabel, rangeLabel, sceneLabel, lastSentLabel, contentLabel, loadData, loadDeliveries, readCurrentUser, loadDevelopers, selectDeveloperMode, previewTarget, syncDeveloperUserId, syncRecipientName, applySceneDefaults, saveTarget, removeTarget, sendNow, deliveryTriggerLabel }=useNotificationSettingsPage()
</script>
