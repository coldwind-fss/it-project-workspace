export interface Category {
  id: string
  name: string
  icon: string
  description: string
  owner: string[]
  sortOrder: number
  color: string
  status: string
  createdAt: string
}

export interface Project {
  id: string
  name: string
  description: string
  status: LifecycleStatus | 'active' | 'paused' | 'archived'
  solutionType?: ProjectSolutionType | string
  solutionTypeLabel?: string
  lifecycleTemplate?: string
  complexityLevel?: 'low' | 'medium' | 'high' | string
  phaseTemplates?: RequirementPhaseTemplate[]
  priority: Priority
  department: string
  businessOwner: string
  devOwner: string
  currentVersion: string
  startDate: string
  targetEndDate: string
  categoryId: string
  categoryName?: string
  categoryColor?: string
  images: string[]
  createdAt: string
  updatedAt: string
  progress?: {
    total: number
    done: number
    progress: number
    overallProgress?: number
    currentTotal?: number
    currentDone?: number
    currentProgress?: number
    mode?: 'empty' | 'initial' | 'iteration' | 'released'
    label?: string
    subLabel?: string
    statusCounts?: Record<string, number>
    activeStatusCounts?: Record<string, number>
  }
}

export interface Requirement {
  id: string
  title: string
  type: RequirementType
  itemKind?: L3ItemKind | string
  itemKindLabel?: string
  parentRequirementId?: string
  versionTarget?: string
  phaseCount?: number
  priority: Priority
  status: RequirementStatus
  projectId: string
  projectName: string
  pname?: string
  sprintId: string
  assignee: string
  requester: string
  department: string
  projectDepartment?: string
  description: string
  acceptanceCriteria: string
  expectedDeliveryTime: string
  completedAt: string
  storyPoints: number
  labels: string
  changeObject?: RequirementChangeObject
  impactLevel?: RequirementImpactLevel
  workloadLevel?: RequirementWorkload
  // Requirement lists return only imageCount; the full Base64 attachments are
  // loaded from the detail endpoint when a user opens or edits the record.
  images?: any[]
  imageCount?: number
  priorityEvaluation?: Record<string, any>
  createdAt: string
  updatedAt: string
}

export type ProjectSolutionType = 'workflow_automation' | 'custom_application' | 'software_replacement' | 'data_integration' | 'ai_agent' | 'technical_foundation' | 'unknown'
export type L3ItemKind = 'initial_build' | 'feature' | 'bugfix' | 'enhancement' | 'integration' | 'design' | 'operation'
export interface RequirementPhaseTemplate { id?: string; solutionType?: string; phaseKey: string; phaseLabel: string; description?: string; required?: boolean; sortOrder?: number; enabled?: boolean }
export interface RequirementPhase extends RequirementPhaseTemplate { requirementId: string; status: 'todo' | 'in_progress' | 'blocked' | 'done' | 'skipped' | string; statusLabel?: string; ownerUserId?: string; ownerName?: string; plannedAt?: string; startedAt?: string; completedAt?: string; evidence?: Record<string, any>; note?: string }

export type RequirementType = '业务确认' | '产品设计' | '技术建设' | '新增功能' | '功能优化' | '问题修复' | '验证交付' | '能力新增' | '能力优化' | '新功能' | '优化改进' | 'UI调整' | '接口对接' | '技术重构' | 'Bug修复' | '需求变更' | '需求对接' | '技术方案验证' | '功能测试'
export type RequirementChangeObject = '模块' | '功能' | '字段' | '流程' | '页面交互' | '接口数据' | '系统基础' | '其他' | 'UI交互' | '技术基础'
export type RequirementImpactLevel = '核心' | '重要' | '常规'
export type RequirementWorkload = '大' | '中' | '小'
export type Priority = 'P0' | 'P1' | 'P2' | 'P3' | 'P4'
export type LifecycleStatus = '待评估' | '已立项' | '需求确认中' | '设计中' | '开发中' | '联调中' | '测试中' | '迭代中' | '待上线' | '已上线' | '维护中' | '暂停中' | '已关闭' | '已归档'
export type RequirementLifecycleStatus = '待处理' | '进行中' | '待交付' | '已交付' | '已关闭'
export type RequirementStatus = RequirementLifecycleStatus | LifecycleStatus | '已排期'

export interface Sprint {
  id: string
  name: string
  projectId: string
  startDate: string
  endDate: string
  status: '规划中' | '进行中' | '已发布' | '已取消'
  releaseNotes: string
  totalTasks: number
  completedTasks: number
}

export interface Changelog {
  id: string
  requirementId: string
  requirementTitle: string
  changeType: ChangeType
  fieldName: string
  oldValue: string
  newValue: string
  reason: string
  operator: string
  createdAt: string
}

export type ChangeType = '范围变更' | '优先级调整' | '状态流转' | '重新排期' | '内容修正'

export interface Release {
  id: string
  projectId: string
  projectName: string
  version: string
  releaseDate: string
  summary: string[]
  type: 'major' | 'minor' | 'patch' | 'hotfix'
}

export interface DashboardStats {
  activeProjects: number
  monthlyNewRequirements: number
  pendingBugs: number
  monthlyReleases: number
}

export interface CategorySummary {
  id: string
  name: string
  color: string
  owner: string
  reqCount: number
  doneCount: number
  projectCount: number
}

export interface ImageItem {
  id: string
  name: string
  data: string  // base64
  type: string  // mime type
}

export interface KnowledgeDoc {
  id: string
  title: string
  type: 'api' | 'prd' | 'design' | 'database' | string
  projectId: string
  projectName: string
  requirementIds?: string[]
  url: string
  description: string
  uploadedBy: string
  createdAt: string
}
