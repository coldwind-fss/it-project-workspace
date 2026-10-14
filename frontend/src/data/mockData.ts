import type { Sprint, Changelog, Release } from '../types'

export const projects: any[] = [
  { id: 'p1', name: '订单管理系统', description: '核心订单处理与仓储物流一体化', currentVersion: 'v2.4.0', status: 'active', progress: 75, color: '#3b82f6', createdAt: '2025-01-15', owner: '张三' },
  { id: 'p2', name: '数据分析报表', description: '经营数据看板与自动报表生成', currentVersion: 'v1.8.2', status: 'active', progress: 40, color: '#8b5cf6', createdAt: '2025-03-01', owner: '王五' },
  { id: 'p3', name: '审批工作流', description: 'OA审批流程自定义引擎', currentVersion: 'v3.1.0', status: 'active', progress: 90, color: '#10b981', createdAt: '2024-08-20', owner: '张三' },
  { id: 'p4', name: '客户管理CRM', description: '客户信息管理与跟进', currentVersion: 'v1.0.0', status: 'paused', progress: 25, color: '#f59e0b', createdAt: '2025-05-10', owner: '李四' },
]

export const requirements: any[] = [
  { id: 'r1', title: '批量导入订单Excel', type: '新功能', priority: 'P1', status: '开发中', projectId: 'p1', projectName: '订单管理系统', sprintId: 's1', assignee: '张三', requester: '李总', description: '支持通过Excel批量导入订单数据，包含订单校验、重复检测、导入结果反馈。', createdAt: '2025-06-01', updatedAt: '2025-06-28' },
  { id: 'r2', title: '订单列表加载速度优化', type: '优化改进', priority: 'P2', status: '测试中', projectId: 'p1', projectName: '订单管理系统', sprintId: 's1', assignee: '张三', requester: '内部', description: '优化虚拟滚动和分页加载，目标首屏<1s。', createdAt: '2025-06-05', updatedAt: '2025-06-27' },
  { id: 'r3', title: '修复订单金额精度丢失', type: 'Bug修复', priority: 'P0', status: '已上线', projectId: 'p1', projectName: '订单管理系统', sprintId: 's2', assignee: '李四', requester: '财务部', description: '大额订单金额小数点后精度丢失紧急修复。', createdAt: '2025-06-10', updatedAt: '2025-06-15' },
  { id: 'r4', title: '报表导出PDF格式', type: '新功能', priority: 'P1', status: '开发中', projectId: 'p2', projectName: '数据分析报表', sprintId: 's3', assignee: '王五', requester: '李总', description: '支持PDF导出', createdAt: '2025-06-12', updatedAt: '2025-06-26' },
  { id: 'r5', title: '移动端审批页面适配', type: 'UI调整', priority: 'P2', status: '已排期', projectId: 'p3', projectName: '审批工作流', sprintId: 's4', assignee: '张三', requester: '市场部', description: '手机端适配', createdAt: '2025-06-14', updatedAt: '2025-06-25' },
  { id: 'r6', title: '审批流程超时自动提醒', type: '新功能', priority: 'P2', status: '待评估', projectId: 'p3', projectName: '审批工作流', sprintId: '', assignee: '待分配', requester: '人事部', description: '超24小时自动提醒', createdAt: '2025-06-18', updatedAt: '2025-06-18' },
  { id: 'r7', title: '订单状态同步延迟修复', type: 'Bug修复', priority: 'P1', status: '测试中', projectId: 'p1', projectName: '订单管理系统', sprintId: 's1', assignee: '李四', requester: '客服部', description: 'ERP同步存在1-3分钟延迟', createdAt: '2025-06-16', updatedAt: '2025-06-28' },
  { id: 'r8', title: '报表查询速度优化', type: '优化改进', priority: 'P3', status: '已上线', projectId: 'p2', projectName: '数据分析报表', sprintId: 's3', assignee: '王五', requester: '内部', description: '从8s优化到1.5s', createdAt: '2025-06-08', updatedAt: '2025-06-22' },
  { id: 'r9', title: '对接微信支付回调', type: '接口对接', priority: 'P1', status: '开发中', projectId: 'p1', projectName: '订单管理系统', sprintId: 's1', assignee: '李四', requester: '业务部', description: '接入微信支付回调', createdAt: '2025-06-20', updatedAt: '2025-06-29' },
  { id: 'r10', title: '操作日志模块重构', type: '技术重构', priority: 'P3', status: '待评估', projectId: 'p1', projectName: '订单管理系统', sprintId: '', assignee: '待分配', requester: '内部', description: '统一重构为AOP', createdAt: '2025-06-22', updatedAt: '2025-06-22' },
  { id: 'r11', title: '报表图表颜色优化', type: 'UI调整', priority: 'P3', status: '已上线', projectId: 'p2', projectName: '数据分析报表', sprintId: 's3', assignee: '王五', requester: '李总', description: '颜色优化', createdAt: '2025-06-03', updatedAt: '2025-06-18' },
  { id: 'r12', title: '审批节点加签功能', type: '新功能', priority: 'P2', status: '已排期', projectId: 'p3', projectName: '审批工作流', sprintId: 's4', assignee: '张三', requester: '人事部', description: '支持加签', createdAt: '2025-06-15', updatedAt: '2025-06-24' },
]

export const sprints: Sprint[] = [
  { id: 's1', name: '2025-Sprint-6', projectId: 'p1', startDate: '2025-06-15', endDate: '2025-07-05', status: '进行中', releaseNotes: '', totalTasks: 8, completedTasks: 3 },
  { id: 's2', name: '2025-Sprint-5', projectId: 'p1', startDate: '2025-05-25', endDate: '2025-06-14', status: '已发布', releaseNotes: '修复Bug；优化性能', totalTasks: 6, completedTasks: 6 },
  { id: 's3', name: '2025-Sprint-4', projectId: 'p2', startDate: '2025-06-01', endDate: '2025-06-30', status: '进行中', releaseNotes: '', totalTasks: 5, completedTasks: 2 },
  { id: 's4', name: '2025-Sprint-3', projectId: 'p3', startDate: '2025-06-20', endDate: '2025-07-10', status: '进行中', releaseNotes: '', totalTasks: 4, completedTasks: 1 },
]

export const changelogs: Changelog[] = [
  { id: 'cl1', requirementId: 'r1', requirementTitle: '批量导入订单Excel', changeType: '范围变更', fieldName: 'description', oldValue: '支持批量导入', newValue: '支持批量导入+重复检测', reason: '业务方要求', operator: '张三', createdAt: '2025-06-20' },
  { id: 'cl2', requirementId: 'r1', requirementTitle: '批量导入订单Excel', changeType: '优先级调整', fieldName: 'priority', oldValue: 'P2', newValue: 'P1', reason: '李总要求', operator: '张三', createdAt: '2025-06-22' },
  { id: 'cl3', requirementId: 'r4', requirementTitle: '报表导出PDF格式', changeType: '重新排期', fieldName: 'sprintId', oldValue: '未排期', newValue: 'Sprint-4', reason: '安排到当前迭代', operator: '王五', createdAt: '2025-06-23' },
  { id: 'cl4', requirementId: 'r2', requirementTitle: '订单列表加载速度优化', changeType: '状态流转', fieldName: 'status', oldValue: '开发中', newValue: '测试中', reason: '开发完成提测', operator: '张三', createdAt: '2025-06-27' },
  { id: 'cl5', requirementId: 'r7', requirementTitle: '订单状态同步延迟修复', changeType: '内容修正', fieldName: 'description', oldValue: '同步延迟', newValue: '1-3分钟延迟需排查', reason: '客服提供详情', operator: '李四', createdAt: '2025-06-25' },
  { id: 'cl6', requirementId: 'r5', requirementTitle: '移动端审批页面适配', changeType: '优先级调整', fieldName: 'priority', oldValue: 'P3', newValue: 'P2', reason: '市场部催促进度', operator: '张三', createdAt: '2025-06-26' },
  { id: 'cl7', requirementId: 'r9', requirementTitle: '对接微信支付回调', changeType: '状态流转', fieldName: 'status', oldValue: '待评估', newValue: '开发中', reason: '接口文档已下发', operator: '李四', createdAt: '2025-06-28' },
  { id: 'cl8', requirementId: 'r3', requirementTitle: '修复订单金额精度丢失', changeType: '状态流转', fieldName: 'status', oldValue: '测试中', newValue: '已上线', reason: '测试通过紧急上线', operator: '李四', createdAt: '2025-06-15' },
]

export const releases: Release[] = [
  { id: 'rel1', projectId: 'p1', projectName: '订单管理系统', version: 'v2.4.0', releaseDate: '2025-06-30', summary: ['批量导入订单Excel', '对接微信支付回调'], type: 'minor' },
  { id: 'rel2', projectId: 'p1', projectName: '订单管理系统', version: 'v2.3.0', releaseDate: '2025-05-15', summary: ['新增备注功能', '优化性能', '修复Bug'], type: 'minor' },
  { id: 'rel3', projectId: 'p1', projectName: '订单管理系统', version: 'v2.2.1', releaseDate: '2025-04-28', summary: ['紧急修复线上超时'], type: 'hotfix' },
  { id: 'rel4', projectId: 'p2', projectName: '数据分析报表', version: 'v1.8.2', releaseDate: '2025-06-22', summary: ['查询速度优化', '颜色优化'], type: 'patch' },
  { id: 'rel5', projectId: 'p3', projectName: '审批工作流', version: 'v3.1.0', releaseDate: '2025-06-10', summary: ['超时自动提醒', '移动端适配'], type: 'minor' },
]

export const categories: any[] = [
  { id: 'cat1', name: 'OA自动化', icon: 'file-text', description: '办公自动化流程与审批', createdAt: '2025-01-01' },
  { id: 'cat2', name: '数据分析', icon: 'bar-chart', description: '数据报表与可视化分析', createdAt: '2025-01-01' },
  { id: 'cat3', name: 'RPA自动化', icon: 'robot', description: '流程机器人自动化', createdAt: '2025-01-01' },
  { id: 'cat4', name: '业务自动化', icon: 'settings', description: '业务系统对接与自动化', createdAt: '2025-01-01' },
  { id: 'cat5', name: 'AI', icon: 'cpu', description: '人工智能相关项目', createdAt: '2025-01-01' },
]

export const typeColors: Record<string, string> = {
  '业务确认': '#0ea5e9', '产品设计': '#8b5cf6', '技术建设': '#64748b',
  '新增功能': '#2563eb', '功能优化': '#f59e0b', '问题修复': '#ef4444', '验证交付': '#14b8a6',
  '能力新增': '#2563eb', '能力优化': '#f59e0b',
  '新功能': '#3b82f6', '优化改进': '#f59e0b', 'Bug修复': '#ef4444',
  'UI调整': '#8b5cf6', '接口对接': '#10b981', '技术重构': '#6b7280',
  '需求变更': '#ec4899', '需求对接': '#0ea5e9', '技术方案验证': '#14b8a6',
  '功能测试': '#a855f7',
}
export const priorityColors: Record<string, string> = {
  'P0': '#ef4444', 'P1': '#f59e0b', 'P2': '#3b82f6', 'P3': '#9ca3af', 'P4': '#cbd5e1',
}
export const statusColors: Record<string, string> = {
  '待处理': '#64748b', '进行中': '#3b82f6', '待交付': '#f59e0b', '已交付': '#10b981',
  '待评估': '#9ca3af', '已排期': '#3b82f6', '已立项': '#3b82f6',
  '需求确认中': '#6366f1', '设计中': '#8b5cf6', '开发中': '#f59e0b',
  '联调中': '#06b6d4', '测试中': '#a855f7', '迭代中': '#0ea5e9',
  '待上线': '#14b8a6', '已上线': '#10b981', '维护中': '#64748b',
  '暂停中': '#f97316', '已关闭': '#6b7280', '已归档': '#94a3b8',
}
export const assigneeMap: Record<string, { initials: string; color: string }> = {
  '张三': { initials: '张', color: '#3b82f6' },
  '李四': { initials: '李', color: '#10b981' },
  '王五': { initials: '王', color: '#8b5cf6' },
  '赵六': { initials: '赵', color: '#f59e0b' },
  '待分配': { initials: '?', color: '#9ca3af' },
}

export const changeTypeConfig: Record<string, { color: string; bgColor: string; icon: string; desc: string }> = {
  '范围变更': { color: '#f59e0b', bgColor: '#fef3c7', icon: '📐', desc: '需求范围扩大或缩小' },
  '优先级调整': { color: '#ef4444', bgColor: '#fef2f2', icon: '⚡', desc: '紧急程度调整' },
  '状态流转': { color: '#3b82f6', bgColor: '#eff6ff', icon: '🔄', desc: '需求状态发生变化' },
  '重新排期': { color: '#8b5cf6', bgColor: '#f5f3ff', icon: '📅', desc: '迭代归属变更' },
  '内容修正': { color: '#10b981', bgColor: '#f0fdf4', icon: '✏️', desc: '需求描述修改' },
}
