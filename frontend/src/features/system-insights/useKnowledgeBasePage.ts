
import { computed } from 'vue'
import { Plus, FileText, BookOpen, Palette, Database } from 'lucide-vue-next'
export function useKnowledgeBasePage(){


const allDocs = [
  { id: 'd1', title: '订单系统API文档', type: 'api' as const, projectId: 'p1', projectName: '订单管理系统', url: '#', description: 'Swagger 3.0 接口规范', uploadedBy: '张三', createdAt: '2025-06-15' },
  { id: 'd2', title: '数据分析PRD', type: 'prd' as const, projectId: 'p2', projectName: '数据分析报表', url: '#', description: 'V1.8 产品需求文档', uploadedBy: '王五', createdAt: '2025-06-10' },
  { id: 'd3', title: '审批流程设计稿', type: 'design' as const, projectId: 'p3', projectName: '审批工作流', url: '#', description: 'Figma 设计源文件', uploadedBy: '赵六', createdAt: '2025-06-20' },
  { id: 'd4', title: '订单系统ER图', type: 'database' as const, projectId: 'p1', projectName: '订单管理系统', url: '#', description: '数据库表关系设计', uploadedBy: '张三', createdAt: '2025-06-05' },
  { id: 'd5', title: 'CRM客户模块PRD', type: 'prd' as const, projectId: 'p4', projectName: '客户管理CRM', url: '#', description: '客户管理模块需求', uploadedBy: '李四', createdAt: '2025-06-18' },
]

const configs = {
  api: { label: 'API文档', icon: FileText, color: '#3b82f6' },
  prd: { label: '产品需求文档', icon: BookOpen, color: '#f59e0b' },
  design: { label: '设计稿', icon: Palette, color: '#8b5cf6' },
  database: { label: '数据库设计', icon: Database, color: '#10b981' },
}

const grouped = computed(() => {
  const types = Object.keys(configs) as (keyof typeof configs)[]
  return types.map(type => ({
    ...configs[type],
    type,
    docs: allDocs.filter(d => d.type === type),
  })).filter(g => g.docs.length > 0)
})
return { allDocs, configs, grouped }
}
