<template>
  <div class="page-transition max-w-6xl">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-bold text-gray-900">开发工作台</h1>
        <p class="text-sm text-gray-500 mt-1">今天先处理什么，做完如何回写到 L3 底表。</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="openRequirementCreate" class="feishu-btn-primary px-4 shadow-sm">
          <ListPlus class="w-4 h-4" /> 登记工作
        </button>
        <button v-if="canCreateProject" @click="openProjectCreate" class="feishu-btn-primary px-4 shadow-sm">
          <Plus class="w-4 h-4" /> 新增项目
        </button>
        <button @click="openWorkReport" class="feishu-btn-ghost border border-gray-200 bg-white text-gray-600 hover:bg-gray-50">
          <FileText class="w-4 h-4" /> 周报 / 月报工作记录
        </button>
        <button @click="syncMine" class="feishu-btn-ghost border border-accent-200 bg-white text-accent-600 hover:bg-accent-50">
          <Send class="w-3.5 h-3.5" /> 同步我的进度
        </button>
      </div>
    </div>

    <div class="mb-5 flex items-center justify-between rounded-lg border border-accent-100 bg-accent-50/50 px-3 py-2">
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <span class="font-medium text-gray-700">当前视角</span>
        <button v-for="item in scopeOptions" :key="item.value" @click="setScope(item.value)"
          :class="['rounded-md px-3 py-1.5 font-medium transition-colors', viewScope === item.value ? 'bg-white text-accent-600 shadow-sm' : 'text-gray-500 hover:bg-white/70']">
          {{ item.label }}
        </button>
      </div>
      <div class="flex items-center gap-4">
        <span v-if="viewScope === 'mine'" class="text-xs text-gray-400">{{ currentUser.devOwnerName || '当前开发者' }} · 以我的安排为准</span>
        <router-link to="/products?view=work" class="text-xs font-medium text-accent-600 hover:text-accent-700">打开产品工作视图 →</router-link>
      </div>
    </div>

    <div class="grid grid-cols-4 gap-4 mb-6">
      <button v-for="card in summaryCards" :key="card.label" @click="setWorkFilter(card.key)"
        :class="['text-left rounded-xl border p-4 transition-all hover:-translate-y-0.5 hover:shadow-sm', card.className, workFilter === card.key ? 'ring-2 ring-accent-300 ring-offset-1' : '']">
        <p class="text-xs text-gray-500">{{ card.label }}</p>
        <p class="mt-1 text-2xl font-bold tabular-nums" :class="card.valueClass">{{ card.value }}</p>
        <p class="mt-1 text-[11px] text-gray-400">{{ card.desc }}</p>
        <p class="mt-2 text-[10px] font-medium text-accent-600">点击查看反馈 →</p>
      </button>
    </div>

    <!-- Team members: keep this available for team review, but stay out of the developer's primary work surface. -->
    <div v-if="viewScope === 'team'" class="mb-6">
      <div class="mb-3 flex items-center justify-between">
        <h2 class="text-sm font-semibold text-gray-900">团队工作摘要</h2>
        <span class="text-xs text-gray-400">点击成员可查看其工作范围</span>
      </div>
      <div class="grid grid-cols-3 gap-4">
      <div v-for="member in teamMembers" :key="member.name"
        :class="['feishu-card cursor-pointer transition-all border-2', activeMember === member.name ? 'border-accent-400' : 'border-transparent hover:border-gray-200']"
        @click="selectMember(member.name)">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold"
            :style="{ backgroundColor: member.color }">{{ member.name[0] }}</div>
          <div class="flex-1">
            <p class="text-sm font-medium text-gray-900">{{ member.name }}</p>
            <p class="text-xs text-gray-400">{{ member.role }}</p>
          </div>
          <div class="text-right">
            <p class="text-lg font-bold text-accent-500">{{ member.taskCount }}</p>
            <p class="text-[10px] text-gray-400">待办</p>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- Content area -->
    <div class="grid grid-cols-2 gap-6">
      <!-- My Requirements -->
      <div class="feishu-card">
        <div class="mb-3 flex items-start justify-between gap-3">
          <div>
            <h3 class="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <ClipboardList class="w-4 h-4 text-accent-500" /> {{ workFilterTitle }}
              <span class="text-xs text-gray-400 font-normal">({{ workList.length }})</span>
            </h3>
            <p class="mt-1 text-[11px] text-gray-400">从这里开始、推进和回写今天的工作</p>
          </div>
          <button @click="openRequirementCreate" class="feishu-btn-ghost text-accent-600 whitespace-nowrap"><ListPlus class="h-3.5 w-3.5" />登记</button>
        </div>
        <div class="mb-3 flex flex-wrap gap-1.5">
          <button v-for="item in workFilterOptions" :key="item.key" @click="setWorkFilter(item.key)"
            :class="['rounded-md px-2 py-1 text-[10px] font-medium transition-colors', workFilter === item.key ? 'bg-accent-50 text-accent-600' : 'bg-gray-50 text-gray-500 hover:bg-gray-100']">
            {{ item.label }}
          </button>
        </div>
        <div v-if="workList.length === 0" class="rounded-lg bg-gray-50 px-3 py-8 text-center text-xs text-gray-400">{{ emptyWorkText }}</div>
        <div v-for="r in workList.slice(0, 8)" :key="r.id"
          class="group flex items-center gap-3 rounded-lg border-b border-gray-50 px-2 py-2.5 transition-colors hover:bg-gray-50 last:border-0"
          @click="router.push('/requirements/' + r.id)">
          <div class="w-2 h-2 rounded-full flex-shrink-0" :style="{ backgroundColor: statusDot(r.status) }" />
          <div class="flex-1 min-w-0">
            <p class="text-xs font-medium text-gray-900 truncate">{{ r.title }}</p>
            <p class="mt-0.5 text-[10px] text-gray-400">{{ r.projectName }} · {{ r.type }} · {{ impactLabel(r) }} / {{ workloadLabel(r) }}</p>
          </div>
          <div class="hidden text-right sm:block">
            <p class="text-[10px] font-medium" :class="dueTone(r).className">{{ dueLabel(r) }}</p>
            <p class="mt-0.5 text-[10px] font-bold" :style="{ color: priorityColor(r.priority) }">{{ r.priority }}</p>
          </div>
          <span class="text-[10px] px-1.5 py-0.5 rounded" :style="{ backgroundColor: statusColor(r.status) + '20', color: statusColor(r.status) }">{{ statusLabel(r.status) }}</span>
          <span v-if="feedbackBadge(r)" :class="['rounded px-1.5 py-0.5 text-[10px] font-medium', feedbackBadge(r) === '反馈需处理' ? 'bg-rose-50 text-rose-600' : feedbackBadge(r) === '有新回执' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700']">{{ feedbackBadge(r) }}</span>
          <div class="flex flex-shrink-0 items-center gap-1 opacity-80 transition-opacity group-hover:opacity-100" @click.stop>
            <button v-if="r.status === '待处理'" @click="updateWorkStatus(r, '进行中')" class="rounded-md bg-blue-50 px-2 py-1 text-[10px] font-medium text-blue-600 hover:bg-blue-100">开始</button>
            <button v-else-if="r.status === '进行中'" @click="openDeliveryCard(r)" class="rounded-md bg-amber-50 px-2 py-1 text-[10px] font-medium text-amber-600 hover:bg-amber-100">准备交付</button>
            <button v-else-if="r.status === '待交付'" @click="openDeliveryCard(r)" class="rounded-md bg-emerald-50 px-2 py-1 text-[10px] font-medium text-emerald-600 hover:bg-emerald-100">交付确认</button>
            <button v-if="['已交付', '已关闭'].includes(r.status)" @click="openFeedbackPanel(r)" class="rounded-md bg-violet-50 px-2 py-1 text-[10px] font-medium text-violet-600 hover:bg-violet-100">上线反馈</button>
            <button @click="openWorkLog(r)" class="rounded-md border border-gray-200 px-2 py-1 text-[10px] text-gray-500 hover:border-accent-200 hover:text-accent-600">记录</button>
            <button @click="router.push('/requirements/' + r.id)" class="rounded-md border border-gray-200 px-2 py-1 text-[10px] text-gray-500 hover:border-accent-200 hover:text-accent-600">详情</button>
          </div>
        </div>
        <div v-if="workList.length > 8" class="mt-3 border-t border-gray-100 pt-2 text-right">
          <router-link to="/products?view=work" class="text-xs text-accent-600">查看全部产品工作 →</router-link>
        </div>
      </div>

      <!-- My Projects -->
      <div class="feishu-card">
        <div class="mb-3 flex items-start justify-between gap-3">
          <div>
            <h3 class="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <FolderKanban class="w-4 h-4 text-accent-500" /> 需要关注的项目
              <span class="text-xs text-gray-400 font-normal">({{ focusProjects.length }})</span>
            </h3>
            <p class="mt-1 text-[11px] text-gray-400">只保留正在推进或仍有当前工作的项目</p>
          </div>
          <router-link to="/products?view=mine" class="text-xs font-medium text-accent-600 whitespace-nowrap">全部 {{ myProjects.length }} 个 →</router-link>
        </div>
        <div v-if="focusProjects.length === 0" class="rounded-lg bg-gray-50 px-3 py-8 text-center text-xs text-gray-400">当前没有待推进项目，可从“全部项目”查看历史项目</div>
        <div v-for="p in focusProjects" :key="p.id"
          class="flex items-center gap-3 py-2 px-2 rounded-lg hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-0 transition-colors"
          @click="router.push('/projects/' + p.id)">
          <div class="flex-1 min-w-0">
            <p class="text-xs font-medium text-gray-900 truncate">{{ p.name }}</p>
            <p class="text-[10px] text-gray-400">{{ p.department }} · {{ p.currentVersion }}</p>
          </div>
          <div class="w-20">
            <div class="progress-bar h-2">
              <div class="progress-fill" :style="{ width: projectProgressPercent(p) + '%', backgroundColor: projectProgressColor(p) }" />
            </div>
            <p class="mt-0.5 text-[10px] text-gray-400 truncate">{{ p.progress?.label || '进度' }}</p>
          </div>
          <span class="text-[10px] font-semibold text-gray-600 tabular-nums">{{ projectProgressPercent(p) }}%</span>
        </div>
        <div v-if="completedProjectCount" class="mt-3 border-t border-gray-100 pt-2 text-xs text-gray-400">
          已交付项目 {{ completedProjectCount }} 个，已收起；需要复盘时进入全部项目查看。
        </div>
      </div>
    </div>

    <section ref="pendingSection" class="mt-6 rounded-xl border border-blue-200 bg-white p-4">
      <div class="flex items-center justify-between"><div><h2 class="text-sm font-semibold">待我处理</h2><p class="mt-1 text-[11px] text-gray-400">需求分派、业务回复、共享动态等动作统一在这里处理。</p></div><button class="text-xs text-blue-700" @click="refreshCollaborationTodos">刷新</button></div>
      <p v-if="!collaborationTodos.length" class="mt-3 text-xs text-gray-500">当前没有待处理事项。</p>
      <div class="mt-3 max-h-72 space-y-2 overflow-y-auto">
        <div v-for="todo in collaborationTodos" :key="todo.id" class="flex items-center gap-3 rounded-lg border border-gray-200 p-3 hover:border-blue-400">
          <button class="min-w-0 flex-1 text-left" @click="openTodo(todo)"><p class="text-sm font-medium text-gray-900">{{ todo.requirementTitle || todo.title || '待处理事项' }}</p><p class="mt-1 text-xs text-gray-500">{{ todo.message || '请打开详情继续处理' }}</p></button>
          <span class="shrink-0 rounded bg-gray-50 px-2 py-1 text-[10px] text-gray-500">{{ todoTypeLabel(todo) }}</span>
          <button class="shrink-0 rounded-md border border-gray-200 px-2 py-1 text-[10px] text-gray-500 hover:border-emerald-200 hover:text-emerald-600" @click="completeTodo(todo)">完成</button>
        </div>
      </div>
    </section>
    <div class="mt-6 flex items-center justify-between rounded-lg border border-gray-100 bg-white px-4 py-3 text-xs text-gray-500">
      <span>工作台负责安排和推进；每次动作都会回写 L3 底表，成果总览再按产品生命周期呈现。</span>
      <div class="flex items-center gap-4">
        <span class="text-gray-400">待处理事项已统一到本工作台</span>
        <router-link to="/requirements" class="text-accent-600 hover:text-accent-700">进入需求底库 →</router-link>
      </div>
    </div>

    <div v-if="showRequirementModal" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4" @click.self="showRequirementModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6 animate-scale-in">
        <div class="mb-4 flex items-start justify-between">
          <div><h3 class="font-semibold text-gray-900">登记存量产品迭代</h3><p class="mt-1 text-xs text-gray-400">创建一条归属于现有 L2 的独立 L3，不重新走需求提报流程。</p></div>
          <button class="feishu-icon-btn" title="关闭" @click="showRequirementModal = false"><X class="h-4 w-4" /></button>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2"><label class="text-xs text-gray-500">工作标题 *</label><input v-model="quickRequirementForm.title" class="feishu-input w-full mt-1" placeholder="例如：新增合同用印单独使用场景支持" /></div>
          <div class="col-span-2"><label class="text-xs text-gray-500">所属项目 *</label><select v-model="quickRequirementForm.projectId" class="feishu-input w-full mt-1"><option value="">请选择项目</option><option v-for="p in projectOptions" :key="p.id" :value="p.id">{{ p.name }}</option></select></div>
          <div><label class="text-xs text-gray-500">工作类型</label><select v-model="quickRequirementForm.type" class="feishu-input w-full mt-1"><option v-for="item in quickTypeOptions" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">优先级</label><select v-model="quickRequirementForm.priority" class="feishu-input w-full mt-1"><option v-for="item in ['P0','P1','P2','P3']" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">产品价值</label><select v-model="quickRequirementForm.impactLevel" class="feishu-input w-full mt-1"><option v-for="item in ['核心','重要','常规']" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">工作量</label><select v-model="quickRequirementForm.workloadLevel" class="feishu-input w-full mt-1"><option v-for="item in ['大','中','小']" :key="item" :value="item">{{ item }}工作量</option></select></div>
          <div><label class="text-xs text-gray-500">当前状态</label><select v-model="quickRequirementForm.status" class="feishu-input w-full mt-1"><option v-for="item in requirementStatuses" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">预计交付时间 *</label><input v-model="quickRequirementForm.expectedDeliveryTime" type="date" class="feishu-input w-full mt-1" /></div>
          <div class="col-span-2"><label class="text-xs text-gray-500">改动与预期结果 *</label><textarea v-model="quickRequirementForm.description" class="feishu-input w-full mt-1" rows="3" placeholder="简要说明这次迭代改什么、完成后带来什么结果"></textarea></div>
          <div class="col-span-2"><label class="text-xs text-gray-500">验收标准 *</label><textarea v-model="quickRequirementForm.acceptanceCriteria" class="feishu-input w-full mt-1" rows="2" placeholder="写一句可验证的完成标准"></textarea></div>
        </div>
        <div class="mt-5 flex justify-end gap-3">
          <button @click="showRequirementModal = false" class="feishu-btn-ghost text-sm">取消</button>
          <button @click="saveQuickRequirement" class="feishu-btn-primary text-sm" :disabled="requirementSaving">{{ requirementSaving ? '登记中...' : '登记并开始' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showWorkLogModal" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4" @click.self="showWorkLogModal = false">
      <div class="flex max-h-[86vh] w-full max-w-xl flex-col overflow-hidden rounded-xl bg-white shadow-xl animate-scale-in">
        <div class="flex items-start justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <h3 class="font-semibold text-gray-900">记录今日进展</h3>
            <p class="mt-1 max-w-[430px] truncate text-xs text-gray-400">{{ activeRequirement?.title }} · {{ activeRequirement?.projectName }} · 默认仅 IT/管理侧可见</p>
          </div>
          <button class="feishu-icon-btn" title="关闭" @click="showWorkLogModal = false"><X class="h-4 w-4" /></button>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto px-6 py-4">
          <div v-if="activeRequirement" class="space-y-4">
            <div class="rounded-xl border border-accent-100 bg-accent-50/40 p-4">
              <div class="grid gap-3 sm:grid-cols-[150px_1fr]">
                <label class="block text-xs text-gray-600">动态类型<select v-model="workLogForm.logType" class="feishu-input mt-1 w-full"><option v-for="item in workLogTypes" :key="item" :value="item">{{ item }}</option></select></label>
                <label class="block text-xs text-gray-600">今日进展 <span class="text-rose-500">*</span><textarea v-model="workLogForm.content" rows="3" maxlength="5000" class="feishu-input mt-1 w-full" placeholder="一句话说明今天实际推进了什么" /></label>
              </div>
              <div class="mt-3 flex items-center justify-between gap-3"><span class="text-[11px] text-gray-400">这条记录会进入个人日报和本周工作汇报，不会自动发送给业务人员。</span><button type="button" class="feishu-btn-primary text-xs" :disabled="workLogSaving" @click="saveWorkLog">{{ workLogSaving ? '保存中...' : '保存今日进展' }}</button></div>
            </div>
            <div>
              <p class="mb-2 text-xs font-semibold text-gray-700">历史进展</p>
              <div v-if="workLogLoading" class="py-6 text-center text-xs text-gray-400">加载中...</div>
              <div v-else-if="!workLogs.length" class="rounded-lg bg-gray-50 px-3 py-6 text-center text-xs text-gray-400">暂无工作进展</div>
              <div v-else class="space-y-2"><div v-for="log in workLogs" :key="log.id" class="rounded-lg border border-gray-100 bg-white px-3 py-2.5"><div class="flex items-center justify-between gap-2"><span class="text-[11px] font-medium text-accent-600">{{ log.logType || '工作进展' }}</span><span class="text-[10px] text-gray-400">{{ log.workDate || log.occurredAt || log.createdAt }}</span></div><p class="mt-1 whitespace-pre-wrap text-xs leading-5 text-gray-700">{{ log.content }}</p></div></div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 border-t border-gray-100 px-6 py-4">
          <button @click="showWorkLogModal = false" class="feishu-btn-ghost text-sm">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showDeliveryModal" class="fixed inset-0 z-[55] flex items-center justify-center bg-black/35 p-4" @click.self="closeDeliveryCard">
      <div class="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl animate-scale-in">
        <div class="flex items-start justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <p class="text-[11px] font-medium text-accent-600">交付工作卡</p>
            <h3 class="mt-1 font-semibold text-gray-900">{{ deliveryRequirement?.title }}</h3>
            <p class="mt-1 text-xs text-gray-400">{{ deliveryRequirement?.projectName }} · {{ deliveryRequirement?.id }}</p>
          </div>
          <button class="feishu-icon-btn" title="关闭" @click="closeDeliveryCard"><X class="h-4 w-4" /></button>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto px-6 py-5">
          <div v-if="deliveryError" role="alert" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">{{ deliveryError }}</div>
          <div v-if="deliveryNotice" role="status" class="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs leading-5 text-emerald-800">{{ deliveryNotice }}</div>
          <div v-if="deliveryLoading" class="flex h-40 items-center justify-center"><div class="h-7 w-7 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" /></div>
          <template v-else-if="deliveryLifecycle">
            <div class="grid gap-2 sm:grid-cols-3">
              <div class="rounded-lg border border-blue-200 bg-blue-50/70 p-3"><p class="text-[10px] text-blue-600">1 · 验收标准</p><p class="mt-1 text-xs font-semibold text-blue-900">{{ deliveryBaseline?.versionLabel || '尚未确认' }}</p></div>
              <div :class="['rounded-lg border p-3', deliveryRequirement?.status === '待交付' ? 'border-amber-200 bg-amber-50/70' : latestDeliveryChangeRound ? 'border-orange-200 bg-orange-50/70' : 'border-gray-200 bg-gray-50']"><p class="text-[10px] text-gray-500">2 · 业务确认</p><p class="mt-1 text-xs font-semibold text-gray-800">{{ deliveryRequirement?.status === '待交付' ? (passedDeliveryRound ? '已确认，待上线' : '等待业务回复') : latestDeliveryChangeRound ? '上轮需修改，待重发' : '待发起' }}</p></div>
              <div class="rounded-lg border border-gray-200 bg-gray-50 p-3"><p class="text-[10px] text-gray-500">3 · 交付上线</p><p class="mt-1 text-xs font-semibold text-gray-800">{{ deliveryRequirement?.status === '已交付' ? '已完成' : '待完成' }}</p></div>
            </div>

            <section v-if="deliveryRequirement?.status === '进行中'" class="mt-5 rounded-xl border border-amber-200 bg-amber-50/40 p-4">
              <h4 class="text-sm font-semibold text-gray-900">准备本次交付</h4>
              <p class="mt-1 text-xs leading-5 text-gray-500">系统会带出已确认的上线前验收标准。这里填写实际做出的结果，再生成业务确认链接。</p>
              <div v-if="latestDeliveryChangeRound" class="mt-3 rounded-lg border border-orange-200 bg-orange-50 px-3 py-3 text-xs leading-5 text-orange-800"><p class="font-semibold">上一轮业务反馈需要修改</p><p v-if="latestDeliveryChangeRound.feedback?.feedbackTypeLabel" class="mt-1">反馈类型：{{ latestDeliveryChangeRound.feedback.feedbackTypeLabel }}</p><p v-if="latestDeliveryChangeRound.feedback?.routeTypeLabel" class="mt-1">处理路由：{{ latestDeliveryChangeRound.feedback.routeTypeLabel }}</p><p class="mt-1">原上线前验收标准仍然有效。请根据业务反馈完成调整，填写本轮实际交付结果后重新发起确认。</p><p v-if="latestDeliveryChangeRound.response?.content" class="mt-1 whitespace-pre-wrap text-orange-700">业务反馈：{{ latestDeliveryChangeRound.response.content }}</p><div v-if="latestDeliveryChangeRound.feedback?.routeType === 'it_review'" class="mt-3 flex flex-wrap gap-2"><button type="button" class="feishu-btn-ghost text-xs" :disabled="deliverySaving" @click="routeDeliveryFeedback('same_l3_rework')">按当前 L3 整改</button><button type="button" class="feishu-btn-ghost text-xs" :disabled="deliverySaving" @click="routeDeliveryFeedback('new_l3_feature')">新建功能 L3</button><button type="button" class="feishu-btn-ghost text-xs" :disabled="deliverySaving" @click="routeDeliveryFeedback('new_l3_restructure')">新建需求重构 L3</button></div></div>
              <div v-if="deliveryBaseline" class="mt-3 rounded-lg border border-blue-200 bg-blue-50 px-3 py-3 text-xs leading-5 text-blue-900">
                <p class="font-semibold">{{ deliveryBaseline.versionLabel }} · {{ deliveryBaseline.templateLabel }}</p>
                <p class="mt-2"><span class="text-blue-600">交付范围：</span>{{ deliveryBaseline.content?.scope }}</p>
                <p class="mt-1"><span class="text-blue-600">验证场景：</span>{{ deliveryBaseline.content?.scenarios }}</p>
                <p class="mt-1"><span class="text-blue-600">通过条件：</span>{{ deliveryBaseline.content?.expected }}</p>
              </div>
              <div v-else class="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-3 text-xs leading-5 text-rose-700">当前 L3 没有已确认的上线前验收标准，不能直接发起交付。请先回到需求详情补齐标准。</div>
              <div class="mt-4 space-y-3">
                <label class="block text-xs text-gray-600">实际交付结果 <span class="text-rose-500">*</span><textarea v-model="deliveryPreparation.actualResult" rows="4" maxlength="10000" class="feishu-input mt-1 w-full resize-y" placeholder="说明已经完成的功能、页面、流程或应用现状，可直接粘贴文字" /></label>
                <label class="block text-xs text-gray-600">验证证据 / 截图说明 <span class="font-normal text-gray-400">（可选）</span><textarea v-model="deliveryPreparation.evidence" rows="3" maxlength="5000" class="feishu-input mt-1 w-full resize-y" placeholder="填写测试结果、访问地址、截图说明或附件位置；图片可在工作动态中补充" /></label>
                <label class="block text-xs text-gray-600">已知问题或交付限制 <span class="font-normal text-gray-400">（可选）</span><textarea v-model="deliveryPreparation.knownIssues" rows="2" maxlength="3000" class="feishu-input mt-1 w-full resize-y" placeholder="没有可填写“无”" /></label>
              </div>
            </section>

            <section v-else-if="deliveryRequirement?.status === '待交付'" class="mt-5 rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
              <h4 class="text-sm font-semibold text-gray-900">交付确认</h4>
              <template v-if="passedDeliveryRound">
                <p class="mt-1 text-xs leading-5 text-emerald-700">业务已确认本轮交付，完成最后一步后即可登记上线并建立回访。</p>
                <div class="mt-3 rounded-lg border border-emerald-200 bg-white px-3 py-3 text-xs leading-5"><p class="font-semibold text-gray-800">{{ passedDeliveryRound.snapshot.title }}</p><p class="mt-1 whitespace-pre-wrap text-gray-600">{{ passedDeliveryRound.response?.content || '业务确认通过' }}</p></div>
                <div class="mt-4 grid gap-3 sm:grid-cols-2"><label class="block text-xs text-gray-600">交付形式<select v-model="deliveryCompletion.deliveryKind" class="feishu-input mt-1 w-full"><option>上线</option><option>试运行</option><option>已交付</option></select></label><label class="block text-xs text-gray-600">实际开始使用日期（默认交付确认日）<input v-model="deliveryCompletion.useStartDate" type="date" class="feishu-input mt-1 w-full" /><span class="mt-1 block text-[10px] text-gray-400">业务确认交付后实际可用的日期；修改后会重新计算 3 天和 30 天节点。</span></label></div>
                <label class="mt-3 block text-xs text-gray-600">上线说明 <span class="font-normal text-gray-400">（可选）</span><textarea v-model="deliveryCompletion.notes" rows="3" maxlength="5000" class="feishu-input mt-1 w-full resize-y" placeholder="填写上线版本、访问入口或需要业务注意的事项" /></label>
              </template>
              <template v-else>
                <p class="mt-1 text-xs leading-5 text-amber-700">交付确认链接已发给业务，等待业务确认。业务如提出修改，需求会自动回到进行中。</p>
                <div v-if="pendingDeliveryRound" class="mt-3 rounded-lg border border-amber-200 bg-white px-3 py-3 text-xs leading-5"><p class="font-semibold text-gray-800">{{ pendingDeliveryRound.snapshot.title }}</p><p class="mt-1 text-gray-500">发送于 {{ pendingDeliveryRound.createdAt }} · 有效至 {{ pendingDeliveryRound.expiresAt }}</p><button v-if="pendingDeliveryRound.link" type="button" class="mt-2 text-blue-700 underline" @click="copyDeliveryLink(pendingDeliveryRound.link)">复制业务确认链接</button></div>
                <button type="button" class="feishu-btn-ghost mt-3 text-xs" :disabled="deliveryLoading" @click="loadDeliveryCard(deliveryRequirement)">刷新业务回复</button>
              </template>
            </section>
          </template>
        </div>
        <div class="flex justify-end gap-2 border-t border-gray-100 px-6 py-4">
          <button type="button" class="feishu-btn-ghost text-sm" @click="closeDeliveryCard">关闭</button>
          <button v-if="deliveryRequirement?.status === '进行中'" type="button" class="feishu-btn-primary text-sm" :disabled="deliverySaving || !deliveryBaseline || pendingFeedbackRoute" @click="sendDeliveryConfirmation">{{ deliverySaving ? '发送中...' : pendingFeedbackRoute ? '请先确认反馈路由' : '生成交付确认链接' }}</button>
          <button v-else-if="deliveryRequirement?.status === '待交付' && passedDeliveryRound" type="button" class="feishu-btn-primary text-sm" :disabled="deliverySaving" @click="completeDelivery">{{ deliverySaving ? '保存中...' : '确认交付并上线' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showFeedbackModal" class="fixed inset-0 z-[58] flex items-center justify-center bg-black/35 p-4" @click.self="closeFeedbackPanel">
      <div class="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl animate-scale-in">
        <div class="flex items-start justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <p class="text-[11px] font-medium text-violet-600">上线反馈工作卡</p>
            <h3 class="mt-1 font-semibold text-gray-900">{{ feedbackRequirement?.title }}</h3>
            <p class="mt-1 text-xs text-gray-400">{{ feedbackRequirement?.projectName }} · {{ feedbackRequirement?.id }}</p>
          </div>
          <button class="feishu-icon-btn" title="关闭" @click="closeFeedbackPanel"><X class="h-4 w-4" /></button>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto px-6 py-5">
          <div v-if="feedbackError" role="alert" class="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs leading-5 text-rose-700">{{ feedbackError }}</div>
          <div v-if="feedbackLoading" class="flex h-40 items-center justify-center"><div class="h-7 w-7 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" /></div>
          <template v-else-if="feedbackDetail">
            <div class="mb-4 rounded-lg border border-violet-100 bg-violet-50/60 px-4 py-3 text-xs text-violet-900">
              <div class="flex flex-wrap items-center justify-between gap-2"><span class="font-semibold">交付后业务反馈</span><router-link :to="'/requirements/' + (feedbackDetail.requirementId || feedbackRequirement?.id)" class="font-medium text-violet-700 hover:text-violet-900">打开 L3 详情 →</router-link></div>
              <p class="mt-1 text-violet-700">实际开始使用日期：{{ feedbackDetail.useStartDate || feedbackDetail.deliveryDate || '未设置' }}。系统以此日期计算 3 天回执和 30 天价值验证。</p>
            </div>
            <div class="space-y-3">
              <div v-for="entry in feedbackStageItems" :key="entry.stage" :class="['rounded-xl border p-4', entry.item?.status === 'submitted' && !entry.item?.viewedAt ? 'border-amber-200 bg-amber-50/40' : 'border-gray-200 bg-white']">
                <div class="flex flex-wrap items-start justify-between gap-2">
                  <div><p class="text-sm font-semibold text-gray-900">{{ entry.label }}</p><p class="mt-1 text-[11px] text-gray-400">计划日期：{{ entry.dueDate || '未设置' }}</p></div>
                  <span :class="['rounded-full px-2 py-1 text-[10px] font-medium', outcomeStatusClass(entry.item)]">{{ outcomeStatusText(entry.item) }}</span>
                </div>
                <div v-if="entry.item?.status === 'pending'" class="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
                  <span class="text-[11px] text-gray-500">业务还没有提交本次反馈</span>
                  <div class="flex items-center gap-2"><button v-if="entry.item?.link" type="button" class="feishu-btn-ghost text-[11px]" @click="copyOutcomeLink(entry.item.link)">复制链接</button><button v-if="entry.item?.id" type="button" class="feishu-btn-primary text-[11px]" :disabled="sendingOutcomeId === entry.item.id" @click="sendFeedbackLink(entry.item)">{{ sendingOutcomeId === entry.item.id ? '发送中...' : '直接发送' }}</button></div>
                </div>
                <div v-else-if="entry.item?.status === 'submitted'" class="mt-3 rounded-lg border border-gray-100 bg-gray-50 px-3 py-3 text-xs leading-5 text-gray-700">
                  <p>{{ outcomeSummary(entry.item) || '业务已提交反馈' }}</p>
                  <p v-if="entry.item.responseSnapshot?.summary" class="mt-1 whitespace-pre-wrap text-gray-600">{{ entry.item.responseSnapshot.summary }}</p>
                  <div class="mt-2 flex flex-wrap items-center justify-between gap-2"><span class="text-[10px] text-gray-400">提交于 {{ entry.item.submittedAt || '—' }}</span><button v-if="!entry.item.viewedAt" type="button" class="feishu-btn-ghost text-[11px] text-amber-700" @click="markFeedbackViewed(entry.item)">标记已查看</button><span v-else class="text-[10px] text-emerald-600">已查看 {{ entry.item.viewedAt }}</span></div>
                </div>
                <div v-else class="mt-3 text-xs text-gray-400">当前没有生成此阶段的反馈请求，请检查业务负责人。</div>
              </div>
            </div>
            <div v-if="feedbackDetail.openIssueCount" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">已有 {{ feedbackDetail.openIssueCount }} 条反馈问题待处理，请在 L3 动态和问题台账中继续闭环。</div>
          </template>
        </div>
        <div class="flex justify-end border-t border-gray-100 px-6 py-4"><button type="button" class="feishu-btn-ghost text-sm" @click="closeFeedbackPanel">关闭</button></div>
      </div>
    </div>

    <div v-if="showProjectModal" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center" @click.self="showProjectModal = false">
      <div class="bg-white rounded-xl shadow-xl w-[560px] p-6 animate-scale-in">
        <div class="mb-4 flex items-start justify-between">
          <div><h3 class="font-semibold text-gray-900">工作台快速新建项目</h3><p class="mt-1 text-xs text-gray-400">创建后会立即进入需求列表、产品进展和成果总览。</p></div>
          <button class="feishu-icon-btn" title="关闭" @click="showProjectModal = false"><X class="h-4 w-4" /></button>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2"><label class="text-xs text-gray-500">项目名称 *</label><input v-model="projectForm.name" class="feishu-input w-full mt-1" placeholder="例如：发票自动报销系统" /></div>
          <div><label class="text-xs text-gray-500">优先级</label><select v-model="projectForm.priority" class="feishu-input w-full mt-1"><option v-for="item in ['P0','P1','P2','P3']" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">项目状态</label><select v-model="projectForm.status" class="feishu-input w-full mt-1"><option v-for="item in lifecycleStatuses" :key="item" :value="item">{{ statusLabel(item) }}</option></select></div>
          <div><label class="text-xs text-gray-500">归属部门 *</label><input v-model="projectForm.department" class="feishu-input w-full mt-1" placeholder="填写归属部门" /></div>
          <div><label class="text-xs text-gray-500">开发负责人 *</label><select v-model="projectForm.devOwner" class="feishu-input w-full mt-1"><option value="">请选择</option><option v-for="item in developerOptions" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">当前版本</label><input v-model="projectForm.currentVersion" class="feishu-input w-full mt-1" /></div>
          <div><label class="text-xs text-gray-500">目标结束时间 *</label><input v-model="projectForm.targetEndDate" type="date" class="feishu-input w-full mt-1" /></div>
          <div class="col-span-2"><label class="text-xs text-gray-500">项目说明</label><textarea v-model="projectForm.description" class="feishu-input w-full mt-1" rows="3" placeholder="填写项目目标或背景"></textarea></div>
        </div>
        <div class="mt-5 flex justify-end gap-3">
          <button @click="showProjectModal = false" class="feishu-btn-ghost text-sm">取消</button>
          <button @click="saveProject" class="feishu-btn-primary text-sm" :disabled="projectSaving">{{ projectSaving ? '创建中...' : '创建项目' }}</button>
        </div>
      </div>
    </div>

    <div v-if="reportOpen" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4" @click.self="reportOpen = false">
      <div class="flex max-h-[88vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
        <div class="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <h2 class="text-lg font-bold text-gray-900">工作记录快速生成</h2>
            <p class="mt-1 text-xs text-gray-400">按 L2 项目归集 L3 新增、完成和状态变化，可直接用于周报或月度工作核算。</p>
          </div>
          <button class="feishu-icon-btn" title="关闭" @click="reportOpen = false"><X class="h-4 w-4" /></button>
        </div>
        <div class="flex items-center justify-between border-b border-gray-100 px-6 py-3">
          <div class="flex rounded-lg bg-gray-100 p-0.5">
            <button @click="loadWorkReport('week')" :class="['rounded-md px-3 py-1.5 text-xs font-medium', reportPeriod === 'week' ? 'bg-white text-accent-600 shadow-sm' : 'text-gray-500']">本周</button>
            <button @click="loadWorkReport('month')" :class="['rounded-md px-3 py-1.5 text-xs font-medium', reportPeriod === 'month' ? 'bg-white text-accent-600 shadow-sm' : 'text-gray-500']">本月</button>
          </div>
          <button v-if="workReport" class="feishu-btn-ghost text-xs text-accent-600" @click="copyWorkReport"><Copy class="h-3.5 w-3.5" /> 复制工作记录</button>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto p-6">
          <div v-if="reportLoading" class="flex h-48 items-center justify-center"><div class="h-7 w-7 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" /></div>
          <template v-else-if="workReport">
            <div class="mb-5 flex items-end justify-between">
              <div><h3 class="text-base font-semibold text-gray-900">{{ workReport.title }}</h3><p class="mt-1 text-xs text-gray-400">{{ workReport.rangeLabel }} · 生成于 {{ workReport.generatedAt }}</p></div>
            </div>
            <div class="grid grid-cols-4 gap-3">
              <div class="rounded-lg border border-blue-100 bg-blue-50/50 p-3"><p class="text-xs text-gray-500">新增 L2 项目</p><p class="mt-1 text-xl font-bold text-accent-600">{{ workReport.summary.newProjects }}</p></div>
              <div class="rounded-lg border border-violet-100 bg-violet-50/50 p-3"><p class="text-xs text-gray-500">新增 L3 需求</p><p class="mt-1 text-xl font-bold text-violet-600">{{ workReport.summary.newRequirements }}</p></div>
              <div class="rounded-lg border border-emerald-100 bg-emerald-50/50 p-3"><p class="text-xs text-gray-500">完成/归档</p><p class="mt-1 text-xl font-bold text-emerald-600">{{ workReport.summary.completedRequirements }}</p></div>
              <div class="rounded-lg border border-amber-100 bg-amber-50/50 p-3"><p class="text-xs text-gray-500">状态变化</p><p class="mt-1 text-xl font-bold text-amber-600">{{ workReport.summary.statusChanges }}</p></div>
            </div>
            <section class="mt-6">
              <h4 class="mb-2 text-sm font-semibold text-gray-800">新增 L2 项目</h4>
              <div v-if="workReport.newProjects.length" class="space-y-2">
                <div v-for="project in workReport.newProjects" :key="project.id" class="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 text-sm">
                  <span class="font-medium text-gray-800">{{ project.name }}</span><span class="text-xs text-gray-500">{{ project.status }}</span>
                </div>
              </div>
              <p v-else class="rounded-lg bg-gray-50 px-3 py-3 text-xs text-gray-400">本统计周期没有新增 L2 项目。</p>
            </section>
            <section class="mt-5">
              <h4 class="mb-2 text-sm font-semibold text-gray-800">L2 项目状态变化</h4>
              <div v-if="workReport.projectChanges?.length" class="space-y-2">
                <div v-for="project in workReport.projectChanges" :key="project.id" class="rounded-lg border border-amber-100 bg-amber-50/40 px-3 py-2 text-sm text-gray-700"><strong class="text-gray-900">{{ project.name }}</strong>，{{ project.text }}</div>
              </div>
              <p v-else class="rounded-lg bg-gray-50 px-3 py-3 text-xs text-gray-400">本统计周期没有 L2 项目状态变化。</p>
            </section>
            <section class="mt-6">
              <h4 class="mb-2 text-sm font-semibold text-gray-800">L2 项目下的 L3 工作记录</h4>
              <div v-if="workReport.groups.length" class="space-y-3">
                <div v-for="group in workReport.groups" :key="group.projectName" class="rounded-lg border border-accent-100 border-l-4 border-l-accent-400 bg-slate-50/50 p-4">
                  <p class="mb-2 text-sm font-semibold text-gray-800">{{ group.projectName }}</p>
                  <ol class="space-y-2 pl-5 text-sm text-gray-600">
                    <li v-for="item in group.items" :key="item.title + item.text" class="pl-1"><strong class="text-gray-900">{{ item.title }}</strong>，{{ item.text }}</li>
                  </ol>
                </div>
              </div>
              <p v-else class="rounded-lg bg-gray-50 px-3 py-3 text-xs text-gray-400">本统计周期没有新增或发生状态变化的 L3 需求。</p>
            </section>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ClipboardList, FolderKanban, Send, FileText, Copy, X, Plus, ListPlus } from 'lucide-vue-next'
import { useWorkspacePage } from "../features/demand-delivery/useWorkspacePage"
const { router, route, activeMember, reqs, collaborationTodos, pendingSection, postlaunchRows, sendingOutcomeId, sendState, refreshCollaborationTodos, todoTypeLabel, openTodo, completeTodo, projects, reportOpen, reportLoading, reportPeriod, workReport, viewScope, showProjectModal, projectSaving, developerOptions, projectForm, showRequirementModal, requirementSaving, quickRequirementForm, showWorkLogModal, workLogLoading, workLogSaving, activeRequirement, workLogs, workLogForm, showDeliveryModal, deliveryLoading, deliverySaving, deliveryError, deliveryNotice, deliveryRequirement, deliveryLifecycle, deliveryPreparation, deliveryCompletion, showFeedbackModal, feedbackLoading, feedbackError, feedbackRequirement, feedbackDetail, workFilter, scopeOptions, lifecycleStatuses, requirementStatuses, quickTypeOptions, workLogTypes, workFilterOptions, currentUser, canCreateProject, deliveryBaseline, pendingDeliveryRound, passedDeliveryRound, latestDeliveryChangeRound, pendingFeedbackRoute, teamMembers, selectMember, copyOutcomeLink, sendOutcomeLink, openFeedbackPanel, closeFeedbackPanel, sendFeedbackLink, markFeedbackViewed, applyCurrentUser, searchName, myReqs, activeReqs, recentDoneReqs, dueAttentionReqs, feedbackRequests, completedReqs, feedbackPendingReqs, feedbackUnreadReqs, feedbackIssueReqs, feedbackStageItems, workList, workFilterTitle, emptyWorkText, summaryCards, setScope, myProjects, focusProjects, completedProjectCount, projectOptions, projectNeedsAttention, setWorkFilter, feedbackForRequirement, feedbackNeedsAttention, feedbackBadge, outcomeStatusClass, outcomeStatusText, outcomeSummary, statusDot, priorityColor, statusColor, statusLabel, dateKey, dateOffsetKey, isDueWithin, dueTone, dueLabel, impactLabel, workloadLabel, projectProgressPercent, projectProgressColor, updateWorkStatus, deliveryToday, loadDeliveryCard, openDeliveryCard, closeDeliveryCard, sendDeliveryConfirmation, routeDeliveryFeedback, completeDelivery, copyDeliveryLink, openRequirementCreate, saveQuickRequirement, openWorkLog, saveWorkLog, syncMine, openProjectCreate, saveProject, openWorkReport, loadWorkReport, copyWorkReport } = useWorkspacePage()
</script>

