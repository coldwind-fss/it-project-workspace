<template>
  <div class="requirements-page page-transition flex h-full min-h-0 flex-col">
    <!-- Title + toolbar -->
    <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
      <h1 class="text-lg font-bold text-gray-900">需求列表</h1>
      <div class="flex flex-wrap items-center justify-end gap-1.5">
        <div class="relative">
          <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
          <input v-model="searchText" placeholder="搜索名称/负责人..." class="feishu-input pl-8 w-48" />
        </div>
        <div class="relative">
          <button type="button" class="feishu-btn-ghost text-xs text-gray-600" @click="filterPanelOpen = !filterPanelOpen">
            <Filter class="w-3.5 h-3.5" /> 筛选
            <span v-if="activeFilterCount" class="rounded-full bg-accent-500 px-1.5 py-0.5 text-[10px] leading-none text-white">{{ activeFilterCount }}</span>
          </button>
          <div v-if="filterPanelOpen" class="absolute right-0 top-full z-30 mt-2 w-[min(440px,calc(100vw-2rem))] rounded-xl border border-gray-200 bg-white p-3 text-left shadow-xl">
            <div class="mb-2 flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-700">筛选项目</span>
              <button v-if="activeFilterCount" type="button" class="text-[11px] text-accent-600 hover:text-accent-700" @click="clearFilters">清空筛选</button>
            </div>
            <div class="grid max-h-72 grid-cols-2 gap-3 overflow-y-auto pr-1">
              <fieldset>
                <legend class="mb-1 text-[11px] font-medium text-gray-400">所属大类</legend>
                <label v-for="c in categories" :key="c.id" class="flex cursor-pointer items-center gap-1.5 py-0.5 text-xs text-gray-600">
                  <input v-model="filters.categoryIds" type="checkbox" :value="c.id" class="rounded border-gray-300 text-accent-500" />
                  <span class="truncate">{{ c.name }}</span>
                </label>
              </fieldset>
              <fieldset>
                <legend class="mb-1 text-[11px] font-medium text-gray-400">优先级</legend>
                <label v-for="p in priorityOptions" :key="p" class="flex cursor-pointer items-center gap-1.5 py-0.5 text-xs text-gray-600">
                  <input v-model="filters.priorities" type="checkbox" :value="p" class="rounded border-gray-300 text-accent-500" />
                  <span :style="{ color: pColor(p) }" class="font-semibold">{{ p }}</span>
                </label>
              </fieldset>
              <fieldset>
                <legend class="mb-1 text-[11px] font-medium text-gray-400">状态</legend>
                <label v-for="s in lifecycleStatuses" :key="s" class="flex cursor-pointer items-center gap-1.5 py-0.5 text-xs text-gray-600">
                  <input v-model="filters.statuses" type="checkbox" :value="s" class="rounded border-gray-300 text-accent-500" />
                  <span class="truncate">{{ s }}</span>
                </label>
              </fieldset>
              <fieldset>
                <legend class="mb-1 text-[11px] font-medium text-gray-400">归属部门</legend>
                <label v-for="d in filterOptions.departments" :key="d" class="flex cursor-pointer items-center gap-1.5 py-0.5 text-xs text-gray-600">
                  <input v-model="filters.departments" type="checkbox" :value="d" class="rounded border-gray-300 text-accent-500" />
                  <span class="truncate">{{ d }}</span>
                </label>
              </fieldset>
              <fieldset class="col-span-2">
                <legend class="mb-1 text-[11px] font-medium text-gray-400">开发负责人</legend>
                <div class="grid grid-cols-2 gap-x-3">
                  <label v-for="d in filterOptions.devOwners" :key="d" class="flex cursor-pointer items-center gap-1.5 py-0.5 text-xs text-gray-600">
                    <input v-model="filters.devOwners" type="checkbox" :value="d" class="rounded border-gray-300 text-accent-500" />
                    <span class="truncate">{{ d }}</span>
                  </label>
                </div>
              </fieldset>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <select v-model="sortKey" class="feishu-input h-8 w-28 text-xs" aria-label="排序字段">
            <option value="">默认顺序</option>
            <option v-for="option in sortOptions" :key="option.key" :value="option.key">按{{ option.label }}</option>
          </select>
          <button v-if="sortKey" type="button" class="feishu-btn-ghost h-8 px-2 text-xs text-gray-600" :title="sortDir > 0 ? '当前为升序，点击切换为降序' : '当前为降序，点击切换为升序'" @click="sortDir *= -1">
            <ArrowUpDown class="w-3.5 h-3.5" /> {{ sortDir > 0 ? '升序' : '降序' }}
          </button>
        </div>
        <button v-if="canCreate" @click="openQuickImport" class="feishu-btn-ghost text-xs text-accent-600"><Upload class="w-3.5 h-3.5" /> 快速导入</button>
        <button @click="exportProjects" class="feishu-btn-ghost text-xs text-accent-600">导出项目</button>
        <button @click="exportRequirements" class="feishu-btn-ghost text-xs text-accent-600">导出需求</button>
        <button v-if="canCreate || canDelete" @click="toggleBatchMode" :class="['feishu-btn-ghost text-xs', batchMode ? 'bg-red-50 text-red-600' : 'text-gray-500']">
          <Trash2 class="w-3.5 h-3.5" /> {{ batchMode ? '退出批量管理' : '批量管理' }}
        </button>
        <button v-if="batchMode && selectedRequirementIds.size && canCreate" @click="openBatchBackfill" class="feishu-btn-ghost text-xs text-accent-600">
          <Edit3 class="w-3.5 h-3.5" /> 补录 L3 字段 {{ selectedRequirementIds.size }} 条
        </button>
        <button v-if="batchMode && selectedRequirementIds.size" @click="bulkDeleteRequirements" class="feishu-btn-ghost text-xs text-red-500">
          <Trash2 class="w-3.5 h-3.5" /> 删除需求 {{ selectedRequirementIds.size }}
        </button>
        <button v-if="batchMode && selectedProjectIds.size" @click="bulkDeleteProjects" class="feishu-btn-ghost text-xs text-red-500">
          <Trash2 class="w-3.5 h-3.5" /> 删除项目 {{ selectedProjectIds.size }}
        </button>
        <button v-if="canManageCategories" @click="showCreateCategory = true" class="feishu-btn-primary text-xs"><Plus class="w-3.5 h-3.5" /> 新建大类</button>
      </div>
    </div>

    <div v-if="loadError" class="mb-3 flex items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
      <span>{{ loadError }}</span>
      <button class="shrink-0 font-semibold text-accent-600 hover:text-accent-700" @click="loadData">重新加载</button>
    </div>

    <!-- Sheet tabs -->
    <div class="flex items-center gap-0.5 mb-4 border-b border-gray-200 overflow-x-auto">
      <div v-for="tab in tabItems" :key="tab.id"
        :class="['feishu-tab group/tab', activeTab === tab.id ? 'feishu-tab-active' : 'feishu-tab-inactive']"
        @click="activeTab = tab.id">
        <span v-if="tab.color" class="w-1.5 h-1.5 rounded-full inline-block mr-1.5" :style="{ backgroundColor: tab.color }" />
        {{ tab.label }}
        <span class="text-[10px] text-gray-400 ml-1">{{ tab.count }}</span>
        <button v-if="canManageCategories && tab.id !== 'all'" @click.stop="deleteCategoryById(tab.id)" class="ml-2 text-gray-300 opacity-0 transition-opacity group-hover/tab:opacity-100 hover:text-red-400" title="删除大类">
          <Trash2 class="w-3 h-3" />
        </button>
      </div>
    </div>

    <!-- L2 project table -->
    <div ref="tableShell" :class="['requirements-table-shell min-h-0 flex-1 bg-white rounded-lg border border-gray-200 overflow-x-scroll overflow-y-auto', `requirements-table-shell--${tableLayoutMode}`]">
      <table :class="['feishu-table compact-l2-table table-fixed', { 'compact-l2-table-batch': batchMode }]">
        <colgroup>
          <col v-if="batchMode" class="l2-col-select" />
          <col class="l2-col-name" />
          <col class="l2-col-category" />
          <col class="l2-col-priority" />
          <col class="l2-col-status" />
          <col class="l2-col-department" />
          <col class="l2-col-business" />
          <col class="l2-col-dev-owner" />
          <col class="l2-col-version" />
          <col class="l2-col-created" />
          <col class="l2-col-progress" />
          <col class="l2-col-description" />
          <col class="l2-col-actions" />
        </colgroup>
        <thead>
          <tr>
            <th v-if="batchMode" class="l2-col-select text-center">
              <input type="checkbox" class="rounded border-gray-300 text-accent-500"
                :checked="displayProjects.length > 0 && displayProjects.every(p => selectedProjectIds.has(p.id))"
                @change="toggleAllProjects" />
            </th>
            <th class="sortable l2-col-name" @click="toggleSort('name')">名称 {{ sortIcon('name') }}</th>
            <th class="sortable l2-col-category" @click="toggleSort('categoryName')">所属大类 {{ sortIcon('categoryName') }}</th>
            <th class="sortable l2-col-priority" @click="toggleSort('priority')">优先级 {{ sortIcon('priority') }}</th>
            <th class="sortable l2-col-status" @click="toggleSort('status')">状态 {{ sortIcon('status') }}</th>
            <th class="sortable l2-col-department" @click="toggleSort('department')">部门 {{ sortIcon('department') }}</th>
            <th class="sortable l2-col-business" @click="toggleSort('businessOwner')">业务对接 {{ sortIcon('businessOwner') }}</th>
            <th class="sortable l2-col-dev-owner" @click="toggleSort('devOwner')">开发负责人 {{ sortIcon('devOwner') }}</th>
            <th class="sortable l2-col-version" @click="toggleSort('currentVersion')">版本 {{ sortIcon('currentVersion') }}</th>
            <th class="sortable l2-col-created" @click="toggleSort('createdAt')">创建时间 {{ sortIcon('createdAt') }}</th>
            <th class="sortable l2-col-progress" @click="toggleSort('progress')">进度 {{ sortIcon('progress') }}</th>
            <th class="l2-col-description">需求描述</th>
            <th class="l2-col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(p, idx) in displayProjects" :key="p.id">
          <tr class="feishu-row group/l2">
            <td v-if="batchMode" class="text-center">
              <input type="checkbox" class="mr-1 rounded border-gray-300 text-accent-500"
                :checked="selectedProjectIds.has(p.id)"
                @click.stop
                @change="toggleProjectSelection(p.id)" />
            </td>
            <td class="l2-col-name font-medium text-gray-900 cursor-pointer hover:text-accent-500"
              @dblclick="goProject(p.id)" :title="'双击进入项目详情'">
              <div class="l2-name-content">
              <ChevronRight class="l2-expander w-3.5 h-3.5 shrink-0 text-accent-500 transition-transform cursor-pointer"
                :class="expandedL2s.has(p.id) ? 'rotate-90' : ''"
                @click="toggleL2(p.id)" />
              <span class="min-w-0 flex-1 truncate whitespace-nowrap">{{ p.name }}</span>
              </div>
              <span v-if="p.solutionTypeLabel" class="ml-5 mt-0.5 block max-w-[150px] truncate text-[10px] text-slate-400">{{ p.solutionTypeLabel }}</span>
            </td>
            <td class="l2-col-category">
              <span class="inline-flex max-w-full items-center gap-1 truncate rounded-md border px-2 py-0.5 text-xs font-semibold" :style="{ color: p.categoryColor || getCatColor(p.categoryId), borderColor: (p.categoryColor || getCatColor(p.categoryId)) + '55', backgroundColor: (p.categoryColor || getCatColor(p.categoryId)) + '12' }" :title="categoryName(p)">
                <span class="truncate">{{ categoryName(p) }}</span>
              </span>
            </td>
            <td class="l2-col-priority">
              <select v-model="p.priority" :disabled="!canEditProject(p)" @change="updateProjectField(p, 'priority')" class="feishu-cell-select"
                :style="{ color: pColor(p.priority) }">
                <option v-for="pr in ['P0','P1','P2','P3']" :key="pr" :value="pr" :style="{ color: pColor(pr) }">{{ pr }}</option>
              </select>
            </td>
            <td class="l2-col-status">
              <select v-model="p.status" :disabled="!canEditProject(p)" @change="updateProjectField(p, 'status')" class="feishu-cell-select"
                :style="{ color: sColor(p.status) }">
                <option v-for="s in lifecycleStatuses" :key="s" :value="s" :style="{ color: sColor(s) }">{{ statusLabel[s] || s }}</option>
              </select>
            </td>
            <td class="l2-col-department text-xs text-gray-500">{{ p.department }}</td>
            <td class="l2-col-business"><span class="inline-flex max-w-full items-center truncate rounded-md border px-2 py-0.5 text-xs font-semibold" :style="personBadgeStyle(p.businessOwner)">{{ p.businessOwner || '-' }}</span></td>
            <td class="l2-col-dev-owner"><span class="inline-flex max-w-full items-center truncate rounded-md border px-2 py-0.5 text-xs font-semibold" :style="personBadgeStyle(p.devOwner)">{{ p.devOwner || '-' }}</span></td>
            <td class="l2-col-version"><span class="inline-flex items-center rounded-md border px-2 py-0.5 font-mono text-xs font-bold" :style="versionBadgeStyle(p.currentVersion)">{{ p.currentVersion || '-' }}</span></td>
            <td class="l2-col-created text-xs text-gray-500">{{ shortDateTime(p.createdAt) }}</td>
            <td class="l2-col-progress">
              <div class="l2-progress" :class="progressBoxClass(p)" :title="progressTooltip(p)">
                <div class="flex items-center justify-between gap-2 mb-1">
                  <span class="text-[11px] font-semibold truncate">{{ progressLabel(p) }}</span>
                  <span class="text-[12px] font-bold tabular-nums">{{ progressPercent(p) }}%</span>
                </div>
                <div class="progress-bar h-2.5 bg-white/70 ring-1 ring-black/5">
                  <div class="progress-fill" :style="{ width: progressPercent(p) + '%', backgroundColor: progressColor(p) }" />
                </div>
                <div class="mt-1 flex items-center justify-between gap-2 text-[10px]">
                  <span class="truncate opacity-80">{{ progressSubLabel(p) }}</span>
                  <span class="font-medium opacity-75">{{ progressCountText(p) }}</span>
                </div>
              </div>
            </td>
            <td class="l2-col-description">
              <div class="flex items-center gap-2">
                <span class="max-w-[150px] truncate text-xs text-gray-500" :title="p.description || ''">{{ p.description || '-' }}</span>
                <div v-if="p.images?.length" class="flex gap-0.5 shrink-0">
                  <img v-for="(img, i) in p.images.slice(0, 2)" :key="i" :src="img.data || img"
                    class="w-6 h-6 rounded object-cover border border-gray-100 cursor-pointer"
                    @click="previewImages(p.images, i)" />
                  <span v-if="p.images.length > 2" class="text-xs text-gray-400 ml-0.5">+{{ p.images.length - 2 }}</span>
                </div>
              </div>
            </td>
            <td class="l2-col-actions">
              <div class="flex items-center gap-1">
                <button v-if="canEditProject(p)" @click.stop="editProject(p)" class="feishu-icon-btn"><Edit3 class="w-3 h-3" /></button>
                <button v-if="canDeleteProject(p)" @click.stop="deleteProject(p)" class="feishu-icon-btn text-gray-300 opacity-0 transition-opacity group-hover/l2:opacity-100 hover:text-red-400" title="移入回收站"><Trash2 class="w-3 h-3" /></button>
              </div>
            </td>
          </tr>

          <!-- L3 sub-table rows -->
          <tr v-if="expandedL2s.has(p.id)" :key="'l3-' + p.id" class="bg-slate-50/70">
             <td :colspan="batchMode ? 13 : 12">
              <div class="mx-5 my-3 rounded-lg border border-accent-100 border-l-4 border-l-accent-400 bg-white shadow-sm">
                <div class="flex items-center justify-between border-b border-slate-100 bg-accent-50/40 px-4 py-2">
                  <span class="text-xs font-semibold text-slate-700">{{ p.name }} · {{ getL3Reqs(p.id).length }} 个需求</span>
                  <button v-if="canCreate" @click="createRequirement(p.id)" class="feishu-icon-btn text-accent-600"><Plus class="w-3.5 h-3.5" /> 新建需求</button>
                </div>
              <div class="px-4 py-3">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] text-slate-400">L3 需求明细</span>
                </div>
                <table class="feishu-l3-table compact-l3-table table-fixed" v-if="getL3Reqs(p.id).length">
                  <thead>
                    <tr>
                      <th class="w-[19%] sortable" @click="toggleSort('title')">标题 {{ sortIcon('title') }}</th>
                      <th class="w-[7%]">工作类型</th>
                      <th class="w-[7%]">变更对象</th>
                      <th class="w-[9%]">产品价值</th>
                      <th class="w-[5%] sortable" @click="toggleSort('priority')">优先级 {{ sortIcon('priority') }}</th>
                      <th class="w-[6%] sortable" @click="toggleSort('status')">状态 {{ sortIcon('status') }}</th>
                      <th class="w-[8%]">归属部门</th>
                      <th class="w-[7%]">提出方</th>
                      <th class="w-[7%]">负责人</th>
                      <th class="w-[7%]">预计交付</th>
                      <th class="w-[7%]">完成时间</th>
                      <th class="w-[7%]">创建时间</th>
                      <th class="w-[9%]">需求描述</th>
                      <th class="w-[5%]">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="r in getL3Reqs(p.id)" :key="r.id" class="feishu-l3-row-item group/l3 bg-white hover:bg-accent-50/40"
                      @dblclick="goRequirement(r.id)" :title="'双击查看需求详情'">
                      <td class="font-medium text-gray-900 text-xs">
                        <div class="flex flex-col gap-1">
                          <label class="flex items-start gap-2">
                            <input v-if="batchMode" type="checkbox" class="mt-0.5 rounded border-gray-300 text-accent-500"
                              :checked="selectedRequirementIds.has(r.id)"
                              @click.stop
                              @change="toggleRequirementSelection(r.id)" />
                            <span>{{ r.title }}</span>
                          </label>
                          <span v-if="isCrossOwnerRequirement(r)" class="w-fit rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600">
                            {{ hasPerson(r.assignee, currentDeveloper) ? '待你处理' : '协作新增' }} · {{ r.requester || '他人' }} 提出
                          </span>
                        </div>
                      </td>
                      <td><span class="feishu-badge" :style="{ backgroundColor: tColor(r.type) + '20', color: tColor(r.type) }">{{ r.type || '未分类' }}</span></td>
                      <td><span class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">{{ r.changeObject || '功能' }}</span></td>
                      <td>
                        <div class="flex flex-wrap items-center gap-1">
                          <span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :style="{ backgroundColor: impactColor(r.impactLevel) + '18', color: impactColor(r.impactLevel) }">{{ r.impactLevel || '常规' }}</span>
                          <span class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">{{ r.workloadLevel || '中' }}工作量</span>
                        </div>
                      </td>
                      <td><span class="text-xs font-bold" :style="{ color: pColor(r.priority) }">{{ r.priority }}</span></td>
                      <td><span class="text-xs px-1.5 py-0.5 rounded" :style="{ backgroundColor: rColor(r.status) + '20', color: rColor(r.status) }">{{ r.status }}</span></td>
                      <td class="text-xs text-gray-500">{{ r.department || r.projectDepartment || '-' }}</td>
                      <td><span class="inline-flex max-w-[96px] items-center truncate rounded-md border px-1.5 py-0.5 text-xs font-semibold" :style="personBadgeStyle(r.requester)">{{ r.requester || '-' }}</span></td>
                      <td><span class="inline-flex max-w-[96px] items-center truncate rounded-md border px-1.5 py-0.5 text-xs font-semibold" :style="personBadgeStyle(r.assignee)">{{ r.assignee || '-' }}</span></td>
                      <td class="text-xs text-gray-500">{{ r.expectedDeliveryTime || '-' }}</td>
                      <td class="text-xs text-gray-500">{{ shortDateTime(r.completedAt) }}</td>
                      <td class="text-xs text-gray-500">{{ shortDateTime(r.createdAt) }}</td>
                      <td>
                        <div class="flex items-center gap-2">
                          <span class="max-w-[150px] truncate text-xs text-gray-500" :title="r.description || ''">{{ r.description || '-' }}</span>
                          <button v-if="r.imageCount" class="inline-flex shrink-0 items-center gap-0.5 rounded border border-slate-200 px-1 py-0.5 text-[10px] text-slate-500 hover:border-accent-300 hover:text-accent-600"
                            :title="`查看 ${r.imageCount} 个附件`" @click.stop="previewRequirementImages(r)">
                            <Paperclip class="h-3 w-3" /> {{ r.imageCount }}
                          </button>
                        </div>
                      </td>
                      <td>
                        <div class="flex items-center gap-1" @click.stop>
                          <button v-if="canEditRequirement(r, p)" @click="editRequirement(r)" class="feishu-icon-btn"><Edit3 class="w-3 h-3" /></button>
                          <button v-if="canDeleteRequirement(r, p)" @click="deleteRequirement(r)" class="feishu-icon-btn text-gray-300 opacity-0 transition-opacity group-hover/l3:opacity-100 hover:text-red-400" title="移入回收站"><Trash2 class="w-3 h-3" /></button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <p v-else class="text-xs text-gray-400 text-center py-4">暂无需求，点击上方「新建需求」添加</p>
              </div>
              </div>
            </td>
          </tr>
          </template>
        </tbody>
      </table>

      <!-- Empty state -->
      <div v-if="isLoading" class="text-center text-gray-400 py-12 text-sm">正在加载项目数据…</div>
      <div v-else-if="displayProjects.length === 0 && !loadError" class="text-center text-gray-400 py-12 text-sm">
        <p>暂无项目数据</p>
        <button v-if="canCreateProject" @click="createProject" class="text-accent-500 hover:text-accent-600 mt-2 inline-flex items-center gap-1">
          <Plus class="w-4 h-4" /> 新建项目
        </button>
      </div>
    </div>

    <!-- Bottom: + 新建项目 -->
    <div class="mt-3">
      <button v-if="canCreateProject" @click="createProject" class="feishu-btn-ghost text-xs text-gray-500 hover:text-accent-500">
        <Plus class="w-3.5 h-3.5" /> 新建项目
      </button>
    </div>

    <!-- Modals (same as before) -->
    <ImagePreviewModal v-model="previewModal.open" :images="previewModal.images" :start-index="previewModal.index" />

    <!-- Category modal -->
    <div v-if="showCreateCategory || editingCategory" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center" @click.self="closeCategoryModal">
      <div class="bg-white rounded-xl shadow-xl w-[480px] p-6 animate-scale-in">
        <h3 class="font-semibold text-gray-900 mb-4">{{ editingCategory ? '编辑大类' : '新建大类' }}</h3>
        <div class="space-y-3">
          <div><label class="text-xs text-gray-500">名称 *</label><input v-model="catForm.name" class="feishu-input w-full mt-1" /></div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="text-xs text-gray-500">图标</label><input v-model="catForm.icon" class="feishu-input w-full mt-1" /></div>
            <div><label class="text-xs text-gray-500">颜色</label><input v-model="catForm.color" type="color" class="w-full h-9 rounded border border-gray-200 mt-1" /></div>
          </div>
          <div><label class="text-xs text-gray-500">描述</label><textarea v-model="catForm.description" class="feishu-input w-full mt-1" rows="2"></textarea></div>
          <div>
            <label class="text-xs text-gray-500">负责人</label>
            <div class="mt-1 grid grid-cols-3 gap-2">
              <label v-for="d in devOpts" :key="d" class="flex items-center gap-1.5 rounded-md border border-gray-200 px-2.5 py-1.5 text-xs text-gray-700 cursor-pointer hover:border-accent-300 hover:bg-accent-50/40">
                <input v-model="catForm.owner" :value="d" type="checkbox" class="rounded border-gray-300 text-accent-500 focus:ring-accent-400" />
                <span class="truncate">{{ d.split('-')[0] }}</span>
              </label>
            </div>
          </div>
          <div><label class="text-xs text-gray-500">排序</label><input v-model.number="catForm.sortOrder" type="number" class="feishu-input w-24 mt-1" /></div>
        </div>
        <div class="flex justify-end gap-3 mt-5">
          <button @click="closeCategoryModal" class="feishu-btn-ghost text-sm">取消</button>
          <button @click="saveCategory" class="feishu-btn-primary text-sm">{{ editingCategory ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>

    <!-- Project modal -->
    <div v-if="showCreateProject || editingProject" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center" @click.self="closeProjectModal">
      <div class="bg-white rounded-xl shadow-xl w-[560px] p-6 animate-scale-in max-h-[90vh] overflow-y-auto" @paste="handleImagePaste($event, projForm)">
        <h3 class="font-semibold text-gray-900 mb-4">{{ editingProject ? '编辑项目' : '新建项目' }}</h3>
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2"><label class="text-xs text-gray-500">名称 *</label><input v-model="projForm.name" class="feishu-input w-full mt-1" /></div>
          <div><label class="text-xs text-gray-500">优先级</label><select v-model="projForm.priority" class="feishu-input w-full mt-1"><option v-for="p in ['P0','P1','P2','P3']" :key="p" :value="p">{{ p }}</option></select></div>
          <div><label class="text-xs text-gray-500">状态</label><select v-model="projForm.status" class="feishu-input w-full mt-1"><option v-for="s in lifecycleStatuses" :key="s" :value="s">{{ statusLabel[s] || s }}</option></select></div>
          <div class="col-span-2"><label class="text-xs text-gray-500">解决方案类型 *</label><select v-model="projForm.solutionType" class="feishu-input w-full mt-1" @change="onProjectSolutionTypeChange"><option value="unknown">待分类</option><option v-for="item in solutionTypeOptions" :key="item.key" :value="item.key">{{ item.label }} · {{ item.description }}</option></select><p class="mt-1 text-[11px] text-gray-400">它决定验收关注点和推荐的初始建设阶段，与所属大类分开填写。</p></div>
          <div><label class="text-xs text-gray-500">所属大类</label><select v-model="projForm.categoryId" class="feishu-input w-full mt-1"><option value="">请选择</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option></select></div>
          <div class="relative">
            <label class="text-xs text-gray-500">部门 *</label>
            <button type="button" class="feishu-input w-full mt-1 flex items-center justify-between text-left"
              @click="deptDropdownOpen = !deptDropdownOpen">
              <span :class="projForm.department ? 'text-gray-900' : 'text-gray-400'">{{ projForm.department || '请选择' }}</span>
              <ChevronRight class="w-3.5 h-3.5 text-accent-500 rotate-90" />
            </button>
            <div v-if="deptDropdownOpen" class="absolute z-[70] mt-1 w-full max-h-72 overflow-auto rounded-lg border border-gray-200 bg-white py-1 shadow-xl">
              <button type="button" class="w-full px-4 py-2 text-left text-sm font-medium text-gray-900 hover:bg-gray-50"
                @click="selectDepartment('')">请选择</button>
              <button v-for="node in visibleDeptOptions" :key="node.id" type="button"
                class="w-full flex items-center gap-1 px-4 py-2 text-left text-sm font-medium text-gray-900 hover:bg-accent-50"
                :class="projForm.department === node.name ? 'bg-accent-500 text-white hover:bg-accent-500' : ''"
                :style="{ paddingLeft: `${16 + node.level * 18}px` }"
                @click="handleDepartmentClick(node)">
                <span class="w-4 h-4 inline-flex items-center justify-center"
                  @click.stop="toggleDeptNode(node.id)">
                  <ChevronRight v-if="node.hasChildren" class="w-3.5 h-3.5 text-accent-500 transition-transform"
                    :class="expandedDeptIds.has(node.id) ? 'rotate-90' : ''" />
                </span>
                <span class="truncate">{{ node.name }}</span>
              </button>
              <p v-if="contactsLoading" class="px-4 py-3 text-sm text-gray-400">组织架构加载中...</p>
              <p v-else-if="visibleDeptOptions.length === 0" class="px-4 py-3 text-sm text-gray-400">暂无组织架构部门</p>
            </div>
          </div>
          <div><label class="text-xs text-gray-500">业务对接负责人</label><SearchableMultiSelect v-model="projForm.businessOwner" :options="bizOwnerOpts" :disabled="!!editingProject && !isManager" /></div>
          <div><label class="text-xs text-gray-500">开发负责人 *</label><SearchableMultiSelect v-model="projForm.devOwner" :options="devOpts" :disabled="!!editingProject && !isManager" placeholder="搜索或选择开发负责人" /></div>
          <div><label class="text-xs text-gray-500">当前版本</label><input v-model="projForm.currentVersion" class="feishu-input w-full mt-1" /></div>
          <div><label class="text-xs text-gray-500">开始时间</label><input v-model="projForm.startDate" type="date" class="feishu-input w-full mt-1" /></div>
          <div><label class="text-xs text-gray-500">目标结束时间 *</label><input v-model="projForm.targetEndDate" type="date" class="feishu-input w-full mt-1" /></div>
          <div v-if="!editingProject && projForm.solutionType !== 'unknown'" class="col-span-2 rounded-lg border border-accent-100 bg-accent-50/40 p-3">
            <div class="flex items-center justify-between gap-2"><div><p class="text-xs font-semibold text-slate-700">前置建设工作包（可选）</p><p class="mt-1 text-[11px] leading-5 text-slate-500">按项目类型推荐初始 L3 阶段；可取消勾选或全部跳过，后续仍可手动补充。</p></div><label class="flex items-center gap-1.5 text-[11px] text-accent-700"><input v-model="projForm.createInitialL3" type="checkbox" class="rounded border-gray-300 text-accent-500" />创建“初始建设” L3</label></div>
            <div v-if="projForm.createInitialL3" class="mt-3 grid gap-2 sm:grid-cols-2">
              <label v-for="phase in phaseTemplatesForForm" :key="phase.phaseKey" class="flex items-start gap-2 rounded-md border border-white bg-white px-2.5 py-2 text-[11px] text-slate-700"><input v-model="projForm.phaseTemplateKeys" :value="phase.phaseKey" type="checkbox" class="mt-0.5 rounded border-gray-300 text-accent-500" /><span><span class="font-medium">{{ phase.phaseLabel }}</span><span class="mt-0.5 block text-[10px] leading-4 text-slate-400">{{ phase.description }}</span></span></label>
            </div>
          </div>
          <div class="col-span-2"><label class="text-xs text-gray-500">描述</label><textarea v-model="projForm.description" class="feishu-input w-full mt-1" rows="2"></textarea></div>
          <div class="col-span-2">
            <label class="text-xs text-gray-500">交付进度反馈截图</label>
            <input type="file" accept="image/*" multiple class="feishu-input w-full mt-1" @change="handleImageUpload($event, projForm)" />
            <p class="mt-1 text-[11px] text-gray-400">也可直接按 Ctrl + V 粘贴剪贴板中的图片</p>
            <div v-if="projForm.images?.length" class="mt-2 flex flex-wrap gap-2">
              <div v-for="(img, i) in projForm.images" :key="i" class="relative group">
                <img :src="imageSrc(img)" class="w-20 h-20 rounded-md object-cover border border-gray-200 cursor-pointer" @click="previewImages(projForm.images, i)" />
                <button type="button" class="absolute -right-1.5 -top-1.5 hidden group-hover:flex w-5 h-5 items-center justify-center rounded-full bg-red-500 text-white text-xs"
                  @click.stop="removeImage(projForm, i)">×</button>
              </div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-5">
          <button @click="closeProjectModal" class="feishu-btn-ghost text-sm">取消</button>
          <button @click="saveProject" class="feishu-btn-primary text-sm">{{ editingProject ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>

    <!-- Requirement modal -->
    <div v-if="showCreateReq || editingReq" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center" @click.self="closeReqModal">
      <div class="bg-white rounded-xl shadow-xl w-[560px] p-6 animate-scale-in max-h-[90vh] overflow-y-auto" @paste="handleImagePaste($event, reqForm)">
        <h3 class="font-semibold text-gray-900 mb-4">{{ editingReq ? '编辑需求' : '新建需求' }}</h3>
        <div class="space-y-3">
          <div><label class="text-xs text-gray-500">标题 *</label><input v-model="reqForm.title" class="feishu-input w-full mt-1" /></div>
          <div class="grid grid-cols-3 gap-3">
            <div><label class="text-xs text-gray-500">工作类型</label><select v-model="reqForm.type" class="feishu-input w-full mt-1"><option v-for="t in typeOpts" :key="t" :value="t">{{ t }}</option></select></div>
            <div><label class="text-xs text-gray-500">L3 工作单元</label><select v-model="reqForm.itemKind" class="feishu-input w-full mt-1"><option v-for="item in itemKindOptions" :key="item.key" :value="item.key">{{ item.label }}</option></select></div>
            <div><label class="text-xs text-gray-500">优先级</label><select v-model="reqForm.priority" class="feishu-input w-full mt-1"><option v-for="p in priorityOptions" :key="p" :value="p">{{ p }}</option></select></div>
            <div><label class="text-xs text-gray-500">状态</label><select v-model="reqForm.status" class="feishu-input w-full mt-1"><option v-for="s in requirementStatuses" :key="s" :value="s">{{ s }}</option></select></div>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div><label class="text-xs text-gray-500">变更对象</label><select v-model="reqForm.changeObject" class="feishu-input w-full mt-1"><option v-for="item in changeObjectOptions" :key="item" :value="item">{{ item }}</option></select></div>
            <div><label class="text-xs text-gray-500">产品影响</label><select v-model="reqForm.impactLevel" class="feishu-input w-full mt-1"><option v-for="item in impactOptions" :key="item" :value="item">{{ item }}</option></select></div>
            <div><label class="text-xs text-gray-500">工作量</label><select v-model="reqForm.workloadLevel" class="feishu-input w-full mt-1"><option v-for="item in workloadOptions" :key="item" :value="item">{{ item }}</option></select></div>
          </div>
          <PriorityAssessment v-model="reqForm.priorityEvaluation" :priority="reqForm.priority || 'P2'" :project-priority="reqAssessmentProjectPriority" @adopt="reqForm.priority = $event" />
          <div class="grid grid-cols-2 gap-3">
            <div><label class="text-xs text-gray-500">所属项目</label><select v-model="reqForm.projectId" class="feishu-input w-full mt-1" @change="syncReqProjectDefaults"><option v-for="p in allProjects" :key="p.id" :value="p.id">{{ p.name }}</option></select></div>
            <div><label class="text-xs text-gray-500">开发负责人 *</label><SearchableMultiSelect v-model="reqForm.assignee" :options="devOpts" :disabled="!!editingReq && !isManager" placeholder="搜索或选择开发负责人" /></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="text-xs text-gray-500">归属部门 *</label><select v-model="reqForm.department" class="feishu-input w-full mt-1"><option value="">请选择</option><option v-for="d in deptFlatOptions" :key="d" :value="d">{{ d }}</option></select></div>
            <div><label class="text-xs text-gray-500">提出方</label><SearchableMultiSelect v-model="reqForm.requester" :options="bizOwnerOpts" :disabled="!!editingReq && !isManager" /></div>
          </div>
          <div><label class="text-xs text-gray-500">预计交付时间 *</label><input v-model="reqForm.expectedDeliveryTime" type="date" class="feishu-input w-full mt-1" /></div>
          <div><label class="text-xs text-gray-500">描述</label><textarea v-model="reqForm.description" class="feishu-input w-full mt-1" rows="2"></textarea></div>
          <div><label class="text-xs text-gray-500">验收标准</label><textarea v-model="reqForm.acceptanceCriteria" class="feishu-input w-full mt-1" rows="2"></textarea></div>
          <div>
            <label class="text-xs text-gray-500">交付进度反馈截图</label>
            <input type="file" accept="image/*" multiple class="feishu-input w-full mt-1" @change="handleImageUpload($event, reqForm)" />
            <p class="mt-1 text-[11px] text-gray-400">也可直接按 Ctrl + V 粘贴剪贴板中的图片</p>
            <div v-if="reqForm.images?.length" class="mt-2 flex flex-wrap gap-2">
              <div v-for="(img, i) in reqForm.images" :key="i" class="relative group">
                <img :src="imageSrc(img)" class="w-20 h-20 rounded-md object-cover border border-gray-200 cursor-pointer" @click="previewImages(reqForm.images, i)" />
                <button type="button" class="absolute -right-1.5 -top-1.5 hidden group-hover:flex w-5 h-5 items-center justify-center rounded-full bg-red-500 text-white text-xs"
                  @click.stop="removeImage(reqForm, i)">×</button>
              </div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-5">
          <button @click="closeReqModal" class="feishu-btn-ghost text-sm">取消</button>
          <button @click="saveRequirement" class="feishu-btn-primary text-sm">{{ editingReq ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>

    <!-- Batch L3 classification backfill modal -->
    <div v-if="showBatchBackfill" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center" @click.self="closeBatchBackfill">
      <div class="bg-white rounded-xl shadow-xl w-[560px] p-6 animate-scale-in">
        <h3 class="font-semibold text-gray-900">批量补录 / 校正 L3 字段</h3>
        <p class="mt-1 text-xs leading-5 text-gray-400">已选择 {{ selectedRequirementIds.size }} 条需求。留空表示保留原值；保存后每条记录都会写入操作记录。</p>
        <div class="mt-4 grid grid-cols-2 gap-3">
          <div><label class="text-xs text-gray-500">工作类型</label><select v-model="batchForm.type" class="feishu-input w-full mt-1"><option value="">保留原值</option><option v-for="item in typeOpts" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">状态</label><select v-model="batchForm.status" class="feishu-input w-full mt-1"><option value="">保留原值</option><option v-for="item in requirementStatuses" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">变更对象</label><select v-model="batchForm.changeObject" class="feishu-input w-full mt-1"><option value="">保留原值</option><option v-for="item in changeObjectOptions" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">产品影响</label><select v-model="batchForm.impactLevel" class="feishu-input w-full mt-1"><option value="">保留原值</option><option v-for="item in impactOptions" :key="item" :value="item">{{ item }}</option></select></div>
          <div><label class="text-xs text-gray-500">工作量</label><select v-model="batchForm.workloadLevel" class="feishu-input w-full mt-1"><option value="">保留原值</option><option v-for="item in workloadOptions" :key="item" :value="item">{{ item }}</option></select></div>
          <div class="col-span-2"><label class="text-xs text-gray-500">补录说明</label><textarea v-model="batchForm.reason" rows="2" class="feishu-input w-full mt-1" placeholder="写入操作记录的说明"></textarea></div>
        </div>
        <div class="mt-5 flex justify-end gap-3">
          <button @click="closeBatchBackfill" class="feishu-btn-ghost text-sm">取消</button>
          <button @click="saveBatchBackfill" class="feishu-btn-primary text-sm">保存补录</button>
        </div>
      </div>
    </div>

    <!-- Quick import modal -->
    <div v-if="showQuickImport" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center" @click.self="showQuickImport = false">
      <div class="bg-white rounded-xl shadow-xl w-[760px] p-6 animate-scale-in max-h-[90vh] overflow-y-auto">
        <div class="flex items-start justify-between mb-4">
          <div>
            <h3 class="font-semibold text-gray-900">快速导入项目/需求</h3>
            <p class="text-xs text-gray-400 mt-1">粘贴日报、日志或上传 txt 文本，系统会按字段识别并生成可编辑草稿。</p>
          </div>
          <button @click="showQuickImport = false" class="feishu-btn-ghost text-sm">关闭</button>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div class="col-span-2 space-y-3">
            <div class="flex rounded-lg bg-gray-100 p-0.5 w-fit">
              <button @click="quickForm.level = 'project'" :class="quickModeClass('project')">导入 L2 项目</button>
              <button @click="quickForm.level = 'requirement'" :class="quickModeClass('requirement')">导入 L3 需求</button>
            </div>
            <div class="rounded-lg border border-accent-100 bg-accent-50/40 p-3">
              <p class="text-xs font-semibold text-gray-700">快速归属</p>
              <p class="mt-1 text-[11px] text-gray-400">可先指定目标；文本中写明“大类：… / 项目：… / 需求：…”时，会优先按文本层级识别，不存在的 L1/L2 会自动创建。</p>
              <select v-if="quickForm.level === 'project'" v-model="quickTarget.categoryId" class="feishu-input mt-2 w-full">
                <option value="">选择归属大类（可留空）</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
              <select v-else v-model="quickTarget.projectId" class="feishu-input mt-2 w-full">
                <option value="">选择归属项目（或从文本自动识别）</option>
                <option v-for="p in allProjects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <textarea v-model="quickForm.text" rows="8" class="feishu-input w-full" placeholder="示例：项目名称：AI电商日报&#10;部门：信息技术部&#10;业务负责人：豪杰-戴豪杰&#10;描述：每日自动汇总电商数据..."></textarea>
            <input type="file" accept=".txt,.md,text/plain" class="feishu-input w-full" @change="readQuickImportFile" />
            <button @click="parseQuickImport" class="feishu-btn-primary text-sm">识别文本</button>
          </div>
          <div class="rounded-lg border border-gray-100 bg-gray-50 p-3">
            <h4 class="text-xs font-semibold text-gray-700 mb-2">默认值设置</h4>
            <div class="space-y-2">
              <div><label class="text-[11px] text-gray-400">优先级</label><select v-model="quickDefaults.priority" class="feishu-input w-full mt-1"><option v-for="p in (quickForm.level === 'requirement' ? priorityOptions : ['P0','P1','P2','P3'])" :key="p" :value="p">{{ p }}</option></select></div>
              <div><label class="text-[11px] text-gray-400">状态</label><select v-model="quickDefaults.status" class="feishu-input w-full mt-1"><option v-for="s in (quickForm.level === 'requirement' ? requirementStatuses : lifecycleStatuses)" :key="s" :value="s">{{ s }}</option></select></div>
              <div><label class="text-[11px] text-gray-400">开发负责人</label><SearchableMultiSelect v-model="quickDefaults.devOwner" :options="devOpts" placeholder="自动识别本人" /></div>
              <div><label class="text-[11px] text-gray-400">预计交付/目标结束</label><input v-model="quickDefaults.date" type="date" class="feishu-input w-full mt-1" /></div>
              <button @click="saveQuickDefaults" class="w-full rounded-md bg-white px-2 py-1.5 text-xs text-accent-600 border border-accent-100 hover:bg-accent-50">保存默认值</button>
            </div>
          </div>
        </div>
        <div v-if="quickDraft" class="mt-4 rounded-lg border border-gray-100 p-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="text-sm font-semibold text-gray-900">识别结果</h4>
            <span v-if="quickMissing.length" class="text-xs text-red-500">缺少：{{ quickMissing.join('、') }}</span>
            <span v-else class="text-xs text-emerald-600">必填字段已完整</span>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="text-xs text-gray-500">名称/标题 *</label><input v-model="quickDraft.name" class="feishu-input w-full mt-1" /></div>
            <div v-if="quickForm.level === 'requirement'"><label class="text-xs text-gray-500">所属项目 *</label><select v-model="quickDraft.projectId" class="feishu-input w-full mt-1" @change="fillQuickProjectDefaults"><option value="">请选择</option><option v-for="p in allProjects" :key="p.id" :value="p.id">{{ p.name }}</option></select></div>
            <div v-else><label class="text-xs text-gray-500">所属大类</label><select v-model="quickDraft.categoryId" class="feishu-input w-full mt-1"><option value="">请选择</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option></select></div>
            <div><label class="text-xs text-gray-500">部门 *</label><select v-model="quickDraft.department" class="feishu-input w-full mt-1"><option value="">请选择</option><option v-for="d in deptFlatOptions" :key="d" :value="d">{{ d }}</option></select></div>
            <div><label class="text-xs text-gray-500">业务负责人/提出方</label><SearchableMultiSelect v-model="quickDraft.businessOwner" :options="bizOwnerOpts" /></div>
            <div><label class="text-xs text-gray-500">开发负责人 *</label><SearchableMultiSelect v-model="quickDraft.devOwner" :options="devOpts" placeholder="搜索或选择开发负责人" /></div>
            <div><label class="text-xs text-gray-500">{{ quickForm.level === 'project' ? '目标结束时间' : '预计交付时间' }} *</label><input v-model="quickDraft.date" type="date" class="feishu-input w-full mt-1" /></div>
            <div class="col-span-2"><label class="text-xs text-gray-500">描述</label><textarea v-model="quickDraft.description" rows="3" class="feishu-input w-full mt-1"></textarea></div>
          </div>
          <PriorityAssessment v-if="quickForm.level === 'requirement'" v-model="quickDraft.priorityEvaluation" :priority="quickDefaults.priority || 'P2'" :project-priority="quickAssessmentProjectPriority" class="mt-3" @adopt="quickDefaults.priority = $event" />
          <div class="flex justify-end mt-4">
            <button @click="saveQuickImport" class="feishu-btn-primary text-sm">生成记录</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search, Plus, ChevronRight, Edit3, Trash2, Upload, Paperclip, Filter, ArrowUpDown } from 'lucide-vue-next'
import ImagePreviewModal from '../components/ImagePreviewModal.vue'
import SearchableMultiSelect from '../components/SearchableMultiSelect.vue'
import PriorityAssessment from '../components/PriorityAssessment.vue'
import { useRequirementsListPage } from "../features/project-work/useRequirementsListPage"
const { route, router, categories, allProjects, allReqs, searchText, sortKey, sortDir, filterPanelOpen, filters, activeTab, expandedL2s, deptDropdownOpen, expandedDeptIds, contactsLoading, showQuickImport, quickForm, quickDraft, quickDefaults, quickTarget, quickAssessmentProjectPriority, batchMode, selectedProjectIds, selectedRequirementIds, showBatchBackfill, batchForm, isLoading, loadError, tableShell, tableLayoutMode, tableResizeObserver, tableResizeFallback, typeOpts, changeObjectOptions, impactOptions, workloadOptions, priorityOptions, deptTree, contactUsers, devOpts, bizOwnerOpts, lifecycleStatuses, requirementStatuses, statusLabel, sortOptions, statusColors, pColor, normalizeStatus, sColor, rColor, tColor, impactColor, badgePalette, hashText, stableBadgeStyle, personBadgeStyle, versionBadgeStyle, isCrossOwnerRequirement, splitPeople, hasPerson, samePeople, tabItems, filterOptions, activeFilterCount, dashboardRange, dashboardPeriodWindow, dashboardProjectId, dashboardStatus, dashboardType, dashboardCreated, dashboardFocus, dashboardDateInPeriod, isDashboardFocusChange, dashboardRequirementRows, categoryName, clearFilters, sortValue, displayProjects, visibleDeptOptions, deptFlatOptions, currentUser, currentDeveloper, currentUserName, localToday, findDepartmentName, currentUserDepartment, isManager, canDelete, canManageCategories, canCreate, canCreateProject, isCreatedByCurrentUser, canDeleteProject, canDeleteRequirement, canEditProject, canEditRequirement, quickMissing, getL3Reqs, toggleL2, toggleProjectSelection, toggleBatchMode, toggleRequirementSelection, toggleAllProjects, bulkDeleteRequirements, bulkDeleteProjects, toggleDeptNode, selectDepartment, handleDepartmentClick, sortIcon, toggleSort, goProject, goRequirement, shortDateTime, quickModeClass, openQuickImport, loadQuickDefaults, saveQuickDefaults, parseTextField, guessOption, normalizeDateValue, parseQuickImport, readQuickImportFile, fillQuickProjectDefaults, saveQuickImport, ensureQuickCategory, ensureQuickProject, downloadCsv, exportProjects, exportRequirements, getCatColor, progressPercent, progressLabel, progressSubLabel, progressCountText, progressColor, progressBoxClass, progressTooltip, showCreateCategory, editingCategory, catForm, editCategory, closeCategoryModal, saveCategory, deleteCategory, deleteCategoryById, showCreateProject, editingProject, projForm, solutionTypeOptions, itemKindOptions, lifecycleTemplates, phaseTemplatesForForm, onProjectSolutionTypeChange, createProject, editProject, closeProjectModal, saveProject, updateProjectField, deleteProject, showCreateReq, editingReq, reqForm, reqAssessmentProjectPriority, createRequirement, editRequirement, closeReqModal, syncReqProjectDefaults, isStatusOnlyRequirementEdit, saveRequirement, deleteRequirement, openBatchBackfill, closeBatchBackfill, saveBatchBackfill, currentUserIsDeveloper, previewModal, previewImages, previewRequirementImages, imageSrc, handleImageUpload, handleImagePaste, appendImageFiles, handleWindowImagePaste, removeImage, loadData, loadContactOptions, syncTableLayout, observeTableLayout } = useRequirementsListPage()
</script>

<style scoped>
.requirements-table-shell {
  --l2-cell-x-padding: 6px;
  --l2-table-width: 100%;
  overflow-x: scroll;
  overflow-y: auto;
  scrollbar-gutter: stable;
  scrollbar-color: #94a3b8 #f1f5f9;
}

.requirements-table-shell--wide {
  --l2-table-min-width: 0px;
}

.requirements-table-shell--compact {
  --l2-table-min-width: 1320px;
}

.requirements-table-shell--scroll {
  --l2-table-min-width: 1480px;
}

.compact-l2-table :deep(th),
.compact-l2-table :deep(td) {
  padding-left: var(--l2-cell-x-padding, 6px);
  padding-right: var(--l2-cell-x-padding, 6px);
  overflow: hidden;
  vertical-align: middle;
}

.compact-l2-table {
  width: var(--l2-table-width, 100%);
  min-width: 0;
  table-layout: fixed;
}

/* Content-aware proportions: short status fields stay tight; descriptive fields get the released space. */
.compact-l2-table :deep(.l2-col-name) { width: 15%; }
.compact-l2-table :deep(.l2-col-category) { width: 9%; }
.compact-l2-table :deep(.l2-col-priority) { width: 5%; }
.compact-l2-table :deep(.l2-col-status) { width: 6%; }
.compact-l2-table :deep(.l2-col-department) { width: 8%; }
.compact-l2-table :deep(.l2-col-business) { width: 8%; }
.compact-l2-table :deep(.l2-col-dev-owner) { width: 9%; }
.compact-l2-table :deep(.l2-col-version) { width: 6%; }
.compact-l2-table :deep(.l2-col-created) { width: 8%; }
.compact-l2-table :deep(.l2-col-progress) { width: 13%; }
.compact-l2-table :deep(.l2-col-description) { width: 8%; }
.compact-l2-table :deep(.l2-col-actions) { width: 5%; }

/* Reserve a compact selection column while keeping all data columns balanced in batch mode. */
.compact-l2-table-batch { min-width: 0; }
.compact-l2-table-batch :deep(.l2-col-select) { width: 4%; }
.compact-l2-table-batch :deep(.l2-col-name) { width: 14%; }
.compact-l2-table-batch :deep(.l2-col-category) { width: 9%; }
.compact-l2-table-batch :deep(.l2-col-priority) { width: 5%; }
.compact-l2-table-batch :deep(.l2-col-status) { width: 6%; }
.compact-l2-table-batch :deep(.l2-col-department) { width: 8%; }
.compact-l2-table-batch :deep(.l2-col-business) { width: 8%; }
.compact-l2-table-batch :deep(.l2-col-dev-owner) { width: 9%; }
.compact-l2-table-batch :deep(.l2-col-version) { width: 6%; }
.compact-l2-table-batch :deep(.l2-col-created) { width: 8%; }
.compact-l2-table-batch :deep(.l2-col-progress) { width: 12%; }
.compact-l2-table-batch :deep(.l2-col-description) { width: 6%; }
.compact-l2-table-batch :deep(.l2-col-actions) { width: 5%; }
.compact-l2-table-batch :deep(th:first-child),
.compact-l2-table-batch :deep(td:first-child) { width: 4%; }

.requirements-table-shell::-webkit-scrollbar {
  height: 10px;
}

.requirements-table-shell::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 999px;
}

.requirements-table-shell::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border: 2px solid #f1f5f9;
  border-radius: 999px;
}

.requirements-table-shell::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.l2-name-content {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 0.35rem;
  line-height: 1.25;
}

.l2-name-content > span {
  overflow: hidden;
  text-overflow: ellipsis;
}

.compact-l2-table :deep(th) {
  font-size: 10px;
  white-space: nowrap;
}

.compact-l2-table :deep(td) {
  white-space: nowrap;
}

.compact-l2-table :deep(.l2-col-description > div) {
  min-width: 0;
}

.compact-l3-table :deep(th),
.compact-l3-table :deep(td) {
  padding-left: 0.35rem;
  padding-right: 0.35rem;
}

.compact-l3-table :deep(td) {
  font-size: 11px;
  vertical-align: middle;
}

.compact-l3-table :deep(td:nth-child(5)),
.compact-l3-table :deep(td:nth-child(8)),
.compact-l3-table :deep(td:nth-child(9)),
.compact-l3-table :deep(td:nth-child(10)) {
  font-size: 10px;
}
</style>
