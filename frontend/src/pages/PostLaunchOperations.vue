<template>
  <div class="page-transition space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-semibold text-accent-600">IT 执行入口</p>
        <h1 class="mt-1 text-xl font-bold text-gray-900">上线后运营记录</h1>
        <p class="mt-1 text-sm text-gray-500">管理交付、回访、问题整改、改善提案和知识沉淀；管理汇总请进入独立看板。</p>
      </div>
      <div class="flex items-center gap-2">
        <router-link to="/postlaunch/dashboard" class="feishu-btn-ghost border border-blue-200 bg-blue-50 text-blue-700">查看价值管理看板</router-link>
        <button class="feishu-btn-ghost border border-gray-200 bg-white" @click="refresh">刷新</button>
        <button class="feishu-btn-primary" @click="showCreate = !showCreate"><Plus class="h-4 w-4" />建立交付记录</button>
      </div>
    </div>

    <div v-if="showCreate" class="rounded-2xl border border-accent-200 bg-accent-50/40 p-4">
      <div class="mb-3 text-sm font-semibold text-gray-900">从已有 L2/L3 建立交付后运营记录</div>
      <div class="grid gap-3 md:grid-cols-4">
        <select v-model="createForm.targetType" class="field"><option value="requirement">L3 需求</option><option value="project">L2 项目</option></select>
        <select v-model="createForm.targetId" class="field md:col-span-2"><option value="">请选择已交付对象</option><option v-for="item in targetOptions" :key="item.id" :value="item.id">{{ item.title }} · {{ item.status }}</option></select>
        <input v-model="createForm.deliveryDate" type="date" class="field" />
      </div>
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <input v-model="createForm.businessOwnerName" class="field max-w-xs" placeholder="业务联系人（可选）" />
        <button class="feishu-btn-primary" :disabled="saving" @click="createOperation">保存交付记录</button>
        <span class="text-xs text-gray-500">仅完成需求池完整链路的正式需求会安排 3 天和 30 天价值验证节点。</span>
      </div>
    </div>

    <div v-if="loading" class="flex h-48 items-center justify-center"><div class="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" /></div>
    <template v-else>
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        <div v-for="card in summaryCards" :key="card.key" class="rounded-xl border bg-white p-3" :class="card.border">
          <p class="text-xs text-gray-500">{{ card.label }}</p><p class="mt-1 text-2xl font-bold" :class="card.color">{{ summary[card.key] || 0 }}</p>
        </div>
      </div>

      <div class="rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-3 text-xs leading-5 text-slate-600">本页只记录执行过程和原始证据，不承担管理指标汇总。需要查看响应率、满意率、使用率和提效比例时，请打开右上角的“价值管理看板”。</div>

      <div class="grid min-h-[560px] gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
        <section class="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3"><h2 class="text-sm font-semibold text-gray-900">交付记录</h2><span class="text-xs text-gray-400">{{ rows.length }} 条</span></div>
          <div class="max-h-[680px] overflow-y-auto">
            <button v-for="row in rows" :key="row.id" @click="select(row.id)" class="w-full border-b border-gray-100 px-4 py-3 text-left transition hover:bg-accent-50" :class="selectedId === row.id ? 'bg-accent-50 ring-1 ring-inset ring-accent-200' : ''">
              <div class="flex items-start justify-between gap-2"><span class="truncate text-sm font-semibold text-gray-900">{{ row.title }}</span><span class="shrink-0 rounded-full bg-green-50 px-2 py-0.5 text-[10px] text-green-700">{{ row.deliveryKind }}</span></div>
              <div class="mt-1 text-xs text-gray-500">{{ row.projectName || '独立 L3' }} · {{ row.deliveryDate }}</div>
              <div class="mt-2 flex gap-2 text-[10px] text-gray-400"><span>3天 {{ outcomeStatus(row, 'day7') }}</span><span>30天 {{ outcomeStatus(row, 'day30') }}</span><span v-if="row.openIssueCount" class="text-red-500">问题 {{ row.openIssueCount }}</span></div>
            </button>
            <div v-if="!rows.length" class="px-4 py-12 text-center text-sm text-gray-400">暂无交付后运营记录</div>
          </div>
        </section>

        <section class="min-w-0 rounded-2xl border border-gray-200 bg-white p-5">
          <div v-if="detail" class="space-y-5">
            <div class="flex flex-wrap items-start justify-between gap-3 border-b border-gray-100 pb-4"><div><p class="text-xs text-accent-600">交付后运营 · {{ detail.deliveryKind }}</p><h2 class="mt-1 text-lg font-bold text-gray-900">{{ detail.title }}</h2><p class="mt-1 text-xs text-gray-500">交付 {{ detail.deliveryDate }} · 业务联系人 {{ detail.businessOwnerName || '待指定' }}</p></div><span class="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">{{ detail.status === 'active' ? '运营中' : detail.status }}</span></div>
            <div v-if="detail.valueVerificationEligibility" class="rounded-xl border p-3 text-xs leading-5" :class="detail.valueVerificationEligible ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-slate-200 bg-slate-50 text-slate-600'"><span class="font-semibold">价值验证资格：</span>{{ detail.valueVerificationEligibility.reason }}</div>
            <div v-if="!detail.businessOwnerName" class="flex flex-wrap items-center gap-2 rounded-xl border border-orange-200 bg-orange-50 p-3"><span class="text-xs text-orange-700">尚未指定业务联系人，补充后才能发送回访。</span><input v-model="ownerName" class="field max-w-xs" placeholder="业务联系人姓名" /><button class="feishu-btn-primary" @click="saveOwner">保存并安排节点</button></div>
            <div class="grid gap-3 md:grid-cols-3"><div class="info"><span>3 天节点</span><b>{{ detail.day7DueDate || '未安排' }}</b></div><div class="info"><span>30 天节点</span><b>{{ detail.day30DueDate || '未安排' }}</b></div><div class="info"><span>开放问题</span><b :class="detail.openIssueCount ? 'text-red-600' : 'text-green-600'">{{ detail.openIssueCount || 0 }}</b></div></div>

            <div class="grid gap-4 lg:grid-cols-2">
              <div class="panel panel-blue"><div class="panel-title">回访与复盘</div><p class="panel-help">只保留上线 3 天回执和上线 30 天价值验证；可复制链接发给业务。</p><div v-for="item in detail.outcomeRequests" :key="item.id" class="mt-2 rounded-lg bg-white px-3 py-2 text-xs"><div class="flex items-center justify-between gap-2"><span>{{ item.stageLabel }}</span><div class="flex items-center gap-2"><span :class="item.status === 'submitted' ? 'text-green-600' : 'text-orange-600'">{{ item.statusLabel || item.status }}</span><button v-if="item.link" type="button" class="text-blue-700 hover:text-blue-900" @click="copyOutcomeLink(item.link)">{{ item.status === 'submitted' ? '复制' : '复制链接' }}</button></div></div><p v-if="item.status === 'submitted' && item.responseSnapshot" class="mt-1 text-[11px] leading-5 text-gray-500">{{ item.stage === 'day7' ? [item.responseSnapshot.useStatus, item.responseSnapshot.goalStatus, item.responseSnapshot.satisfaction].filter(Boolean).join(' · ') : [item.responseSnapshot.effectStatus, item.responseSnapshot.changeTypes?.join('、')].filter(Boolean).join(' · ') }}</p><p v-if="item.status === 'submitted' && item.responseSnapshot?.summary" class="mt-1 whitespace-pre-wrap text-[11px] leading-5 text-gray-600">{{ item.responseSnapshot.summary }}</p></div><div v-if="!detail.outcomeRequests?.length" class="mt-3 text-xs text-gray-400">尚未生成回访请求，请确认业务联系人。</div></div>
              <div class="panel panel-amber"><div class="panel-title">问题与整改</div><div v-if="detail.issues?.length" class="mt-2 space-y-2"><div v-for="issue in detail.issues" :key="issue.id" class="rounded-lg bg-white px-3 py-2"><div class="flex items-center justify-between gap-2"><b class="truncate text-xs text-gray-800">{{ issue.title }}</b><select class="rounded border border-gray-200 px-1 py-0.5 text-[10px]" :value="issue.status" @change="updateIssue(issue.id, ($event.target as HTMLSelectElement).value)"><option>待核实</option><option>处理中</option><option>待验证</option><option>已关闭</option></select></div><p class="mt-1 text-[11px] text-gray-500">{{ issue.description || '无补充说明' }}</p></div></div><p v-else class="mt-2 text-xs text-gray-400">暂无问题记录。</p><button class="mt-3 rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-700" @click="showIssue = !showIssue">登记问题</button></div>
            </div>

            <div v-if="showIssue" class="rounded-xl border border-amber-200 bg-amber-50/50 p-3"><div class="grid gap-2 md:grid-cols-4"><input v-model="issueForm.title" class="field md:col-span-2" placeholder="问题标题" /><select v-model="issueForm.severity" class="field"><option>一般</option><option>重要</option><option>重大</option></select><button class="feishu-btn-primary" @click="createIssue">保存问题</button></div><textarea v-model="issueForm.description" class="field mt-2 min-h-[70px] w-full" placeholder="描述现象（可选）" /></div>

            <div class="grid gap-4 lg:grid-cols-2"><div class="panel panel-purple"><div class="panel-title">改善提案</div><div v-for="p in detail.proposals" :key="p.id" class="mt-2 rounded-lg bg-white px-3 py-2 text-xs"><b>{{ p.title }}</b><span class="ml-2 text-gray-400">{{ p.status }}</span></div><button class="mt-3 rounded-lg border border-purple-300 bg-white px-3 py-1.5 text-xs font-medium text-purple-700" @click="createProposal">快速登记改善提案</button></div><div class="panel panel-green"><div class="panel-title">知识沉淀</div><div v-for="k in detail.knowledge" :key="k.id" class="mt-2 rounded-lg bg-white px-3 py-2 text-xs"><b>{{ k.title }}</b><span class="ml-2 text-gray-400">{{ k.status === 'published' ? '已发布' : '草稿' }}</span></div><button class="mt-3 rounded-lg border border-green-300 bg-white px-3 py-1.5 text-xs font-medium text-green-700" @click="createKnowledge">记录本次经验</button></div></div>
          </div>
          <div v-else class="flex h-80 items-center justify-center text-sm text-gray-400">从左侧选择一条交付记录</div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { usePostLaunchOperationsPage } from "../features/demand-delivery/usePostLaunchOperationsPage"
const { loading, saving, showCreate, showIssue, route, rows, detail, selectedId, requirements, projects, createForm, issueForm, ownerName, summaryCards, summary, targetOptions, outcomeStatus, calculateSummary, refresh, select, saveOwner, createOperation, createIssue, updateIssue, createProposal, createKnowledge, copyOutcomeLink } = usePostLaunchOperationsPage()
</script>

<style scoped>
.field { border: 1px solid #d1d5db; border-radius: .65rem; background: white; padding: .6rem .75rem; font-size: .8rem; outline: none; }
.field:focus { border-color: #60a5fa; box-shadow: 0 0 0 2px #dbeafe; }
.info { display:flex; flex-direction:column; gap:.25rem; border-radius:.75rem; background:#f9fafb; padding:.75rem; } .info span { font-size:.7rem; color:#9ca3af; } .info b { font-size:.9rem; color:#374151; }
.panel { border-radius:.9rem; padding:1rem; border:1px solid; } .panel-blue { background:#eff6ff; border-color:#bfdbfe; } .panel-amber { background:#fffbeb; border-color:#fde68a; } .panel-purple { background:#f5f3ff; border-color:#ddd6fe; } .panel-green { background:#ecfdf5; border-color:#a7f3d0; } .panel-title { font-size:.85rem; font-weight:700; color:#111827; } .panel-help { margin-top:.3rem; font-size:.7rem; color:#6b7280; }
</style>
