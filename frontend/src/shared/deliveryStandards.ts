export type DeliveryStandardField = {
  key: string
  label: string
  placeholder: string
}

export type ValueMetricPreset = {
  key: string
  label: string
  unit: string
  direction: 'higher' | 'lower'
  sourceHint: string
  windowHint: string
}

/**
 * One acceptance-standard vocabulary is shared by the demand-pool card and
 * the formal L3 detail.  The demand-pool solution type is normalized before
 * it is used here so old records and newly-created L2 projects render the
 * same form.
 */
export const DELIVERY_STANDARD_COMMON_FIELDS = [
  { key: 'scope', label: '本次交付范围', placeholder: '只写本次 L3 实际交付的边界，不要重复业务原始需求' },
  { key: 'scenarios', label: '业务验证场景', placeholder: '业务人员按什么关键路径验证，覆盖哪些典型场景' },
  { key: 'expected', label: '功能验收通过标准', placeholder: '上线时必须看到什么功能结果，什么情况算通过' },
  { key: 'evidence', label: '验收证据', placeholder: '截图、数据结果、流程记录或附件' },
  { key: 'exclusions', label: '不在本次范围', placeholder: '明确本次不交付的内容' },
] as const

export const DELIVERY_STANDARD_TEMPLATE_LABELS: Record<string, string> = {
  workflow_automation: '业务流程自动化',
  custom_application: '新应用 / 新平台',
  new_app_platform: '新应用 / 新平台',
  software_replacement: '现有软件平替',
  existing_capability: '现有系统新增能力',
  complex_refactor: '复杂重构',
  data_integration: '数据 / 报表 / 集成',
  ai_agent: 'AI / 智能体',
  technical_foundation: '技术基础 / 稳定性 / 安全',
  custom: '通用交付标准',
}

export const DELIVERY_STANDARD_TEMPLATE_FIELDS: Record<string, DeliveryStandardField[]> = {
  workflow_automation: [
    { key: 'trigger', label: '触发条件', placeholder: '什么情况下启动流程' },
    { key: 'steps', label: '流转步骤与规则', placeholder: '经过哪些步骤、谁负责、如何判断' },
    { key: 'exceptions', label: '异常分支', placeholder: '异常时如何处理、谁收到通知' },
    { key: 'output', label: '结果与通知', placeholder: '最终产生什么结果或通知' },
  ],
  custom_application: [
    { key: 'users', label: '使用角色', placeholder: '谁使用、谁确认' },
    { key: 'coreFlow', label: '核心操作', placeholder: '最关键的操作路径' },
    { key: 'permissions', label: '权限与数据', placeholder: '权限、数据输入输出' },
    { key: 'exceptions', label: '异常处理', placeholder: '异常时如何处理' },
  ],
  new_app_platform: [
    { key: 'users', label: '使用角色', placeholder: '谁使用、谁确认' },
    { key: 'coreFlow', label: '核心操作', placeholder: '最关键的操作路径' },
    { key: 'permissions', label: '权限与数据', placeholder: '权限、数据输入输出' },
    { key: 'exceptions', label: '异常处理', placeholder: '异常时如何处理' },
  ],
  software_replacement: [
    { key: 'mustHave', label: '必备能力', placeholder: '哪些功能不能缺失' },
    { key: 'migration', label: '数据迁移', placeholder: '哪些数据需要迁移，如何核对' },
    { key: 'compatibility', label: '兼容与权限', placeholder: '兼容环境、权限和授权要求' },
    { key: 'rollback', label: '切换与回退', placeholder: '上线失败时如何切回原系统' },
  ],
  existing_capability: [
    { key: 'changedArea', label: '本次新增能力', placeholder: '新增或改变了哪项能力' },
    { key: 'protectedFunctions', label: '受保护功能', placeholder: '哪些现有功能不能受影响' },
    { key: 'regression', label: '回归范围', placeholder: '需要一起验证哪些既有流程' },
    { key: 'rollback', label: '回退方式', placeholder: '出现问题时如何恢复' },
  ],
  complex_refactor: [
    { key: 'affectedScope', label: '影响范围', placeholder: '涉及哪些模块、人员或数据' },
    { key: 'protectedFunctions', label: '受保护功能', placeholder: '哪些既有功能必须保持不变' },
    { key: 'regression', label: '回归范围', placeholder: '需要验证哪些原有流程' },
    { key: 'rollback', label: '切换与回退', placeholder: '上线失败时如何恢复' },
  ],
  data_integration: [
    { key: 'sources', label: '数据来源与口径', placeholder: '来源、字段口径和责任人' },
    { key: 'refresh', label: '刷新与准确性', placeholder: '更新频率、延迟和核对方式' },
    { key: 'failure', label: '失败重试', placeholder: '接口或同步失败如何发现和重试' },
    { key: 'permissions', label: '权限范围', placeholder: '谁能查看、操作或下载' },
  ],
  ai_agent: [
    { key: 'scenarioBoundary', label: '适用场景与边界', placeholder: '什么场景使用，什么情况必须转人工' },
    { key: 'accuracy', label: '准确性与覆盖率', placeholder: '通过什么样本或规则判定结果可接受' },
    { key: 'humanHandoff', label: '人工接管', placeholder: '低置信度、异常或敏感事项如何交给人工' },
    { key: 'costLatency', label: '成本与时延', placeholder: '响应时间、调用成本或并发要求' },
  ],
  technical_foundation: [
    { key: 'metrics', label: '指标要求', placeholder: '性能、稳定性或安全指标' },
    { key: 'monitoring', label: '监控告警', placeholder: '如何监控、告警给谁' },
    { key: 'recovery', label: '恢复与回滚', placeholder: '故障时如何恢复或回滚' },
    { key: 'evidenceDetail', label: '验证方式', placeholder: '压测、日志、扫描或演练结果' },
  ],
  custom: [
    { key: 'users', label: '使用角色', placeholder: '谁使用、谁确认' },
    { key: 'coreFlow', label: '核心操作', placeholder: '最关键的操作路径' },
    { key: 'permissions', label: '权限与数据', placeholder: '权限、数据输入输出' },
    { key: 'exceptions', label: '异常处理', placeholder: '异常时如何处理' },
  ],
}

/**
 * Suggested value metrics are an IT authoring aid, not extra questions for
 * business users.  The selected rows are persisted in the same structure
 * consumed by the day-30 callback and the post-launch management dashboard.
 */
export const VALUE_METRIC_PRESETS: Record<string, ValueMetricPreset[]> = {
  workflow_automation: [
    { key: 'handling_time', label: '单次处理耗时', unit: '分钟/次', direction: 'lower', sourceHint: '业务台账 / 抽样记录 / 系统日志', windowHint: '上线前连续一周' },
    { key: 'manual_steps', label: '人工操作步骤', unit: '步/次', direction: 'lower', sourceHint: '流程走查 / 操作记录', windowHint: '典型业务场景抽样' },
    { key: 'error_rate', label: '错误率', unit: '%', direction: 'lower', sourceHint: '业务差错台账 / 系统日志', windowHint: '上线前连续一月' },
    { key: 'throughput', label: '单位时间处理量', unit: '件/小时', direction: 'higher', sourceHint: '业务统计 / 系统日志', windowHint: '上线前连续一周' },
  ],
  custom_application: [
    { key: 'target_user_usage_rate', label: '目标用户使用率', unit: '%', direction: 'higher', sourceHint: '登录日志 / 使用人员清单', windowHint: '上线后30天' },
    { key: 'core_task_completion_rate', label: '核心任务完成率', unit: '%', direction: 'higher', sourceHint: '业务台账 / 埋点日志', windowHint: '上线前后各一月' },
    { key: 'handling_time', label: '核心任务处理耗时', unit: '分钟/次', direction: 'lower', sourceHint: '业务抽样 / 系统日志', windowHint: '上线前后各一周' },
  ],
  software_replacement: [
    { key: 'target_user_usage_rate', label: '目标用户使用率', unit: '%', direction: 'higher', sourceHint: '账号清单 / 登录日志', windowHint: '上线后30天' },
    { key: 'compatibility_pass_rate', label: '关键能力兼容通过率', unit: '%', direction: 'higher', sourceHint: '迁移验收清单', windowHint: '切换验收周期' },
    { key: 'operating_cost', label: '使用或运维成本', unit: '元/月', direction: 'lower', sourceHint: '采购 / 运维台账', windowHint: '切换前后各一月' },
  ],
  existing_capability: [
    { key: 'core_task_completion_rate', label: '核心任务完成率', unit: '%', direction: 'higher', sourceHint: '业务台账 / 系统日志', windowHint: '上线前后各一月' },
    { key: 'handling_time', label: '相关操作耗时', unit: '分钟/次', direction: 'lower', sourceHint: '业务抽样 / 系统日志', windowHint: '上线前后各一周' },
    { key: 'issue_rate', label: '相关问题发生率', unit: '%', direction: 'lower', sourceHint: '问题台账 / 系统日志', windowHint: '上线前后各一月' },
  ],
  complex_refactor: [
    { key: 'availability', label: '可用率', unit: '%', direction: 'higher', sourceHint: '监控平台', windowHint: '上线前后各一月' },
    { key: 'response_time', label: '关键操作响应时间', unit: '毫秒', direction: 'lower', sourceHint: '性能监控 / 压测报告', windowHint: '同等负载测试' },
    { key: 'incident_count', label: '相关故障次数', unit: '次/月', direction: 'lower', sourceHint: '故障台账', windowHint: '上线前后各一月' },
  ],
  data_integration: [
    { key: 'data_accuracy_rate', label: '数据准确率', unit: '%', direction: 'higher', sourceHint: '抽样核对 / 对账结果', windowHint: '上线前后各一月' },
    { key: 'refresh_latency', label: '数据更新延迟', unit: '分钟', direction: 'lower', sourceHint: '同步日志 / 报表时间', windowHint: '上线前后各一周' },
    { key: 'manual_hours', label: '人工汇总耗时', unit: '小时/月', direction: 'lower', sourceHint: '业务工时记录', windowHint: '上线前后各一月' },
  ],
  ai_agent: [
    { key: 'accuracy_rate', label: '结果准确率', unit: '%', direction: 'higher', sourceHint: '标注样本 / 评测报告', windowHint: '同一测试集或业务样本' },
    { key: 'manual_intervention_rate', label: '人工干预率', unit: '%', direction: 'lower', sourceHint: '人工接管记录 / 系统日志', windowHint: '试运行连续一月' },
    { key: 'handling_time', label: '单次处理耗时', unit: '分钟/次', direction: 'lower', sourceHint: '系统日志 / 业务抽样', windowHint: '上线前后各一周' },
    { key: 'cost_per_task', label: '单次处理成本', unit: '元/次', direction: 'lower', sourceHint: '模型调用账单 / 人工成本估算', windowHint: '试运行连续一月' },
  ],
  technical_foundation: [
    { key: 'availability', label: '系统可用率', unit: '%', direction: 'higher', sourceHint: '监控平台', windowHint: '上线前后各一月' },
    { key: 'response_time', label: '接口响应时间', unit: '毫秒', direction: 'lower', sourceHint: 'APM / 压测报告', windowHint: '同等负载测试' },
    { key: 'incident_count', label: '故障次数', unit: '次/月', direction: 'lower', sourceHint: '故障台账', windowHint: '上线前后各一月' },
    { key: 'recovery_time', label: '平均恢复时间', unit: '分钟', direction: 'lower', sourceHint: '告警与故障记录', windowHint: '上线前后各一月' },
  ],
  custom: [
    { key: 'target_user_usage_rate', label: '目标用户使用率', unit: '%', direction: 'higher', sourceHint: '使用记录 / 业务确认', windowHint: '上线后30天' },
    { key: 'handling_time', label: '核心任务处理耗时', unit: '分钟/次', direction: 'lower', sourceHint: '业务抽样 / 系统日志', windowHint: '上线前后各一周' },
  ],
}

export function normalizeDeliveryStandardType(value: unknown): string {
  const key = String(value || '').trim()
  const aliases: Record<string, string> = {
    new_app_platform: 'custom_application',
    custom: 'custom_application',
    workflow: 'workflow_automation',
    rpa: 'workflow_automation',
    data: 'data_integration',
    integration: 'data_integration',
    ai: 'ai_agent',
    agent: 'ai_agent',
  }
  return aliases[key] || key || 'custom'
}

export function deliveryStandardFields(type: unknown): DeliveryStandardField[] {
  const key = normalizeDeliveryStandardType(type)
  return DELIVERY_STANDARD_TEMPLATE_FIELDS[key] || DELIVERY_STANDARD_TEMPLATE_FIELDS.custom
}

export function deliveryStandardLabel(type: unknown): string {
  const key = normalizeDeliveryStandardType(type)
  return DELIVERY_STANDARD_TEMPLATE_LABELS[key] || DELIVERY_STANDARD_TEMPLATE_LABELS.custom
}

export function valueMetricPresets(type: unknown): ValueMetricPreset[] {
  const key = normalizeDeliveryStandardType(type)
  return VALUE_METRIC_PRESETS[key] || VALUE_METRIC_PRESETS.custom
}
